
(function(){
  function dismissed(){return localStorage.getItem('v334_onboarding_dismissed')==='1';}
  function injectOnboarding(){
    if(dismissed() || document.querySelector('.v334-onboarding')) return;
    var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
    if(!target) return;
    var box=document.createElement('section');
    box.className='v334-onboarding';
    box.innerHTML=[
      '<div class="v334-onboarding-head"><h2>Primeros pasos SHARK</h2><span>Guía rápida cliente</span></div>',
      '<div class="v334-steps">',
      '<a class="v334-step" href="/fixtures/today-pro"><b>📅</b><strong>1. Partidos hoy</strong><small>Empieza viendo qué se juega.</small></a>',
      '<a class="v334-step green" href="/cliente/live-central"><b>🔥</b><strong>2. Live</strong><small>Revisa marcador y minuto.</small></a>',
      '<a class="v334-step gold" href="/cliente/1x2"><b>👑</b><strong>3. 1X2</strong><small>Local, empate o visitante.</small></a>',
      '<a class="v334-step" href="/cliente/match-center-premium"><b>📊</b><strong>4. Match Center</strong><small>Todo el partido en una ficha.</small></a>',
      '<a class="v334-step" href="/cliente/favorites-following"><b>⭐</b><strong>5. Seguir</strong><small>Guarda lo importante.</small></a>',
      '<a class="v334-step" href="/cliente/shark-ai-pro"><b>🦈</b><strong>6. SHARK</strong><small>Pregunta antes de decidir.</small></a>',
      '</div><div class="v334-dismiss"><button type="button" data-v334-dismiss>Entendido</button></div>'
    ].join('');
    var ref=document.querySelector('.v333-perf-strip') || document.querySelector('.v332-decision-flow') || target.firstChild;
    if(ref && ref.parentNode) ref.parentNode.insertBefore(box, ref.nextSibling); else target.insertBefore(box,target.firstChild);
    var btn=box.querySelector('[data-v334-dismiss]');
    if(btn) btn.addEventListener('click',function(){localStorage.setItem('v334_onboarding_dismissed','1');box.remove();});
  }
  function boot(){
    document.documentElement.classList.add('v334-onboarding-ready');
    injectOnboarding();
    document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
    document.body.style.overflowY='auto';document.documentElement.style.overflowY='auto';
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  setTimeout(boot,900);
})();
