"""Entrada Lambda real. IAM del despliegue limita la invocacion a una sola skill."""
import hashlib
import json
import logging
import os
import time
import urllib.request

import boto3
from botocore.config import Config
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_intent_name, is_request_type
from tutor import clean_text, converse_arguments, extract_answer, ssml

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
CLIENT_CONFIG = Config(connect_timeout=0.5, read_timeout=3.5, retries={"total_max_attempts": 1})
_runtime = None
_table = None


def runtime():
    global _runtime
    if _runtime is None:
        _runtime = boto3.client("bedrock-runtime", region_name=os.environ["BEDROCK_REGION"], config=CLIENT_CONFIG)
    return _runtime


def table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb", config=Config(connect_timeout=0.4, read_timeout=0.6, retries={"total_max_attempts": 1})).Table(os.environ["HISTORY_TABLE"])
    return _table


def user_key(handler_input):
    system = handler_input.request_envelope.context.system
    user_id = system.user.user_id
    if not user_id:
        raise ValueError("Usuario ausente")
    return hashlib.sha256((os.environ["SKILL_ID"] + ":" + user_id).encode()).hexdigest()


def load_history(key):
    item = table().get_item(Key={"pk": "history#" + key}, ConsistentRead=True).get("Item", {})
    if int(item.get("expires", 0)) <= int(time.time()):
        return []
    history = item.get("history", [])
    return history if isinstance(history, list) else []


def save_history(key, history):
    table().put_item(Item={"pk": "history#" + key, "history": history[-3:], "expires": int(time.time()) + 1800})


def rate_limit(key):
    # Maximo 15 inferencias por usuario y hora; no sustituye un presupuesto.
    now = int(time.time())
    table().update_item(
        Key={"pk": "rate#" + key + "#" + str(now // 3600)},
        UpdateExpression="SET #n = if_not_exists(#n, :zero) + :one, expires = :ttl",
        ConditionExpression="attribute_not_exists(#n) OR #n < :limit",
        ExpressionAttributeNames={"#n": "count"},
        ExpressionAttributeValues={":zero": 0, ":one": 1, ":limit": 15, ":ttl": now + 7200},
    )


def progressive(handler_input):
    system = handler_input.request_envelope.context.system
    # No reenviar el token de Alexa a hosts indicados arbitrariamente en un evento.
    if system.api_endpoint not in {
        "https://api.amazonalexa.com", "https://api.eu.amazonalexa.com", "https://api.fe.amazonalexa.com"
    } or not system.api_access_token:
        return
    body = json.dumps({
        "header": {"requestId": handler_input.request_envelope.request.request_id},
        "directive": {"type": "VoicePlayer.Speak", "speech": "<speak>Estoy consultando tu pregunta.</speak>"},
    }).encode()
    request = urllib.request.Request(system.api_endpoint + "/v1/directives", data=body, headers={
        "Authorization": "Bearer " + system.api_access_token, "Content-Type": "application/json"
    }, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=0.5):
            pass
    except Exception:
        # No registrar excepcion/URL/token; la respuesta principal sigue siendo necesaria.
        LOG.info("progressive_unavailable")


def say(handler_input, text, end=False, reprompt=None):
    builder = handler_input.response_builder.speak(ssml(text)).set_should_end_session(end)
    if reprompt:
        builder.ask(ssml(reprompt))
    return builder.response


class LaunchHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return say(handler_input, "Bienvenido a tutor academico. Di: explica que es Lambda. No compartas datos personales.", reprompt="Di explica, seguido de tu pregunta.")


class QueryHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GenerativeQueryIntent")(handler_input)

    def handle(self, handler_input):
        start = time.monotonic()
        slots = handler_input.request_envelope.request.intent.slots or {}
        query = clean_text(getattr(slots.get("query"), "value", None), 600)
        if not query:
            return say(handler_input, "Di explica, seguido de tu pregunta.", reprompt="Por ejemplo: explica que es una VPN.")
        try:
            key = user_key(handler_input)
            rate_limit(key)
            history = load_history(key)
            # Informar no extiende el limite de aproximadamente ocho segundos.
            progressive(handler_input)
            generated = runtime().converse(**converse_arguments(
                query, history, os.environ["MODEL_ID"], os.environ["GUARDRAIL_ID"], os.environ["GUARDRAIL_VERSION"]
            ))
            answer = extract_answer(generated)
            # No persistir entradas rechazadas: pueden contener datos personales.
            if generated.get("stopReason") != "guardrail_intervened":
                try:
                    save_history(key, history + [{"question": query, "answer": answer}])
                except Exception:
                    LOG.warning("history_save_failed")
                    answer += " No pude guardar este turno para la siguiente pregunta."
            LOG.info(json.dumps({"event": "answer", "milliseconds": round((time.monotonic()-start)*1000)}))
            return say(handler_input, answer, reprompt="Puedes decir explica, seguido de otra pregunta, u olvida la conversacion.")
        except Exception as error:
            # No registrar evento, historial, pregunta ni mensajes de excepcion del proveedor.
            LOG.warning(json.dumps({"event": "query_failed", "type": type(error).__name__}))
            return say(handler_input, "No pude completar la consulta. Puede haber un limite de uso o un problema de acceso. Intenta mas tarde.", end=True)


class ForgetHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ForgetIntent")(handler_input)

    def handle(self, handler_input):
        try:
            table().delete_item(Key={"pk": "history#" + user_key(handler_input)})
            return say(handler_input, "Elimine tu historial de conversacion.", reprompt="Di explica, seguido de una nueva pregunta.")
        except Exception:
            return say(handler_input, "No pude eliminar el historial ahora. Intenta mas tarde.", end=True)


class HelpHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        return say(handler_input, "Di explica que es Bedrock, o pregunta como funciona una red. Di olvida la conversacion para borrar el historial.", reprompt="¿Que tema quieres aprender?")


class StopHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return any(is_intent_name(name)(handler_input) for name in ["AMAZON.StopIntent", "AMAZON.CancelIntent"])

    def handle(self, handler_input):
        return say(handler_input, "Hasta luego. Puedes volver a abrir tutor academico.", end=True)


class EndHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response


class FallbackHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return True

    def handle(self, handler_input):
        return say(handler_input, "No entendi. Di explica, seguido de tu pregunta.", reprompt="Por ejemplo: explica que es Lambda.")


sb = SkillBuilder()
for request_handler in [LaunchHandler(), QueryHandler(), ForgetHandler(), HelpHandler(), StopHandler(), EndHandler(), FallbackHandler()]:
    sb.add_request_handler(request_handler)
_sdk_handler = sb.lambda_handler()


def handler(event, context):
    expected = os.environ.get("SKILL_ID", "")
    actual = event.get("context", {}).get("System", {}).get("application", {}).get("applicationId")
    if not expected.startswith("amzn1.ask.skill.") or actual != expected:
        raise PermissionError("Skill no autorizada")
    return _sdk_handler(event, context)
