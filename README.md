# Taller independiente: Alexa + Lambda + Amazon Bedrock

Construye un tutor academico en español. Este proyecto no pertenece al taller multicloud y no utiliza Google Cloud ni un dominio propio.

Repositorio del proyecto: https://github.com/ga22038/AgenteAlexa

Taller publicado: https://ga22038.github.io/AgenteAlexa/

Puedes leer las practicas, usar el simulador de respuestas fijas y descargar el proyecto desde ese enlace. El sitio del taller no invoca AWS. La publicacion de este material es independiente de la certificacion y publicacion de la skill en la tienda de Alexa.

Puedes obtener el codigo desde el ZIP del taller o clonarlo en una carpeta nueva:

```powershell
git clone https://github.com/ga22038/AgenteAlexa.git "C:\Dev\AgenteAlexa"
cd "C:\Dev\AgenteAlexa"
```

## Comenzar en PowerShell

Descomprime el paquete en una carpeta propia y entra en ella. Esta ruta es solo un ejemplo:

```powershell
cd "C:\Dev\16 Alexa Bedrock"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe lab.py test
.\.venv\Scripts\python.exe lab.py serve
```

Abre http://127.0.0.1:8092. El taller incluye ocho practicas y un simulador local de respuestas fijas sin consumo AWS. No necesita claves para ese recorrido.

Sigue [la guia completa](docs/taller.md). Para AWS, cada persona crea su propio `lab.json`, utiliza su perfil y confirma su ID de cuenta. No copies sesiones, claves ni archivos `.secrets/` de otra persona.

## Comandos

| Comando | Accion |
| --- | --- |
| `python lab.py test` | Pruebas locales con proveedores simulados |
| `python lab.py serve` | Taller local y simulador sin llamadas cloud |
| `python lab.py init --student TU-CARNET --account TU-ID-AWS --profile alexa-estudiante` | Configuracion personal, sin claves |
| `python lab.py doctor` | Consultas reales de identidad, plan y disponibilidad |
| `python lab.py probe` | Una inferencia pequeña real; consume uso del modelo |
| `python lab.py build` | Paquete Linux/Python 3.12 de Lambda |
| `python lab.py deploy` | Stack personal de Lambda, IAM, DynamoDB, Guardrails y registros |
| `python lab.py test-cloud` | Eventos sinteticos contra la Lambda real; consume AWS |
| `python lab.py status` | Clasificacion de evidencias registradas |
| `python lab.py package` | ZIP compartible sin configuracion privada ni resultados del propietario |

La CLI bloquea una cuenta distinta a la configurada y cualquier plan que no sea FREE activo. Nunca actualiza facturacion ni acepta suscripciones Marketplace. Los servicios y la inferencia pueden consumir creditos; no se promete costo cero. Un compañero con otro tipo de cuenta necesita revisar su presupuesto y adaptar ese control explicitamente fuera de esta ruta gratuita.

## Estructura

- `src/tutor.py`: mensajes, limites de historial, escape SSML y ejemplos locales.
- `src/lambda_function.py`: ASK SDK, Bedrock Converse, DynamoDB, progresivas y borrado.
- `infra/template.json`: recursos y permisos concretos, sin servidores permanentes.
- `skill/interaction-model.es-MX.json`: modelo de voz y frases para capturar preguntas.
- `web/`: taller independiente.
- `docs/taller.md`: practicas, evidencias, costos, limpieza y matriz del PDF.
- `docs/capturas/`: capturas reales sin datos privados.
- `output/`: resultados locales privados y paquetes generados; excluido de Git.

## Alcance academico

El PDF presenta Claude 3 Haiku como ejemplo. Esta primera ruta usa Amazon Nova Micro regional cuando esta disponible en el plan actual. La sustitucion debe explicarse y confirmarse con el docente si exige un modelo concreto. Las cifras de latencia del PDF son orientativas, no garantias.

La certificacion y publicacion en la tienda requieren completar los datos, las politicas y la revision de Amazon. No se consideran realizadas por tener pruebas unitarias correctas ni por responder desde Bedrock. Consulta [las evidencias del ejemplo](web/evidencias.json).

Consulta [duracion, limites y desactivacion](docs/uso-limites.md) antes de dejar la skill disponible.

Consulta [costos y alternativas de API](docs/costos-y-alternativas.md) para calcular escenarios con Nova u OpenAI. OpenAI se explica como alternativa; no se ha integrado ni contratado.
