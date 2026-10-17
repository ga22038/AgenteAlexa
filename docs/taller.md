# Taller nuevo: integra IA generativa en Alexa con AWS Lambda y Bedrock

## 1. Resultado que debes poder explicar

Al finalizar, tendras una custom skill que recibe preguntas en español, consulta un modelo en Amazon Bedrock y responde por voz. Lambda coordina la solicitud; DynamoDB mantiene un historial limitado; Guardrails filtra entradas y respuestas. Cada integrante usa sus propias cuentas y recursos.

Este laboratorio es independiente del proyecto multicloud. No requiere sus dominios, servidores, VPN, bases de datos ni credenciales.

Ruta de una solicitud:

```text
Persona -> Alexa / custom skill -> Lambda -> Bedrock + Guardrails
                                     |               |
                                  DynamoDB       texto breve
                                     |               |
                                  CloudWatch <- Lambda -> voz en Alexa
```

El simulador incluido en la computadora representa ese flujo con respuestas fijas. No es una IA local, no invoca AWS y no acredita una prueba de Alexa.

## 2. Antes de empezar

Necesitas Python 3.12 o posterior, PowerShell, acceso a Internet para instalar dependencias, una cuenta AWS propia con un plan FREE activo y creditos vigentes, y una cuenta Amazon Developer. AWS CLI v2 se necesita en las practicas cloud. Un Echo se necesita para la prueba fisica indicada en el proyecto solicitado; primero puedes usar el simulador oficial.

No necesitas comprar un dominio. La skill invoca el ARN de Lambda. No se utiliza Google Cloud. Docker es opcional para comprobar el paquete de Lambda en Linux; no forma parte del despliegue requerido.

Antes de usar recursos, lee [duracion y apagado](uso-limites.md) y [costos y alternativas](costos-y-alternativas.md). Los precios de IA no incluyen automaticamente filtros ni infraestructura.

El registro Amazon Developer solicita datos reales de contacto y un acuerdo. Cada integrante completa ese registro personalmente en Amazon. No fotografies contraseñas, codigos, direccion, telefono ni documentos de identidad. El nombre publico del desarrollador debe seguir las reglas de Amazon; no es obligatorio crear una empresa para la cuenta individual de estudiante.

## 3. Practica 1: comprender la arquitectura

1. Dibuja el recorrido de una pregunta.
2. Explica la diferencia entre la cuenta de Amazon Developer y AWS.
3. Explica por que Lambda necesita permisos y por que no necesita claves guardadas en el codigo.
4. Identifica los datos que se almacenan: historial de tres pares pregunta/respuesta y clave de usuario derivada por hash. El historial vence logicamente a los 30 minutos. DynamoDB elimina fisicamente los elementos vencidos de forma asincrona.

Entrega un diagrama y una explicacion propia, no solo una captura de esta guia.

## 4. Practica 2: preparar el proyecto local

Descomprime el ZIP compartido. Elige una carpeta nueva; no sobrescribas otro proyecto.

```powershell
cd "C:\Dev\16 Alexa Bedrock"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe lab.py test
.\.venv\Scripts\python.exe lab.py serve
```

Abre http://127.0.0.1:8092. Si el puerto esta ocupado:

```powershell
.\.venv\Scripts\python.exe lab.py serve --port 8093
```

El servidor escucha solo en 127.0.0.1. No permite descargar lab.json, .secrets ni las evidencias locales. Ctrl+C detiene el servidor. Usa el ejecutable de `.venv` en los comandos siguientes para no depender de la politica de activacion de scripts de PowerShell.

Resultado esperado: pruebas locales correctas. Conserva la salida real. Los mensajes de proveedores y la tabla estan simulados en esas pruebas.

## 5. Practica 3: conversar sin consumir AWS

1. En el taller, escribe `que es Lambda`.
2. Escribe `dame un ejemplo`.
3. Pulsa `Olvidar conversacion`.
4. Repite la pregunta de seguimiento.

Explica que cambio y por que. El filtro local es ilustrativo; no equivale a Amazon Bedrock Guardrails. No uses datos personales. Una respuesta fija del simulador tampoco prueba que AWS o Alexa esten configurados.

## 6. Practica 4: configurar tu cuenta propia

Instala AWS CLI v2 desde su sitio oficial. Usa el mecanismo oficial de tu cuenta. La ruta AWS login abre un navegador:

```powershell
aws login --profile alexa-estudiante --region us-east-1
```

