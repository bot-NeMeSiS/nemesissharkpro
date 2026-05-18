
(function(){
function injectQaStrip(){
  if(document.querySelector('.v351-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;
  var strip=document.createElement('section');
  strip.className='v351-strip';
  strip.innerHTML='<div><strong>✅ Production Readiness QA</strong><small>Centro de revisión final: cliente, datos, 1X2, Telegram, membresías y navegación.</small></div><a href="/admin/production-readiness">Abrir QA</a>';
  var ref=document.querySelector('.v350-client-strip') || document.querySelector('.v349-shell') || target.firstChild;
  if(ref && ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling);}else{target.insertBefore(strip,target.firstChild);}
}
function boot(){
  document.documentElement.classList.add('v351-production-qa-ready');
  injectQaStrip();
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setTimeout(boot,900);
})();
