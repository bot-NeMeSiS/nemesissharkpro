
(function(){
function injectSalesFlow(){
  if(document.querySelector('.v343-sales-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;

  var box=document.createElement('section');
  box.className='v343-sales-strip';
  box.innerHTML=[
    '<div class="v343-sales-head"><h2>Planes SHARK</h2><span class="v343-badge">Beta Premium</span></div>',
    '<div class="v343-tier-grid">',
    '<div class="v343-tier"><strong>FREE</strong><small>Para probar la experiencia.</small><ul><li>Partidos hoy</li><li>Live básico</li><li>Acceso limitado SHARK</li></ul></div>',
    '<div class="v343-tier pro"><strong>PRO</strong><small>Para usar SHARK en serio.</small><ul><li>1X2 inteligente</li><li>Match Center</li><li>Decision Flow</li></ul><a class="v343-upgrade-btn" href="/cliente/membresia">Subir a PRO</a></div>',
    '<div class="v343-tier elite"><strong>ELITE</strong><small>Máxima experiencia premium.</small><ul><li>Live Command</li><li>Alertas prioritarias</li><li>SHARK personalizado</li></ul><a class="v343-upgrade-btn" href="/cliente/membresia">Ver ELITE</a></div>',
    '</div>'
  ].join('');

  var ref=document.querySelector('.v341-trust-strip') || document.querySelector('.v340-commercial-strip') || target.firstChild;
  if(ref && ref.parentNode){ref.parentNode.insertBefore(box,ref.nextSibling);}else{target.insertBefore(box,target.firstChild);}
}
function softLockPremium(){
  document.querySelectorAll('.v337-live-command,.v336-personal-strip,.v335-intel-strip').forEach(function(el){
    el.classList.add('v343-soft-lock');
  });
}
function boot(){
  document.documentElement.classList.add('v343-revenue-ready');
  injectSalesFlow();
  softLockPremium();
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setTimeout(boot,900);
})();
