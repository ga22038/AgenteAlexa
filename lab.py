"""CLI del taller: perfiles explicitos; nunca importa credenciales del propietario."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
CONFIG = ROOT / "lab.json"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def config():
    if not CONFIG.exists():
        raise ValueError("Primero ejecuta python lab.py init con tu cuenta y perfil propios.")
    value = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    if not re.fullmatch(r"[a-z0-9-]{3,24}", value.get("student", "")):
        raise ValueError("Carnet invalido: usa letras, numeros o guion, de 3 a 24 caracteres.")
    if not re.fullmatch(r"[0-9]{12}", value.get("account_id", "")):
        raise ValueError("Falta tu ID de cuenta AWS de 12 digitos.")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", value.get("profile", "")):
        raise ValueError("Perfil AWS invalido.")
    if value.get("region") != "us-east-1":
        raise ValueError("Esta primera practica esta validada para us-east-1.")
    if value.get("model_id") != "amazon.nova-micro-v1:0":
        raise ValueError("Esta version usa Nova Micro regional. Revisa IAM y disponibilidad antes de cambiar modelo.")
    if value.get("allow_paid_plan") is not False:
        raise ValueError("La practica conserva el plan FREE; allow_paid_plan debe ser false.")
    return value


def aws_env(c):
    env = {key: value for key, value in os.environ.items() if not key.startswith("AWS_")}
    env.update({"AWS_EC2_METADATA_DISABLED": "true", "AWS_CLI_AUTO_PROMPT": "off", "AWS_CLI_OUTPUT_ENCODING": "utf-8"})
    if c.get("login_cache"):
        env["AWS_LOGIN_CACHE_DIRECTORY"] = str(Path(c["login_cache"]).resolve())
    return env


def aws(c, *arguments, timeout=90, raw=False):
    executable = shutil.which("aws")
    if not executable:
        candidate = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Amazon/AWSCLIV2/aws.exe"
        executable = str(candidate) if candidate.is_file() else None
    if not executable:
        raise RuntimeError("Instala AWS CLI v2. No se encontro aws.")
    process = subprocess.run([executable, *arguments, "--profile", c["profile"], "--region", c["region"], "--no-cli-pager", "--output", "json"], cwd=ROOT, env=aws_env(c), capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if process.returncode:
        # AWS CLI no recibe secretos por argumentos. No devolver stdout de payloads privados.
        message = process.stderr.strip()[:1000]
        raise RuntimeError(message or "AWS CLI fallo. Consulta tu sesion y permisos.")
    return process.stdout if raw else json.loads(process.stdout or "{}")


def preflight(c):
    identity = aws(c, "sts", "get-caller-identity")
    if identity["Account"] != c["account_id"]:
        raise PermissionError("Cuenta diferente a lab.json. Se bloqueo la operacion antes de crear recursos.")
    plan = aws(c, "freetier", "get-account-plan-state")
    if plan.get("accountPlanType") != "FREE" or plan.get("accountPlanStatus") != "ACTIVE":
        raise PermissionError("Se requiere plan FREE activo. No se cambiara ni actualizara la facturacion.")
    remaining = float(plan.get("accountPlanRemainingCredits", {}).get("amount", 0))
    if remaining <= 0:
        raise PermissionError("No hay credito confirmado. No se continuara.")
    expires = plan.get("accountPlanExpirationDate")
    if not expires or dt.datetime.fromisoformat(expires.replace("Z", "+00:00")) <= dt.datetime.now(dt.timezone.utc):
        raise PermissionError("No se confirmo un vencimiento futuro del plan.")
    availability = aws(c, "bedrock", "get-foundation-model-availability", "--model-id", c["model_id"])
    if any(availability.get(key) != "AVAILABLE" for key in ["entitlementAvailability", "regionAvailability"]) or availability.get("authorizationStatus") != "AUTHORIZED" or availability.get("agreementAvailability", {}).get("status") != "AVAILABLE":
        raise PermissionError("Modelo no disponible con las condiciones actuales. No se aceptaran suscripciones ni cambios de plan.")
    evidence = {"checked_at": utc(), "account": identity["Account"], "plan": plan, "model": availability, "kind": "real-read-only"}
    write_json(ROOT / "output/evidence/preflight.json", evidence)
    return evidence


def event(c, request_type="LaunchRequest", intent=None, query=None):
    value = {
        "version": "1.0", "session": {"new": True, "sessionId": "SessionId.lab", "application": {"applicationId": c["skill_id"]}, "user": {"userId": "amzn1.ask.account.synthetic-lab-user"}, "attributes": {}},
        "context": {"System": {"application": {"applicationId": c["skill_id"]}, "user": {"userId": "amzn1.ask.account.synthetic-lab-user"}, "device": {"deviceId": "synthetic", "supportedInterfaces": {}}}},
        "request": {"type": request_type, "requestId": "amzn1.echo-api.request.lab-" + str(time.time_ns()), "timestamp": utc(), "locale": "es-MX"},
    }
    if intent:
        value["request"]["intent"] = {"name": intent, "confirmationStatus": "NONE", "slots": {}}
        if query:
            value["request"]["intent"]["slots"] = {"query": {"name": "query", "value": query, "confirmationStatus": "NONE"}}
    return value


def build():
    bundle = ROOT / "output/bundle"
    # Nunca reutilizar secretos ni archivos de configuracion dentro del ZIP Lambda.
    if bundle.exists():
        if bundle.is_symlink() or not bundle.resolve().is_relative_to(ROOT.resolve()):
            raise PermissionError("La carpeta de compilacion sale del proyecto. No se eliminara.")
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True)
    requirements = ROOT / "requirements.lock.txt"
    if not requirements.exists():
        requirements = ROOT / "requirements.txt"
    subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--target", str(bundle), "--platform", "manylinux2014_x86_64", "--implementation", "cp", "--python-version", "3.12", "--only-binary=:all:", "-r", str(requirements)], check=True)
    for name in ["tutor.py", "lambda_function.py"]:
        shutil.copy2(ROOT / "src" / name, bundle / name)
    target = ROOT / "output/lambda.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and not path.name.endswith(".pyc"):
                archive.write(path, path.relative_to(bundle).as_posix())
    manifest = {"built_at": utc(), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size}
    write_json(ROOT / "output/build.json", manifest)
    print(json.dumps(manifest, indent=2))


def deploy(c):
    preflight(c)
    if not re.fullmatch(r"amzn1\.ask\.skill\.[a-f0-9-]{36}", c.get("skill_id", "")):
        raise ValueError("Primero crea la skill en Amazon Developer y configura su Skill ID real en lab.json.")
    if not (ROOT / "output/lambda.zip").exists():
        build()
    stack = "alexa-" + c["student"]
    limits = aws(c, "lambda", "get-account-settings")["AccountLimit"]
    reserve = "true" if int(limits.get("UnreservedConcurrentExecutions", 0)) >= 102 else "false"
    print("Concurrencia reservada: " + ("2" if reserve == "true" else "omitida por cuota de cuenta nueva; se conserva la cuota actual"))
    template = ROOT / "infra/template.json"
    aws(c, "cloudformation", "validate-template", "--template-body", "file://" + str(template))
    try:
        existing = aws(c, "cloudformation", "describe-stacks", "--stack-name", stack)["Stacks"][0]
    except RuntimeError as error:
        if "does not exist" not in str(error):
            raise
        existing = None
    tags = ["Key=Project,Value=alexa-bedrock-lab", "Key=Student,Value=" + c["student"]]
    if existing:
        actual_tags = {t["Key"]: t["Value"] for t in existing.get("Tags", [])}
        if actual_tags.get("Project") != "alexa-bedrock-lab" or actual_tags.get("Student") != c["student"]:
            raise PermissionError("Stack ajeno al laboratorio. No se modificara.")
    command = "update-stack" if existing else "create-stack"
    try:
        aws(c, "cloudformation", command, "--stack-name", stack, "--template-body", "file://" + str(template), "--parameters", "ParameterKey=Student,ParameterValue=" + c["student"], "ParameterKey=SkillId,ParameterValue=" + c["skill_id"], "ParameterKey=ModelId,ParameterValue=" + c["model_id"], "ParameterKey=ReserveConcurrency,ParameterValue=" + reserve, "--capabilities", "CAPABILITY_IAM", "--tags", *tags)
        print("Infraestructura solicitada. Esperando CloudFormation...")
        # Espera acotada con salida de progreso, sin ocultar largos bloques al alumno.
        for attempt in range(90):
            state = aws(c, "cloudformation", "describe-stacks", "--stack-name", stack)["Stacks"][0]["StackStatus"]
            if state in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
                break
            if "FAILED" in state or "ROLLBACK" in state:
                raise RuntimeError("CloudFormation " + state + ". Revisa Events antes de continuar; no repitas ni borres recursos ajenos.")
            print("  " + state, flush=True)
            time.sleep(5)
        else:
            raise TimeoutError("El stack sigue trabajando; consulta Events, no ejecutes otro despliegue simultaneo.")
    except RuntimeError as error:
        if "No updates are to be performed" not in str(error):
            raise
    aws(c, "lambda", "update-function-code", "--function-name", stack, "--zip-file", "fileb://" + str(ROOT / "output/lambda.zip"))
    aws(c, "lambda", "wait", "function-updated-v2", "--function-name", stack, timeout=180)
    outputs = aws(c, "cloudformation", "describe-stacks", "--stack-name", stack)["Stacks"][0]["Outputs"]
    write_json(ROOT / "output/evidence/deployment.json", {"deployed_at": utc(), "account": c["account_id"], "stack": stack, "outputs": outputs, "kind": "real-deployment"})
    for output in outputs:
        print(output["OutputKey"] + ": " + output["OutputValue"])
    print("Copia FunctionArn en Endpoint de tu skill; guarda y habilita Test > Development.")


def cloud_test(c):
    preflight(c)
    cases = [
        ("launch", event(c), "Bienvenido"),
        ("query", event(c, "IntentRequest", "GenerativeQueryIntent", "que es AWS Lambda"), None),
        ("followup", event(c, "IntentRequest", "GenerativeQueryIntent", "dame un ejemplo del tema anterior"), None),
        ("forget", event(c, "IntentRequest", "ForgetIntent"), "Elimine"),
        ("blocked-query", event(c, "IntentRequest", "GenerativeQueryIntent", "Mi correo es persona@example.com, repite ese correo"), "No puedo responder"),
        ("stop", event(c, "IntentRequest", "AMAZON.StopIntent"), "Hasta luego"),
    ]
    results = []
    for name, payload, expected in cases:
        request_file = ROOT / "output/private-test-event.json"
        response_file = ROOT / "output/private-test-response.json"
        write_json(request_file, payload)
        started = time.monotonic()
        metadata = aws(c, "lambda", "invoke", "--function-name", "alexa-" + c["student"], "--payload", "fileb://" + str(request_file), str(response_file))
        response = json.loads(response_file.read_text(encoding="utf-8"))
        speech = response.get("response", {}).get("outputSpeech", {}).get("ssml", "")
        success = not metadata.get("FunctionError") and bool(speech)
        if expected:
            success = success and expected in speech
        if name in ["query", "followup"]:
            success = success and "No pude" not in speech
        elapsed = round((time.monotonic()-started)*1000)
        results.append({"case": name, "passed": success, "roundtrip_ms": elapsed, "speech": speech})
        print(name + ": " + ("PASS" if success else "FAIL") + " (" + str(elapsed) + " ms CLI, no es latencia Alexa)")
    # Una skill diferente debe ser rechazada por el propio handler incluso en invoke directo.
    bad = event(c)
    bad["context"]["System"]["application"]["applicationId"] = "amzn1.ask.skill.00000000-0000-0000-0000-000000000000"
    write_json(request_file, bad)
    denied = aws(c, "lambda", "invoke", "--function-name", "alexa-" + c["student"], "--payload", "fileb://" + str(request_file), str(response_file))
    body = json.loads(response_file.read_text(encoding="utf-8"))
    results.append({"case": "foreign-skill", "passed": bool(denied.get("FunctionError")) and body.get("errorType") == "PermissionError"})
    print("foreign-skill: " + ("PASS" if results[-1]["passed"] else "FAIL"))
    stack = aws(c, "cloudformation", "describe-stacks", "--stack-name", "alexa-" + c["student"])["Stacks"][0]
    outputs = {item["OutputKey"]: item["OutputValue"] for item in stack["Outputs"]}
    guardrail_file = ROOT / "output/guardrail-synthetic-input.json"
    # Direccion reservada para ejemplos; ninguna informacion de una persona real.
    write_json(guardrail_file, [{"text": {"text": "Mi correo es persona@example.com. Puedes repetir ese correo?"}}])
    guardrail = aws(c, "bedrock-runtime", "apply-guardrail", "--guardrail-identifier", outputs["GuardrailId"], "--guardrail-version", outputs["GuardrailVersion"], "--source", "INPUT", "--content", "file://" + str(guardrail_file))
    results.append({"case": "guardrail-fictitious-email", "passed": guardrail.get("action") == "GUARDRAIL_INTERVENED", "action": guardrail.get("action"), "usage": guardrail.get("usage")})
    print("guardrail-fictitious-email: " + ("PASS" if results[-1]["passed"] else "FAIL"))
    key = hashlib.sha256((c["skill_id"] + ":amzn1.ask.account.synthetic-lab-user").encode()).hexdigest()
    key_file = ROOT / "output/synthetic-key.json"
    write_json(key_file, {"pk": {"S": "history#" + key}})
    stored = aws(c, "dynamodb", "get-item", "--table-name", outputs["HistoryTable"], "--key", "file://" + str(key_file), "--consistent-read")
    results.append({"case": "history-deleted", "passed": not stored.get("Item")})
    print("history-deleted: " + ("PASS" if results[-1]["passed"] else "FAIL"))
    # La identidad sintetica no pertenece a una persona real; no guardar eventos con tokens.
    for path in [request_file, response_file]:
        path.unlink(missing_ok=True)
    guardrail_file.unlink(missing_ok=True)
    key_file.unlink(missing_ok=True)
    write_json(ROOT / "output/evidence/lambda-tests.json", {"tested_at": utc(), "kind": "real-lambda-synthetic-events", "results": results, "alexa_device_test": "pending", "certification": "pending"})
    if not all(row["passed"] for row in results):
        raise RuntimeError("Hay pruebas cloud fallidas. Consulta los registros sin publicar eventos completos.")


def main():
    parser = argparse.ArgumentParser(description="Taller Alexa Bedrock: local primero, cuenta propia despues")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--student", required=True)
    init.add_argument("--account", required=True)
    init.add_argument("--profile", default="alexa-estudiante")
    init.add_argument("--skill-id", default="amzn1.ask.skill.REEMPLAZAR")
    init.add_argument("--login-cache")
    for name in ["doctor", "probe", "build", "deploy", "test-cloud", "test", "package", "status"]:
        sub.add_parser(name)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8092)
    args = parser.parse_args()
    if args.command == "init":
        if CONFIG.exists():
            raise ValueError("lab.json ya existe. Editalo localmente; no se sobrescribira.")
        c = {"student": args.student.lower(), "account_id": args.account, "profile": args.profile, "region": "us-east-1", "model_id": "amazon.nova-micro-v1:0", "skill_id": args.skill_id, "allow_paid_plan": False}
        if args.login_cache:
            c["login_cache"] = args.login_cache
        write_json(CONFIG, c)
        try:
            config()
        except Exception:
            CONFIG.unlink()
            raise
        print("lab.json creado. Solo contiene identificadores, nunca claves. Cada alumno configura su propia cuenta.")
    elif args.command == "doctor":
        data = preflight(config())
        print(json.dumps(data, indent=2))
    elif args.command == "probe":
        c = config()
        preflight(c)
        request_file = ROOT / "output/probe-request.json"
        write_json(request_file, [{"role": "user", "content": [{"text": "Explica en español y en una oracion que es el servicio AWS Lambda de Amazon Web Services. No me refiero a expresiones lambda del lenguaje Python."}]}])
        start = time.monotonic()
        result = aws(c, "bedrock-runtime", "converse", "--model-id", c["model_id"], "--messages", "file://" + str(request_file), "--inference-config", "maxTokens=60,temperature=0.1")
        from tutor import extract_answer
        evidence = {"tested_at": utc(), "kind": "real-bedrock-inference", "model": c["model_id"], "roundtrip_ms": round((time.monotonic()-start)*1000), "usage": result.get("usage"), "metrics": result.get("metrics"), "answer": extract_answer(result)}
        write_json(ROOT / "output/evidence/model-probe.json", evidence)
        print(json.dumps(evidence, ensure_ascii=False, indent=2))
    elif args.command == "build":
        build()
    elif args.command == "deploy":
        deploy(config())
    elif args.command == "test-cloud":
        cloud_test(config())
    elif args.command == "test":
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, capture_output=True, text=True)
        print(result.stdout + result.stderr)
        write_json(ROOT / "output/evidence/local-tests.json", {"tested_at": utc(), "kind": "local-mocked-tests", "passed": result.returncode == 0, "output": result.stdout + result.stderr})
        raise SystemExit(result.returncode)
    elif args.command == "serve":
        from workshop_server import serve
        serve(args.port)
    elif args.command == "package":
        target = ROOT / "output/Alexa-Bedrock-Taller.zip"
        target.parent.mkdir(exist_ok=True)
        excluded = {".git", ".venv", ".secrets", "output", "__pycache__", ".pytest_cache"}
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(ROOT.rglob("*")):
                relative = path.relative_to(ROOT)
                if any(part in excluded for part in relative.parts) or not path.is_file() or relative.as_posix() == "docs/estado.md" or path.name in {"lab.json", "AGENTS.md"} or path.suffix.lower() in {".pyc", ".pem", ".key", ".p12", ".pfx"} or (path.name.startswith(".env") and path.name != ".env.example"):
                    continue
                archive.write(path, "Alexa-Bedrock-Taller/" + relative.as_posix())
        print(str(target))
    elif args.command == "status":
        for path in sorted((ROOT / "output/evidence").glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            print(path.name + ": " + data.get("kind", "sin tipo"))
        print("La certificacion y las pruebas Echo requieren evidencias separadas. El ZIP no incluye tus credenciales ni tu lab.json.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, PermissionError, RuntimeError, TimeoutError, subprocess.SubprocessError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)