Si tu institucion usa IAM Identity Center, configura y autentica un perfil SSO con `aws configure sso` y `aws sso login --profile alexa-estudiante`. No confundas SSO con la sesion de Amazon Developer.

Usa tu carnet y tu ID AWS de 12 digitos:

```powershell
.\.venv\Scripts\python.exe lab.py init --student TU-CARNET --account TU-ID-AWS --profile alexa-estudiante
.\.venv\Scripts\python.exe lab.py doctor
```

Sustituye los marcadores antes de ejecutar. lab.json queda excluido de Git. Contiene identificadores, nunca claves. Si ya existe, editalo en tu computadora; init no lo sobrescribe.

doctor comprueba identidad real, coincidencia de cuenta, FREE activo, credito positivo, vencimiento futuro y disponibilidad regional del modelo. Conserva el resultado como evidencia de consulta, no de despliegue.

La CLI elimina variables AWS heredadas y selecciona el perfil explicitamente. Un perfil con el mismo nombre en dos computadoras no comparte credenciales: cada uno debe autenticarlo en su cuenta. No distribuyas tu directorio .aws, sesiones, claves ni el lab.json del docente.

Si aparecen AccessDenied, ExpiredToken o restricciones del plan, detente y revisa el acceso. No uses la cuenta de otro integrante para aparentar que tu laboratorio funciona. Si se solicita actualizar a pago o contratar una oferta, no aceptes para seguir esta ruta.

## 7. Practica 5: crear tu skill

1. Abre https://developer.amazon.com/alexa/console/ask con la cuenta Amazon vinculada a tu Echo.
2. Completa el registro si es tu primera vez. Revisa los datos y el acuerdo antes de enviarlo.
3. Crea una skill nueva llamada `Tutor academico`.
4. Selecciona Español (Mexico), tipo Custom y backend propio / Provision your own. No uses Alexa-hosted para esta ruta, porque desplegaremos Lambda en tu AWS.
5. Elige una plantilla vacia si se ofrece.
6. En Build, abre JSON Editor. Pega el contenido de `skill/interaction-model.es-MX.json`.
7. Guarda y construye el modelo. Resuelve cualquier error antes de continuar.
8. Copia el Skill ID real y reemplaza el campo skill_id de lab.json.

El nombre de invocacion es `tutor academico`. Las preguntas empiezan por `explica`, `pregunta`, `dime` o `consulta`. AMAZON.SearchQuery requiere una frase portadora; usar solo `{query}` como expresion de ejemplo no es esta implementacion.

No se necesita pedir la direccion del usuario, acceso a compras, ubicacion ni credenciales. Si habilitas otras capacidades, debes revisar sus permisos por separado.

## 8. Practica 6: Bedrock y despliegue real

La primera prueba envia una pregunta ficticia pequeña. Consume uso de Bedrock:

```powershell
.\.venv\Scripts\python.exe lab.py probe
```

El resultado real se guarda en output/evidence/model-probe.json. Incluye tokens y metricas del servicio. Comprueba tambien que la respuesta sea correcta: una llamada HTTP exitosa no garantiza calidad academica.

Construye el paquete y despliega:

```powershell
.\.venv\Scripts\python.exe lab.py build
.\.venv\Scripts\python.exe lab.py deploy
```

build descarga dependencias para Linux/Python 3.12 y genera output/lambda.zip. deploy valida la plantilla, comprueba la cuenta y crea el stack `alexa-TU-CARNET` en minusculas. No modifica stacks sin las etiquetas del laboratorio. Espera a que termine; no lances dos despliegues simultaneos.

Recursos creados:

| Recurso | Para que sirve | Control de uso |
| --- | --- | --- |
| Lambda | Recibe la solicitud de Alexa | 256 MB, timeout 7 s; reserva de 2 solo si la cuota lo permite |
| Rol IAM | Permite acciones del backend | Modelo, tabla, Guardrail y registros concretos |
| DynamoDB | Historial y contador de preguntas | 1 unidad de lectura/escritura aprovisionada, TTL |
| Guardrail versionado | Contenido y datos sensibles | Filtros configurados, aplicado en cada consulta real |
| CloudWatch Logs | Tiempos y tipo de fallos | Retencion de 7 dias, sin registrar preguntas o tokens |
| Permiso de invocacion | Conecta Alexa con Lambda | Principal Alexa y Skill ID especifico |

