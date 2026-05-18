
(function(){
function injectDataStrip(){
  if(document.querySelector('.v346-data-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;

  var strip=document.createElement('section');
  strip.className='v346-data-strip';
  strip.innerHTML='<div><strong>📡 Datos reales y Live Pipeline</strong><small>Diagnóstico de API, caché, partidos, minuto, marcador, escudos y 1X2.</small></div><a href="/cliente/real-data-pipeline">Revisar datos</a>';

  var ref=document.querySelector('.v345-shell') || document.querySelector('.v344-shell') || target.firstChild;
  if(ref && ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling);}else{target.insertBefore(strip,target.firstChild);}
}

function boot(){
  document.documentElement.classList.add('v346-real-data-ready');
  injectDataStrip();
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setTimeout(boot,900);
})();
