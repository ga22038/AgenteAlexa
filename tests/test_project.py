import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import MagicMock, patch
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import lab
import tutor
import lambda_function as function
from workshop_server import Handler, ThreadingHTTPServer

SKILL = "amzn1.ask.skill.11111111-2222-3333-4444-555555555555"


class VoiceCoreTests(unittest.TestCase):
    def test_untrusted_model_xml_is_escaped(self):
        value = tutor.ssml('Hola <audio src="https://malicious.invalid/a"/> & gracias')
        self.assertNotIn("<audio", value)
        self.assertIn("&lt;audio", value)
        self.assertIn("&amp;", value)

    def test_history_is_bounded_and_cannot_inject_system_roles(self):
        history = [{"question": "q"*1000, "answer": "a"*1500, "role": "system"} for _ in range(20)]
        args = tutor.converse_arguments("pregunta", history, "model", "guardrail", "1")
        self.assertEqual(len(args["messages"]), 7)
        self.assertEqual({m["role"] for m in args["messages"]}, {"user", "assistant"})
        self.assertEqual(len(args["messages"][0]["content"][0]["text"]), 350)
        self.assertEqual(args["guardrailConfig"]["guardrailVersion"], "1")

    def test_guardrail_block_never_reads_generated_text(self):
        answer = tutor.extract_answer({"stopReason": "guardrail_intervened", "output": {"message": {"content": [{"text": "UNSAFE"}]}}})
        self.assertNotIn("UNSAFE", answer)

    def test_empty_query_does_not_produce_inference_request(self):
        with self.assertRaises(ValueError):
            tutor.converse_arguments("  ", [], "model")


class LambdaTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"SKILL_ID": SKILL, "BEDROCK_REGION": "us-east-1", "MODEL_ID": "amazon.nova-micro-v1:0", "HISTORY_TABLE": "test", "GUARDRAIL_ID": "testguard", "GUARDRAIL_VERSION": "1"})
        self.env.start()
        self.table = MagicMock()
        self.table.get_item.return_value = {}
        self.runtime = MagicMock()
        self.runtime.converse.return_value = {"output": {"message": {"content": [{"text": "Lambda ejecuta codigo."}]}}}
        self.patches = [patch.object(function, "_table", self.table), patch.object(function, "_runtime", self.runtime)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.env.stop()

    def event(self, name=None, query=None):
        return lab.event({"skill_id": SKILL}, "IntentRequest" if name else "LaunchRequest", name, query)

    def test_rejects_other_skill_before_calling_aws(self):
        event = self.event()
        event["context"]["System"]["application"]["applicationId"] = "other"
        with self.assertRaises(PermissionError):
            function.handler(event, None)
        self.table.assert_not_called()
        self.runtime.converse.assert_not_called()

    def test_launch_and_stop_do_not_invoke_bedrock(self):
        response = function.handler(self.event(), None)
        self.assertIn("Bienvenido", response["response"]["outputSpeech"]["ssml"])
        stop = function.handler(self.event("AMAZON.StopIntent"), None)
        self.assertTrue(stop["response"]["shouldEndSession"])
        self.runtime.converse.assert_not_called()

    def test_query_includes_guardrail_and_saves_history(self):
        result = function.handler(self.event("GenerativeQueryIntent", "que es Lambda"), None)
        self.assertIn("Lambda ejecuta", result["response"]["outputSpeech"]["ssml"])
        kwargs = self.runtime.converse.call_args.kwargs
        self.assertEqual(kwargs["guardrailConfig"]["guardrailIdentifier"], "testguard")
        self.table.put_item.assert_called_once()
        key = self.table.put_item.call_args.kwargs["Item"]["pk"]
        self.assertNotIn("synthetic-lab-user", key)

    def test_missing_query_never_calls_model(self):
        result = function.handler(self.event("GenerativeQueryIntent"), None)
        self.assertIn("Di explica", result["response"]["outputSpeech"]["ssml"])
        self.runtime.converse.assert_not_called()

    def test_failed_rate_limit_prevents_inference(self):
        self.table.update_item.side_effect = RuntimeError("private provider error")
        result = function.handler(self.event("GenerativeQueryIntent", "hola"), None)
        self.assertIn("No pude", result["response"]["outputSpeech"]["ssml"])
        self.assertNotIn("private provider error", json.dumps(result))
        self.runtime.converse.assert_not_called()

    def test_forget_really_deletes_history(self):
        result = function.handler(self.event("ForgetIntent"), None)
        self.assertIn("Elimine", result["response"]["outputSpeech"]["ssml"])
        self.table.delete_item.assert_called_once()

    def test_guardrail_rejected_question_is_never_persisted(self):
        self.runtime.converse.return_value = {"stopReason": "guardrail_intervened"}
        result = function.handler(self.event("GenerativeQueryIntent", "persona@example.com"), None)
        self.assertIn("No puedo responder", result["response"]["outputSpeech"]["ssml"])
        self.table.put_item.assert_not_called()

    def test_stale_history_is_not_sent_to_model(self):
        self.table.get_item.return_value = {"Item": {"expires": 1, "history": [{"question": "old", "answer": "old"}]}}
        function.handler(self.event("GenerativeQueryIntent", "nueva"), None)
        self.assertEqual(len(self.runtime.converse.call_args.kwargs["messages"]), 1)


class IsolationTests(unittest.TestCase):
    def test_environment_drops_inherited_credentials_and_profile(self):
        with patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "fake-test", "AWS_SECRET_ACCESS_KEY": "fake-test", "AWS_PROFILE": "owner", "AWS_BEARER_TOKEN_BEDROCK": "fake-test", "AWS_WEB_IDENTITY_TOKEN_FILE": "owner.json"}):
            env = lab.aws_env({"profile": "student"})
        for name in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_PROFILE", "AWS_BEARER_TOKEN_BEDROCK", "AWS_WEB_IDENTITY_TOKEN_FILE"]:
            self.assertNotIn(name, env)

    def test_account_mismatch_stops_before_model_or_plan(self):
        with patch.object(lab, "aws", return_value={"Account": "111111111111"}) as call:
            with self.assertRaises(PermissionError):
                lab.preflight({"account_id": "222222222222"})
        self.assertEqual(call.call_count, 1)

    def test_paid_plan_cannot_be_silently_used(self):
        with patch.object(lab, "aws", side_effect=[{"Account": "111111111111"}, {"accountPlanType": "PAID", "accountPlanStatus": "ACTIVE"}]) as call:
            with self.assertRaises(PermissionError):
                lab.preflight({"account_id": "111111111111"})
        self.assertEqual(call.call_count, 2)

    def test_no_wildcard_bedrock_or_database_permission(self):
        template = json.loads((ROOT / "infra/template.json").read_text())
        policy = template["Resources"]["ExecutionRole"]["Properties"]["Policies"][0]["PolicyDocument"]
        for statement in policy["Statement"]:
            self.assertNotEqual(statement["Resource"], "*")
        permission = template["Resources"]["AlexaPermission"]["Properties"]
        self.assertEqual(permission["EventSourceToken"], {"Ref": "SkillId"})


class LocalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_private_files_are_never_served(self):
        for path in ["/lab.json", "/.secrets/credentials.env", "/../lab.py", "/output/evidence/preflight.json"]:
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(self.url + path)
            self.assertEqual(caught.exception.code, 404)

    def test_foreign_origin_cannot_use_simulator(self):
        request = urllib.request.Request(self.url + "/api/simulate", data=b'{"question":"hola"}', headers={"Content-Type": "application/json", "Origin": "https://foreign.invalid"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 403)

    def test_simulation_is_explicit_and_uses_no_cloud(self):
        request = urllib.request.Request(self.url + "/api/simulate", data=b'{"question":"que es Lambda","history":[]}', headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request) as response:
            value = json.load(response)
        self.assertEqual(value["mode"], "simulation")
        self.assertEqual(value["aws_calls"], 0)
        self.assertIn("Lambda", value["answer"])


if __name__ == "__main__":
    unittest.main()
