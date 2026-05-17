
(function(){
  function insertDensityStrip(){
    if(document.querySelector('.v327-home-strip')) return;
    var target = document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
    if(!target) return;
    var strip=document.createElement('section');
    strip.className='v327-home-strip';
    strip.innerHTML=[
      '<a href="/fixtures/today-pro"><span>📅</span><div><strong>Partidos hoy</strong><small>Agenda rápida</small></div></a>',
      '<a href="/cliente/live-central"><span>🔥</span><div><strong>Live ahora</strong><small>Marcador y minuto</small></div></a>',
      '<a class="v327-gold" href="/cliente/1x2"><span>👑</span><div><strong>Combis 1X2</strong><small>Local · X · Visitante</small></div></a>',
      '<a href="/cliente/match-center-premium"><span>📊</span><div><strong>Match Center</strong><small>Todo en uno</small></div></a>'
    ].join('');
    target.insertBefore(strip, target.firstChild);
  }
  function boot(){
    document.body.classList.add('v327-density-ready');
    insertDensityStrip();
    document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
    document.body.style.overflowY='auto';
    document.documentElement.style.overflowY='auto';
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  setTimeout(boot,700);
})();
