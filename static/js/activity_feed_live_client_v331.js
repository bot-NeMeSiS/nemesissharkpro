
(function(){
  function injectFeed(){
    if(document.querySelector('.v331-feed')) return;
    var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
    if(!target) return;
    var feed=document.createElement('section');
    feed.className='v331-feed';
    feed.innerHTML=[
      '<div class="v331-feed-head"><h2>Actividad recomendada</h2><span>LIVE CLIENT</span></div>',
      '<div class="v331-feed-grid">',
      '<a class="v331-feed-item green" href="/cliente/live-central"><b>🔥</b><strong>Revisar Live</strong><small>Marcador, minuto y partidos activos.</small></a>',
      '<a class="v331-feed-item gold" href="/cliente/1x2"><b>👑</b><strong>Combi 1X2</strong><small>Local, empate o visitante con REAL ONLY.</small></a>',
      '<a class="v331-feed-item" href="/cliente/match-center-premium"><b>📊</b><strong>Match Center</strong><small>Todo el partido en una ficha premium.</small></a>',
      '<a class="v331-feed-item" href="/cliente/favorites-following"><b>⭐</b><strong>Seguidos</strong><small>Equipos y partidos importantes.</small></a>',
      '</div>'
    ].join('');
    var ref=document.querySelector('.v330-launch-strip') || document.querySelector('.v329-follow-strip') || document.querySelector('.v328-trust-strip') || target.firstChild;
    if(ref && ref.parentNode) ref.parentNode.insertBefore(feed, ref.nextSibling);
    else target.insertBefore(feed,target.firstChild);
  }
  function boot(){
    document.documentElement.classList.add('v331-activity-feed-ready');
    injectFeed();
    document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
    document.body.style.overflowY='auto';
    document.documentElement.style.overflowY='auto';
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  setTimeout(boot,900);
})();
