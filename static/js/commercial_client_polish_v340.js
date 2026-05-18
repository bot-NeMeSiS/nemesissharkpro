
(function(){
function cleanCommercialNoise(){
  document.querySelectorAll('.debug,.debug-panel,.dev-note,.technical-note,.api-debug,.json-debug,[data-debug="true"],[data-dev="true"],.vapid-warning,.push-config-warning').forEach(function(el){
    el.remove();
  });

  document.querySelectorAll('*').forEach(function(el){
    var txt=(el.textContent||'').trim().toLowerCase();
    if(txt.includes('demo') || txt.includes('placeholder') || txt.includes('test mode')){
      if(el.children.length===0 && txt.length<80){
        el.textContent=el.textContent.replace(/demo/ig,'beta').replace(/placeholder/ig,'datos pendientes').replace(/test mode/ig,'modo beta');
      }
    }
  });
}

function injectCommercialStrip(){
  if(document.querySelector('.v340-commercial-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;

  var strip=document.createElement('section');
  strip.className='v340-commercial-strip';
  strip.innerHTML='<div><strong>🦈 Experiencia Premium Beta</strong><small>Datos reales, lectura SHARK y decisiones guiadas en un entorno comercial limpio.</small></div><a href="/cliente/v340-commercial-polish">Revisar experiencia</a>';

  var ref=document.querySelector('.v337-live-command') || document.querySelector('.v336-personal-strip') || target.firstChild;

  if(ref && ref.parentNode){
    ref.parentNode.insertBefore(strip,ref.nextSibling);
  }else{
    target.insertBefore(strip,target.firstChild);
  }
}

function boot(){
  document.documentElement.classList.add('v340-commercial-polish-ready');
  cleanCommercialNoise();
  injectCommercialStrip();
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',boot);
}else{
  boot();
}
setTimeout(boot,900);
})();
