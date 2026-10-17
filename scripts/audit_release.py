"""Comprobaciones de archivos antes de compartir. No muestra valores detectados."""
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
patterns = [
    re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"sk-(?:proj-)?[a-zA-Z0-9_-]{30,}"),
]
forbidden_parts = {".secrets", ".venv", ".aws", "__pycache__", ".git"}
forbidden_files = {"lab.json", "credentials.env", "runtime.env", "estado.md", "AGENTS.md"}
tracked = subprocess.run(["git", "ls-files", "--cached", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.decode().split("\0")
for name in filter(None, tracked):
    path = Path(name)
    if any(part in forbidden_parts for part in path.parts) or path.name in forbidden_files:
        raise RuntimeError("Archivo privado preparado para Git: " + name)
    if any(pattern.search((ROOT / path).read_bytes()) for pattern in patterns):
        raise RuntimeError("Posible secreto en archivo preparado: " + name)
package = ROOT / "output/Alexa-Bedrock-Taller.zip"
with zipfile.ZipFile(package) as archive:
    for name in archive.namelist():
        path = Path(name)
        if any(part in forbidden_parts for part in path.parts) or path.name in forbidden_files or "output" in path.parts:
            raise RuntimeError("Archivo privado dentro del ZIP: " + name)
        if any(pattern.search(archive.read(name)) for pattern in patterns):
            raise RuntimeError("Posible secreto en ZIP: " + name)
print("Revision correcta: Git y ZIP sin configuracion privada ni patrones de claves detectados.")
print("Esta comprobacion de patrones no reemplaza la revision humana de capturas y documentos.")
