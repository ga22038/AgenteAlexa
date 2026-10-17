# Duracion, respuestas, limites y apagado

## ¿Durante cuanto tiempo puedo usarla?

La skill de desarrollo puede funcionar mientras este habilitada, AWS permita acceder a los servicios y sus recursos permanezcan activos. El plan gratuito y los creditos de cada cuenta tienen sus propios limites. Revisa siempre tu cuenta con `python lab.py doctor`; no copies la fecha ni el saldo del autor como si fueran tuyos.

El saldo y la fecha de vencimiento son datos de cada cuenta y pueden ser distintos entre compañeros. El plan puede terminar antes si se agotan los creditos. La facturacion puede actualizarse con retraso. Esta guia no publica los saldos privados del autor ni promete costo cero.

No se activo un plan de pago, no se contrataron modelos de Marketplace y no se configuro una suscripcion mensual del laboratorio. Lambda, registros, DynamoDB, inferencia y filtros tienen sus propias condiciones de uso y pueden consumir creditos. Tener la skill publicada o varios usuarios puede aumentar el uso.

## ¿Que puede responder?

- Explicaciones generales de temas academicos y tecnologicos.
- Definiciones, comparaciones sencillas y ejemplos.
- Preguntas de seguimiento basadas en el historial reciente.
- Ayuda para usar la skill y confirmacion del borrado de historial.

Prueba: `Alexa, abre tutor academico`; `explica que es AWS Lambda`; `explica un ejemplo del tema anterior`; `olvida la conversacion`; `para`.

El modelo genera texto: puede equivocarse o producir respuestas incompletas. No busca informacion en Internet, no lee tus repositorios ni tus documentos y no conoce automaticamente lo que ocurre en tus otras aplicaciones. Esta version no ejecuta compras, no controla dispositivos ni administra tu AWS por voz. Un tema mencionado por el usuario no se convierte en permiso para ejecutar acciones externas.

## Limites implementados

| Limite | Valor y alcance |
| --- | --- |
| Consultas | 15 por usuario en cada ventana horaria UTC; incluye consultas rechazadas |
| Pregunta | Se conserva como maximo una entrada de 600 caracteres para inferencia |
| Respuesta del modelo | Maximo 140 tokens; puede terminar antes o quedar cortada |
| Historial | Hasta 3 pares recientes pregunta/respuesta |
| Contexto enviado | Preguntas anteriores limitadas a 350 caracteres y respuestas a 450 |
| Vencimiento del historial | 30 minutos despues del ultimo turno guardado; TTL elimina fisicamente de forma asincrona |
| Consultas bloqueadas | No se guardan en el historial |
| Timeout Lambda | 7 segundos; una progresiva no amplia los aproximadamente 8 segundos de Alexa |
| Concurrencia | Se conserva la cuota AWS; reserva de 2 solo si queda capacidad suficiente. El autor tiene cuota total 10 compartida por la cuenta |
| Registros | Retencion 7 dias; el codigo registra duracion o tipo de fallo, no preguntas completas ni tokens |
| Filtros | Odio, violencia, contenido sexual y ciertos datos sensibles como correo, telefono o tarjeta |

Estos controles no constituyen un limite monetario global. Los filtros no garantizan ausencia de errores ni cobertura de todo contenido no deseado. No se midio un p95 de latencia ni se promete que todas las solicitudes respondan a tiempo. La cuota de otro alumno puede ser distinta.

## Desactivar temporalmente la skill

En Amazon Developer:

1. Abre tu skill.
2. Entra en Test.
3. Cambia Development por Off.

Deshabilita las pruebas en el simulador y en los dispositivos vinculados. No borra el codigo ni los recursos AWS. DynamoDB y los registros permanecen; Off por si solo no garantiza consumo total cero. Una skill publicada requiere revisar tambien su distribucion; este proyecto aun no esta publicado en la tienda.

Para dejar de hablar sin apagar el laboratorio, di `para` o `cancela`. Eso cierra esa conversacion, no desactiva toda la skill ni elimina recursos. Para borrar la memoria, di `olvida la conversacion`.

## Eliminar los recursos AWS al terminar

**Esto elimina permanentemente el historial, los registros y los recursos del stack. Guarda primero las evidencias y confirma la cuenta y el nombre exacto del stack.**

En CloudFormation, region N. Virginia / us-east-1, selecciona solo tu stack `alexa-TU-CARNET` y elige Delete. El autor usa `alexa-ga22038`; los alumnos deben usar el suyo, nunca operar sobre la cuenta o el stack del autor.

El procedimiento de CLI con comprobaciones esta en [la guia](taller.md#12-limpieza-al-terminar). Espera DELETE_COMPLETE o confirma que el stack desaparecio, y revisa cualquier fallo de borrado. Eliminarlo no revierte consumo anterior. El repositorio, el ZIP y tu carpeta de codigo se conservan. Eliminar el stack no elimina automaticamente la definicion de la skill en Amazon Developer.

## Referencias

- Plan AWS: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html
- Precios Bedrock: https://aws.amazon.com/bedrock/pricing/
- Pruebas Alexa: https://developer.amazon.com/en-US/docs/alexa/devconsole/alexa-simulator.html
- Progresivas y timeout: https://developer.amazon.com/en-US/docs/alexa/custom-skills/send-the-user-a-progressive-response.html
