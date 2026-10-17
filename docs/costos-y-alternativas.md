# Cuanto cuesta preguntar y como cambiar de proveedor

Consulta de precios: 16 de octubre de 2026, hora de El Salvador. Los precios pueden cambiar. Estos calculos no actualizan ningun plan ni constituyen una factura.

## Si sigo haciendo preguntas

Cada consulta aceptada puede consumir inferencia y evaluaciones de filtros, ademas de Lambda, DynamoDB y registros. Al superar 15 consultas por usuario en una ventana horaria UTC, la aplicacion deja de invocar el modelo para ese usuario. La solicitud a Lambda y el intento de comprobar el contador siguen siendo operaciones AWS; el limite no es un bloqueo monetario global.

El historial tambien se envia como entrada al modelo y se evalua segun los filtros configurados. Una pregunta de seguimiento puede costar mas que una pregunta aislada aunque ambas sean cortas. Una consulta bloqueada por Guardrails puede consumir evaluacion del filtro sin generar inferencia; no equivale a una llamada gratuita.

## Ejemplo reproducible de inferencia de texto

Supuestos: 1,000 consultas; cada una tiene 1,000 tokens de entrada no almacenada en cache y 140 tokens facturables de salida. Se excluyen herramientas, audio de OpenAI, escrituras de cache e impuestos. Alexa ya realiza el reconocimiento y la sintesis de voz de esta skill; no es obligatorio contratar una API de audio adicional para cambiar el modelo de texto.

| Modelo / proveedor | USD por millon de tokens de entrada | USD por millon de tokens de salida | USD por las 1,000 consultas del ejemplo |
| --- | ---: | ---: | ---: |
| Amazon Nova Micro, regional | 0.035 | 0.14 | 0.0546 |
| OpenAI GPT-6 Luna, Standard, contexto corto | 0.10 | 0.50 | 0.17 |
| OpenAI GPT-6.1 Sol, Standard, contexto corto | 2.00 | 10.00 | 3.40 |

Formula: consultas multiplicado por ((tokens de entrada / 1,000,000 * tarifa de entrada) + (tokens de salida / 1,000,000 * tarifa de salida)). En modelos que generan razonamiento, la salida facturable puede incluir tokens que no se escuchan como respuesta; no estimes el costo contando solo palabras habladas.

Estos modelos son ejemplos de tarifas, no una prueba de que todos cumplan el tiempo de respuesta de Alexa en esta aplicacion. La ruta implementada y probada utiliza Nova Micro; OpenAI todavia no esta integrado.

## Los filtros actuales tienen un costo separado

Para el camino Converse/Guardrails usado aqui, la referencia consultada publica USD 0.15 por 1,000 unidades para filtros de contenido y USD 0.10 por 1,000 unidades para informacion sensible. Una unidad tiene hasta 1,000 caracteres; se redondea al entero superior. Se evalua la entrada y la salida cuando corresponda. Las tres categorias de contenido configuradas pertenecen a esa politica de contenido; no son tres modelos de texto adicionales.

Suponiendo 1 a 4 unidades de entrada y 1 unidad de salida por consulta, los dos tipos de filtro suman aproximadamente USD 0.50 a USD 1.25 por cada 1,000 consultas permitidas. El numero real de unidades depende del texto y del historial. La inferencia se suma por separado.

Para 100 consultas al dia durante 30 dias, el ejemplo con Nova Micro y esos filtros cuesta aproximadamente USD 1.66 a USD 3.91, antes de los otros servicios AWS, beneficios o creditos aplicables e impuestos. No se debe presentar ese rango como costo total garantizado.

No se calculo aqui una factura completa de Lambda, DynamoDB, CloudWatch y trafico. Sus beneficios gratuitos y las cuotas pueden variar por cuenta; ademas, una cuenta puede tener otros proyectos. Revisa Billing y los recursos etiquetados del laboratorio. Un aviso de presupuesto normalmente no bloquea por si mismo el consumo.

## ¿Puedo usar una API de OpenAI?

Si. Se puede adaptar el backend para invocar una API de texto de OpenAI mediante credenciales propias. La API tambien puede alimentar otras aplicaciones, como una web o una automatizacion. Ese cambio requiere codigo, limites, tratamiento seguro de la clave y nuevas pruebas de latencia y contenido. La arquitectura de la skill actual no cambia automaticamente por pagar una cuenta de otro proveedor.

Una clave de API utiliza la facturacion y condiciones de esa API. No confundas disponer de una suscripcion de ChatGPT con haber configurado la autenticacion y la facturacion para esta integracion. Existen otros mecanismos de acceso, como Sign in with ChatGPT para aplicaciones elegibles, que necesitan su propia autorizacion y desarrollo; este laboratorio no los implementa.

Cambiar Bedrock por OpenAI tambien cambia el alcance academico del proyecto solicitado. Si el docente exige Bedrock, conserva y demuestra esa ruta. Se puede desarrollar una comparacion adicional sin reemplazarla.

## Cuando termine AWS FREE

La finalizacion del plan gratuito puede cerrar el acceso a la cuenta y los recursos segun las condiciones AWS. Pagar OpenAI no extiende AWS, no conserva Lambda y no paga DynamoDB. Para mantener el backend en AWS se necesita una cuenta habilitada bajo un plan admitido por AWS; una alternativa arquitectonica es alojar el backend en otro servicio compatible con los requisitos de Alexa.

Esta practica conserva el plan FREE. Sus comprobaciones bloquean despliegues con un plan distinto para impedir una transicion accidental a pago. No se ha cambiado facturacion ni habilitado un proveedor de pago adicional.

## Fuentes oficiales

- OpenAI API Pricing: https://developers.openai.com/api/docs/pricing
- Sign in with ChatGPT: https://developers.openai.com/siwc/quickstart
- Amazon Bedrock Pricing y Guardrails: https://aws.amazon.com/bedrock/pricing/
- Ejemplo de tarifas Nova: https://aws.amazon.com/blogs/machine-learning/effective-cost-optimization-strategies-for-amazon-bedrock/
- Planes de AWS: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html
