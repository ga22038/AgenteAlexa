"""Empaqueta un taller estatico sin credenciales ni endpoints cloud del propietario."""
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / "output/site"
if target.exists():
    if target.is_symlink() or not target.resolve().is_relative_to(ROOT.resolve()):
        raise PermissionError("El destino sale del proyecto")
    shutil.rmtree(target)
shutil.copytree(ROOT / "web", target)
shutil.copytree(ROOT / "docs/capturas", target / "capturas")
shutil.copy2(ROOT / "docs/taller.md", target / "guia.md")
for name in ["taller.md", "uso-limites.md", "costos-y-alternativas.md", "certificacion.md", "capturas.md"]:
    shutil.copy2(ROOT / "docs" / name, target / name)
subprocess.run([sys.executable, str(ROOT / "lab.py"), "package"], check=True)
shutil.copy2(ROOT / "output/Alexa-Bedrock-Taller.zip", target / "Alexa-Bedrock-Taller.zip")
(target / ".nojekyll").write_text("", encoding="utf-8")
print(str(target))
