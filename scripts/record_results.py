"""Publica solo un resumen acotado del ejemplo, sin eventos o credenciales."""
from pathlib import Path
import argparse
import base64
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import lab

parser = argparse.ArgumentParser(description="Resumen de pruebas y afirmaciones manuales diferenciadas")
parser.add_argument("--alexa-observed", action="store_true", help="El operador declara que observo los casos del simulador; no se verifica automaticamente")
parser.add_argument("--echo-user-confirmed", action="store_true", help="Registrar confirmacion manual del usuario, sin afirmar observacion directa")
parser.add_argument("--handler-ms", type=int, nargs="*", default=[], help="Muestras copiadas de CloudWatch, no latencia de voz")
args = parser.parse_args()

c = lab.config()
local = json.loads((ROOT / "output/evidence/local-tests.json").read_text(encoding="utf-8"))
tests = json.loads((ROOT / "output/evidence/lambda-tests.json").read_text(encoding="utf-8"))
build = json.loads((ROOT / "output/build.json").read_text(encoding="utf-8"))
metadata = lab.aws(c, "lambda", "get-function-configuration", "--function-name", "alexa-" + c["student"], "--query", "{State:State,Update:LastUpdateStatus,Hash:CodeSha256,Runtime:Runtime,Timeout:Timeout,Memory:MemorySize}")
if base64.b64decode(metadata["Hash"]).hex() != build["sha256"]:
    raise RuntimeError("El codigo desplegado no coincide con el ZIP actual")
if metadata["State"] != "Active" or metadata["Update"] != "Successful":
    raise RuntimeError("Lambda no confirmo una actualizacion correcta")
summary = {
    "example_only": True,
    "recorded_at_utc": lab.utc(),
    "local_tests": int(re.search(r"Ran (\d+) tests", local["output"]).group(1)),
    "local_tests_passed": local["passed"],
    "stack": "Creado y codigo Lambda desplegado; hash del ZIP coincide con AWS",
    "deployed_code_sha256": build["sha256"],
    "lambda_runtime": metadata["Runtime"],
    "lambda_tests": str(len(tests["results"])) + " comprobaciones cloud " + ("correctas" if all(row["passed"] for row in tests["results"]) else "con fallos"),
    "cloud_cases": [{"case": row["case"], "passed": row["passed"]} for row in tests["results"]],
    "observed_handler_ms": args.handler_ms,
    "alexa_simulator": "Apertura, pregunta, seguimiento, borrado y bloqueo de correo ficticio observados por el operador" if args.alexa_observed else "Pendiente de evidencia manual",
    "echo": "El usuario confirmo apertura, pregunta y seguimiento; sin grabacion ni medicion de latencia fisica" if args.echo_user_confirmed else "Pendiente de evidencia manual",
    "echo_evidence_source": "Declaracion manual, no verificada automaticamente" if args.echo_user_confirmed else "Sin confirmacion",
    "certification": "Pendiente de materiales, envio y revision de Amazon",
    "published_skill": False,
    "note": "Las muestras internas, si se proporcionaron, no representan p95 ni latencia completa de Alexa. Las pruebas de simulador y Echo son declaraciones manuales. Los resultados pertenecen a este ejemplo, no al laboratorio de cada estudiante.",
}
lab.write_json(ROOT / "web/evidencias.json", summary)
lab.write_json(ROOT / "output/evidence/verified-summary.json", summary)
print(json.dumps(summary, ensure_ascii=False, indent=2))