No se crea EC2, VPN, NAT Gateway, dominio ni base RDS. El stack puede consumir creditos. La concurrencia y el limite de 15 preguntas por usuario/hora reducen uso, pero no limitan el gasto total de todas las personas en dinero. En cuentas nuevas con cuota total de 10, se omite la reserva porque AWS exige capacidad sin reservar. La funcion comparte entonces la cuota actual de la cuenta; no se solicita una ampliacion.

Si CloudFormation falla, consulta Events y conserva el motivo. Una cuenta nueva puede tener cuotas distintas; no eleves cuotas ni cambies el plan sin revisar el impacto. No borres recursos de otro stack para resolverlo.

Copia FunctionArn de la salida. En Amazon Developer, abre Endpoint, selecciona AWS Lambda ARN y pega ese ARN. Guarda y activa Test > Development. No expongas una Function URL publica; no se necesita para esta skill.

## 9. Practica 7: pruebas reproducibles

### A. Lambda con eventos sinteticos

```powershell
.\.venv\Scripts\python.exe lab.py test-cloud
```

Prueba apertura, pregunta, seguimiento, borrado y cierre. Guarda output/evidence/lambda-tests.json. El usuario de prueba es ficticio y el historial se borra al finalizar el recorrido. El tiempo medido incluye AWS CLI y red; no es el tiempo extremo a extremo de Alexa.

### B. Simulador oficial de Alexa

1. Activa Development en Test y elige Español (Mexico).
2. Escribe o di `abre tutor academico`.
3. `explica que es AWS Lambda`.
4. `explica un ejemplo del tema anterior`.
5. `olvida la conversacion`.
6. `ayuda` y `para`.
7. Haz una consulta con un correo ficticio, por ejemplo `persona@example.com`, para comprobar la politica de datos sensibles. Registra si el filtro interviene realmente; no lo supongas.

Prueba tambien una solicitud que la politica de contenido deba rechazar, sin introducir informacion de personas reales. Guardrails reduce riesgos pero no garantiza que toda respuesta sea correcta o apropiada.

### C. Echo fisico y latencia

El Echo debe usar la misma cuenta Amazon que habilita la skill de desarrollo y un idioma compatible. Ejecuta los mismos casos por voz. Comprueba reconocimiento, audio, sesion, seguimiento y cierre.

Registra al menos diez consultas, duracion observada, exitos y errores. No acredites todos los casos con una sola muestra rapida. El limite de Alexa es aproximadamente ocho segundos; la respuesta progresiva informa que se esta procesando, pero no amplia ese plazo. La configuracion de timeout tampoco garantiza que nunca haya latencia por arranque en frio o fallos de red.

### D. Seguridad y costo

Comprueba que el permiso Lambda no permita cualquier skill. Revisa la politica IAM, TTL y los registros. Confirma que no incluyen eventos completos, tokens o preguntas privadas. Compara saldo/uso antes y despues; la informacion de facturacion puede tardar en actualizarse. No atribuyas todo el consumo de una cuenta con otros proyectos a este taller.

## 10. Practica 8: entrega y publicacion

Organiza las evidencias por practica con fecha, comando, resultado, interpretacion y limitaciones. Las capturas deben mostrar estados reales. No reconstruyas una consola para hacer parecer que ejecutaste una prueba.

```powershell
.\.venv\Scripts\python.exe lab.py status
.\.venv\Scripts\python.exe lab.py package
```

El ZIP comparte codigo y guia; excluye .venv, .secrets, configuracion personal y evidencias output del propietario. El avance marcado en el navegador solo indica lectura/autorreporte; no aprueba una rubrica.

Para distribuir publicamente una skill, prepara nombre, descripcion, iconos, instrucciones de prueba y politica de privacidad que describa el tratamiento real del historial. Revisa la clasificacion de audiencia y los requisitos de Amazon para IA generativa. Si el uso se dirige a niños, revisa sus reglas especificas antes de publicarlo; esta implementacion de laboratorio no se presenta como una skill infantil certificada.

Completa las pruebas de certificacion y envia la skill para revision. Amazon puede solicitar cambios. No prometas una fecha de aprobacion. La publicacion queda pendiente hasta que Amazon la acepte y exista evidencia verificable de la tienda.

## 11. Matriz de requisitos del documento solicitado

Esta tabla es una lista de comprobacion, no una afirmacion de cumplimiento.

