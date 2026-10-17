'use strict';
const labs = [
  {title:'Entender el proyecto',category:'DISEÑO · SIN CONSUMO',goal:'Explica qué hace cada servicio antes de crear recursos.',html:`<ol><li>Alexa convierte tu voz en una solicitud para tu skill.</li><li>Lambda valida la skill y consulta el historial en DynamoDB.</li><li>Bedrock genera una respuesta; Guardrails evalúa contenido y datos sensibles.</li><li>Alexa pronuncia el texto. CloudWatch guarda tiempos y fallos, sin preguntas ni tokens.</li></ol><div class="callout">No necesitas dominio, Google Cloud ni un servidor EC2. Una cuenta Amazon Developer y una cuenta AWS cumplen funciones distintas.</div><p><b>Prueba:</b> explica el recorrido de “explica qué es una VPN”. <b>Evidencia:</b> un diagrama propio y una explicación de cada componente.</p>`},
  {title:'Preparar tu computadora',category:'LOCAL · SIN CONSUMO',goal:'Instala las dependencias en un entorno separado y ejecuta las pruebas.',html:`<p>Descomprime el paquete del taller en tu propia carpeta. Abre PowerShell allí. No copies archivos .secrets de otra persona.</p><pre>cd "C:\\Dev\\16 Alexa Bedrock"
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
.\\.venv\\Scripts\\python.exe lab.py test
.\\.venv\\Scripts\\python.exe lab.py serve</pre><p><b>Resultado esperado:</b> pruebas locales correctas y taller en http://127.0.0.1:8092. Son pruebas con respuestas simuladas, no llamadas AWS.</p>`},
  {title:'Conversar sin gastar',category:'SIMULACIÓN LOCAL',goal:'Observa una pregunta, su seguimiento y el borrado de memoria.',html:`<ol><li>En el simulador inferior pregunta “qué es Lambda”.</li><li>Después pregunta “dame un ejemplo”. Observa la referencia al tema anterior.</li><li>Pulsa “Olvidar conversación” y repite la pregunta de seguimiento.</li></ol><div class="callout">Las respuestas son fijas. El filtro mostrado es ilustrativo; no acredita Guardrails. No introduzcas información personal.</div><p><b>Evidencia:</b> captura del recorrido y explicación de por qué un historial cambia una respuesta.</p><p><a href="#simulador">Ir al simulador ↓</a></p>`},
  {title:'Conectar tu propia AWS',category:'CONSULTAS AWS · CUENTA PROPIA',goal:'Comprueba identidad, plan, créditos y disponibilidad del modelo.',html:`<p>Instala AWS CLI v2. Autentícate con el mecanismo oficial de tu cuenta: <code>aws login</code> o <code>aws configure sso</code> si tu institución usa IAM Identity Center. Nunca uses un perfil prestado.</p><pre>aws login --profile alexa-estudiante --region us-east-1
python lab.py init --student TU-CARNET --account TU-ID-AWS --profile alexa-estudiante
python lab.py doctor</pre><p>Sustituye TU-ID-AWS por tus 12 dígitos. El comando bloquea cuentas distintas, planes que no sean FREE y modelos sin acceso confirmado.</p><div class="callout">Crédito no significa uso ilimitado. Si AWS exige actualizar a pago o contratar una suscripción, detente. No aceptes ese cambio para seguir el taller.</div><p><b>Evidencia:</b> cuenta propia, plan vigente, vencimiento y disponibilidad. Oculta información personal y nunca captures claves.</p>`},
  {title:'Crear la skill de Alexa',category:'AMAZON DEVELOPER',goal:'Crea tu propia skill en español y obtiene su identificador.',html:`<ol><li>Abre <a href="https://developer.amazon.com/alexa/console/ask" target="_blank" rel="noreferrer">Amazon Developer ↗</a> con la cuenta de tu Echo.</li><li>Completa personalmente el registro si se solicita y revisa los términos.</li><li>Crea una custom skill “Tutor académico”, idioma Español (México), con backend propio / Provision your own.</li><li>En Build → JSON Editor pega <code>skill/interaction-model.es-MX.json</code>. Guarda y construye el modelo.</li><li>Copia tu Skill ID y reemplaza el valor skill_id de tu <code>lab.json</code>.</li></ol><p>Di “explica” o “pregunta” antes de la consulta. El tipo AMAZON.SearchQuery necesita esa frase inicial.</p><p><b>Evidencia:</b> Skill ID propio y modelo construido. No compartas sesiones ni contraseñas.</p>`},
  {title:'Desplegar Lambda y Bedrock',category:'AWS REAL · CONSUME CRÉDITOS',goal:'Crea únicamente los recursos etiquetados de tu laboratorio.',html:`<pre>python lab.py probe
python lab.py build
python lab.py deploy</pre><p><code>probe</code> consume una inferencia pequeña de Nova Micro. <code>deploy</code> crea un stack CloudFormation con Lambda, rol IAM, DynamoDB, Guardrails y registros de siete días.</p><ol><li>Espera el despliegue sin ejecutarlo dos veces.</li><li>Copia FunctionArn en Endpoint de tu skill y guarda.</li><li>Activa Test → Development en Amazon Developer.</li></ol><div class="callout">El rol tiene acceso al modelo, tabla y Guardrail concretos. La invocación está limitada a tu Skill ID. Reserva de concurrencia cuando la cuota lo permite y 15 preguntas por usuario/hora reducen uso, pero no son un presupuesto monetario.</div><p><b>Evidencia:</b> stack completo, ARN, respuesta real de probe y consumo observado. El modelo del PDF es un ejemplo; esta ruta usa Nova Micro. Documenta el cambio y confirma su aceptación académica.</p>`},
  {title:'Probar y medir',category:'EVIDENCIA REAL',goal:'Distingue una llamada Lambda de una conversación real en Alexa.',html:`<pre>python lab.py test-cloud</pre><p>Prueba apertura, pregunta, seguimiento, borrado y cierre con eventos sintéticos. El tiempo de CLI incluye red; no equivale al tiempo completo de Alexa.</p><ol><li>En el simulador oficial: “abre tutor académico”.</li><li>“Explica qué es Lambda”, después “explica un ejemplo del tema anterior”.</li><li>“Olvida la conversación”, después “para”.</li><li>Con datos ficticios, verifica bloqueo de información sensible y contenido no permitido.</li><li>Repite en tu Echo; registra fallos y tiempos. Una respuesta progresiva no amplía los aproximadamente ocho segundos.</li></ol><p><b>Evidencia:</b> resultados y capturas propias; conserva los casos fallidos como pendientes. No publiques el historial de personas reales.</p>`},
  {title:'Entregar, publicar y limpiar',category:'CIERRE DEL PROYECTO',goal:'Comprueba requisitos y elimina solo tus recursos cuando termines.',html:`<ul><li>Código, arquitectura y explicación de IAM.</li><li>Memoria entre turnos; persistencia y borrado de DynamoDB.</li><li>Guardrails y pruebas de latencia; errores controlados.</li><li>Prueba física en Echo. El simulador no sustituye este requisito del PDF.</li><li>Materiales de certificación, política de privacidad y publicación. Amazon revisa la skill; publicar no es automático.</li></ul><pre>python lab.py status
python lab.py package</pre><p>La guía descargable contiene la matriz de requisitos y el procedimiento de limpieza. Antes de borrar, guarda evidencias y verifica la cuenta y el nombre exacto del stack. El ZIP comparte código y guía; excluye credenciales, lab.json y resultados del propietario.</p><div class="callout">Si faltan Echo, certificación o publicación, registra “pendiente”. No marques todo como aprobado por tener una respuesta de Bedrock.</div>`}
];
let selected=0;
let progress={};
try { progress=JSON.parse(localStorage.getItem('alexa-lab-progress-v1')||'{}'); } catch {}
if (!progress || typeof progress!=='object' || Array.isArray(progress)) progress={};
const $=id=>document.getElementById(id);
function render(){
  $('lab-nav').replaceChildren();
  labs.forEach((lab,i)=>{const button=document.createElement('button');button.className='nav-button'+(i===selected?' active':'')+(progress[i]?' done':'');button.setAttribute('aria-current',i===selected?'step':'false');const number=document.createElement('span');number.className='num';number.textContent=String(i+1).padStart(2,'0');const title=document.createElement('span');title.textContent=lab.title;button.append(number,title);button.addEventListener('click',()=>{selected=i;render();});$('lab-nav').append(button);});
  const lab=labs[selected];$('lab-title').textContent=lab.title;$('lab-category').textContent=lab.category;$('lab-number').textContent=String(selected+1).padStart(2,'0')+' / 08';$('lab-goal').textContent=lab.goal;
  // Contenido de autor constante; ninguna entrada de usuario se interpreta como HTML.
  $('lab-content').innerHTML=lab.html;
  $('reviewed').checked=!!progress[selected];$('progress-label').textContent=labs.filter((_,i)=>progress[i]).length+' de 8 prácticas revisadas';$('next-lab').textContent=selected===7?'Volver al inicio ↑':'Siguiente práctica →';
  document.querySelectorAll('#lab-content pre').forEach(pre=>{const wrapper=document.createElement('div');wrapper.className='code-wrap';pre.replaceWith(wrapper);wrapper.append(pre);const copy=document.createElement('button');copy.className='copy';copy.textContent='Copiar';copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(pre.textContent);copy.textContent='Copiado';}catch{copy.textContent='Selecciona el texto';}});wrapper.append(copy);});
}
$('reviewed').addEventListener('change',()=>{progress[selected]=$('reviewed').checked;try{localStorage.setItem('alexa-lab-progress-v1',JSON.stringify(progress));}catch{}render();});
$('next-lab').addEventListener('click',()=>{selected=(selected+1)%labs.length;render();$('laboratorios').scrollIntoView();});
let history=[];
function browserSimulation(question,previous){
  const q=question.toLowerCase();
  if(['contraseña','tarjeta','lastimar'].some(word=>q.includes(word)))return 'Simulación de filtro: usa una pregunta académica sin información sensible.';
  if(q.includes('ejemplo')&&previous.length)return 'Simulación de memoria: recuerdo tu pregunta anterior sobre '+previous[previous.length-1].question.slice(0,80)+'. En AWS, el modelo recibe ese historial para responder.';
  if(q.includes('lambda'))return 'Lambda ejecuta tu código cuando llega una solicitud. No necesitas administrar un servidor encendido.';
  if(q.includes('bedrock'))return 'Bedrock permite invocar modelos de inteligencia artificial desde tu aplicación. En este proyecto, Lambda le envía tu pregunta.';
  if(q.includes('red')||q.includes('vpn'))return 'Una red conecta dispositivos para intercambiar información. Una VPN crea una conexión protegida entre redes o equipos.';
  return 'Simulación con respuestas fijas: Alexa recibe la pregunta, Lambda la procesa y Bedrock genera la respuesta. Esta demostración no consume AWS.';
}
function bubble(text,kind){const p=document.createElement('p');p.className='bubble '+kind;p.textContent=text;$('messages').append(p);$('messages').scrollTop=$('messages').scrollHeight;}
$('chat-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const question=$('question').value.trim();
  if(!question)return;
  const button=event.currentTarget.querySelector('button');
  button.disabled=true;
  $('chat-error').textContent='';
  bubble(question,'user');
  $('question').value='';
  try{
    let data;
    // El sitio publico simula en el navegador: nunca envia preguntas a GitHub o AWS.
    if(['127.0.0.1','localhost'].includes(location.hostname)){
      const response=await fetch('./api/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,history})});
      data=[404,405,501].includes(response.status)?{answer:browserSimulation(question,history)}:await response.json();
      if(!response.ok&&![404,405,501].includes(response.status))throw Error(data.error||'No se pudo simular.');
    }else{
      data={answer:browserSimulation(question,history)};
    }
    bubble(data.answer,'bot');
    history=[...history,{question,answer:data.answer}].slice(-3);
  }catch(error){
    $('chat-error').textContent=error.message;
  }finally{
    button.disabled=false;
    $('question').focus();
  }
});
$('clear-chat').addEventListener('click',()=>{history=[];$('messages').replaceChildren();bubble('Conversación local borrada. Di qué tema quieres practicar.','bot');});
$('export-progress').addEventListener('click',()=>{const data={exported_at:new Date().toISOString(),kind:'self-reported-reading-progress',practices:labs.map((lab,i)=>({practice:lab.title,reviewed:!!progress[i]})),cloud_test:'pending-separate-evidence',echo:'pending-separate-evidence',certification:'pending-separate-evidence'};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const anchor=document.createElement('a');anchor.href=url;anchor.download='mi-avance-alexa.json';anchor.click();URL.revokeObjectURL(url);});
fetch('./api/status').then(response=>response.json()).then(data=>{$('test-status').textContent=data.local_tests_passed===true?'Pruebas locales del código: correctas. Alexa, Echo y certificación requieren evidencias aparte.':'Ejecuta python lab.py test para registrar las pruebas locales. Las pruebas cloud y Echo son independientes.';}).catch(()=>{$('test-status').textContent='Consulta las evidencias desde la CLI del taller.';});
render();
fetch('./capturas.json').then(r=>r.json()).then(items=>{items.forEach(item=>{if(!/^[a-zA-Z0-9-]+\.jpg$/.test(item.file))return;const figure=document.createElement('figure');const link=document.createElement('a');link.href='./capturas/'+item.file;link.target='_blank';link.rel='noreferrer';const img=document.createElement('img');img.src=link.href;img.alt=item.title;img.loading='lazy';link.append(img);const caption=document.createElement('figcaption');const title=document.createElement('b');title.textContent=item.title;const detail=document.createElement('p');detail.textContent=item.description;caption.append(title,detail);figure.append(link,caption);$('captures').append(figure);});}).catch(()=>{$('captures').textContent='Las capturas se encuentran en docs/capturas del paquete.';});
fetch('./evidencias.json').then(r=>r.json()).then(data=>{$('evidence-example').textContent='Ejemplo del autor: '+data.local_tests+' pruebas locales '+(data.local_tests_passed?'correctas':'por revisar')+'. '+data.lambda_tests+'. Simulador Alexa: '+data.alexa_simulator+'. Echo: '+data.echo+'. Certificación: '+data.certification+'. '+data.note;}).catch(()=>{$('evidence-example').textContent='Consulta el estado documentado en la guía del proyecto.';});
