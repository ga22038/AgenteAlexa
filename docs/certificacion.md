# Preparacion para certificacion y publicacion

Estado: pendiente de revision y aprobacion de Amazon. El proyecto funciona en desarrollo; esto no equivale a publicacion.

## Datos propuestos para la ficha

- Nombre: Tutor Academico IA.
- Idioma: Español (Mexico).
- Invocacion: tutor academico.
- Audiencia prevista: estudiantes universitarios y publico general; no se presenta como una skill dirigida a niños.
- Descripcion breve: Practica conceptos de tecnologia con explicaciones breves generadas por inteligencia artificial.
- Descripcion: Abre tutor academico y di explica seguido de tu pregunta. El tutor utiliza Amazon Bedrock para generar respuestas breves. Puede mantener el tema de la conversacion y borrar su historial cuando dices olvida la conversacion. Las respuestas pueden contener errores; contrastalas con tus materiales de estudio. No compartas datos personales.
- Frases de ejemplo: Alexa, abre tutor academico; explica que es AWS Lambda; explica un ejemplo del tema anterior.

## Materiales que faltan antes de enviar

1. Iconos originales en los tamaños solicitados por la consola.
2. URL publica de una politica de privacidad que describa al responsable real de cada skill y su contacto. No copies el nombre o correo del autor en las skills de los compañeros.
3. Revision del tratamiento de historial: hash del identificador de usuario, hasta tres pares, vencimiento logico 30 minutos y eliminacion fisica asincrona por TTL. El comando de borrado elimina el historial inmediatamente cuando DynamoDB confirma la operacion. Los contadores de uso tienen TTL independiente.
4. Declaracion de IA generativa, clasificacion de contenido y respuestas a las preguntas vigentes de Amazon. Verifica las reglas actuales en la consola antes de enviar.
5. Pruebas completas de apertura, consulta, ayuda, seguimiento, borrado, cancelacion, cierre, filtros y manejo de fallos.
6. Medicion de varias consultas en el simulador y un Echo, incluyendo errores. No declarar que nunca se supera un tiempo sin evidencia suficiente.
7. Revision de acceso AWS, presupuesto y tiempo de permanencia de los recursos. Una skill publicada puede recibir mas uso que una demostracion del grupo.

## Instrucciones de prueba para el revisor

Abre tutor academico. Di explica que es AWS Lambda. Luego di explica un ejemplo del tema anterior. Di ayuda para las instrucciones. Di olvida la conversacion para borrar el historial. Di para para terminar. No requiere compras ni vinculacion de cuentas. El contenido se genera mediante IA y no debe usarse como sustituto de materiales academicos verificados.

Estos textos son borradores revisables. No garantizan certificacion. El envio publico debe realizarse despues de completar los datos y verificar el comportamiento real.