| Requisito del PDF | Implementacion preparada | Evidencia que debes producir |
| --- | --- | --- |
| ASK Custom Skill | Modelo es-MX y captura SearchQuery | Modelo construido e invocacion real |
| Lambda + Python/Boto3 | ASK SDK y Converse API | Despliegue y respuesta Lambda real |
| LLM en Bedrock | Nova Micro configurable dentro de esta ruta | Inferencia, tokens y calidad; justificar cambio frente a Claude |
| Respuestas para voz | Prompt breve y escape SSML | Audio claro en simulador/Echo |
| Contexto entre turnos | Tres pares de historial | Seguimiento coherente observado |
| Persistencia | DynamoDB y TTL 30 minutos | Nueva sesion recuerda; borrado comprobado |
| Respuesta progresiva | Llamada con endpoint permitido | Audio intermedio real cuando llega antes de la respuesta final |
| Guardrails | Filtros y version en cada Converse | Casos permitidos/bloqueados reales |
| IAM de minimo privilegio | Politicas de recursos concretos | Revisar rol y permiso de Skill ID |
| Latencia de Alexa | Limites de tokens, timeouts, sin reintentos automaticos | Muestras por voz y fallos documentados |
| Pruebas unitarias | unittest y proveedores simulados | Salida local real |
| Pruebas extremo a extremo | Guion Alexa y Echo | Grabacion/capturas propias |
| Certificacion y publicacion | Procedimiento y materiales por completar | Aprobacion y pagina de tienda reales |

El cronograma del PDF propone cuatro semanas. No garantiza certificacion ni convierte DynamoDB o Guardrails en implementados por copiar su ejemplo: el ejemplo no incluye esas partes.

## 12. Limpieza al terminar

La limpieza elimina permanentemente el historial y los recursos de este stack. Guarda antes las evidencias que necesitas. Verifica primero `aws sts get-caller-identity --profile alexa-estudiante` y confirma tu cuenta. Consulta el stack antes de borrarlo:

```powershell
aws cloudformation describe-stacks --stack-name alexa-TU-CARNET --region us-east-1 --profile alexa-estudiante
```

Reemplaza TU-CARNET por el carnet en minusculas que configuraste. Solo cuando confirmes que es tu stack de laboratorio y quieras eliminarlo:

```powershell
aws cloudformation delete-stack --stack-name alexa-TU-CARNET --region us-east-1 --profile alexa-estudiante
aws cloudformation wait stack-delete-complete --stack-name alexa-TU-CARNET --region us-east-1 --profile alexa-estudiante
```

Desactiva las pruebas de la skill en Amazon Developer si ya no usaras su endpoint. Consulta los recursos y facturacion despues de limpiar. Borrar el stack no elimina una skill publicada ni revierte consumo ya realizado. No borres stacks o recursos del taller multicloud.

## 13. Preguntas para defender el proyecto

1. ¿Por que se usa una custom skill y no se modifica Alexa globalmente?
2. ¿Que diferencia hay entre la intencion y la pregunta capturada?
3. ¿Como se autoriza a Lambda a invocar Bedrock sin guardar claves en el codigo?
4. ¿Que pasa si el modelo tarda demasiado o devuelve XML?
5. ¿Que memoria se conserva y como la borra el usuario?
6. ¿Por que una progresiva no resuelve un timeout de diez segundos?
7. ¿Que prueba acredita Guardrails y cual solo simula un filtro?
8. ¿Que recursos consumen tus creditos y como los eliminas?
9. ¿Por que la salida correcta de una API no garantiza una respuesta correcta?
10. ¿Que falta para afirmar que la skill esta certificada y publicada?

## Referencias oficiales

- ASK Python SDK: https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit-sdk-for-python/overview.html
- Lambda y Skill ID: https://developer.amazon.com/en-US/docs/alexa/custom-skills/host-a-custom-skill-as-an-aws-lambda-function.html
- Captura SearchQuery: https://developer.amazon.com/en-US/docs/alexa/custom-skills/slot-type-reference.html
- Simulador oficial: https://developer.amazon.com/en-US/docs/alexa/devconsole/alexa-simulator.html
- Respuestas progresivas: https://developer.amazon.com/en-US/docs/alexa/custom-skills/send-the-user-a-progressive-response.html
- Bedrock Converse: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
- Nova Micro: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-micro.html
- Acceso a modelos: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html
- Precios: https://aws.amazon.com/bedrock/pricing/
- Planes AWS: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html
