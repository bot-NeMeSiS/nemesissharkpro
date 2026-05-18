
(function(){
function injectClientExperienceStrip(){
  if(document.querySelector('.v350-client-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;

  var strip=document.createElement('section');
  strip.className='v350-client-strip';
  strip.innerHTML='<div><strong>🦈 Experiencia cliente consolidada</strong><small>Ruta limpia: Inicio → Partidos → 1X2 → Live → Match → Favoritos → SHARK.</small></div><a href="/cliente/experience-final">Abrir hub</a>';

  var ref=document.querySelector('.v349-shell') || document.querySelector('.v348-ui-strip') || target.firstChild;
  if(ref && ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling);}else{target.insertBefore(strip,target.firstChild);}
}

function ensureCoreNavigationLinks(){
  document.querySelectorAll('a[href="/cliente/live"]').forEach(function(a){ a.href='/cliente/live-command-center'; });
  document.querySelectorAll('a[href="/cliente/favoritos"]').forEach(function(a){ a.href='/cliente/favorites-following'; });
  document.querySelectorAll('a[href="/cliente/picks"]').forEach(function(a){ a.href='/picks'; });
}

function boot(){
  document.documentElement.classList.add('v350-client-experience-ready');
  injectClientExperienceStrip();
  ensureCoreNavigationLinks();
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setTimeout(boot,900);
})();
