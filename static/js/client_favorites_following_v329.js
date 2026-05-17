
(function(){
  function insertFollowStrip(){
    if(document.querySelector('.v329-follow-strip')) return;
    var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
    if(!target) return;
    var strip=document.createElement('section');
    strip.className='v329-follow-strip';
    strip.innerHTML=[
      '<a class="v329-gold" href="/cliente/favorites-following"><span>⭐</span><div><strong>Mis favoritos</strong><small>Equipos y partidos</small></div></a>',
      '<a href="/cliente/match-center-premium"><span>📊</span><div><strong>Seguidos</strong><small>Match Center</small></div></a>',
      '<a href="/cliente/live-central"><span>🔥</span><div><strong>Live seguido</strong><small>Minuto y marcador</small></div></a>',
      '<a href="/api/client/favorites/status-v329"><span>✅</span><div><strong>Estado</strong><small>Favoritos activos</small></div></a>'
    ].join('');
    var ref=document.querySelector('.v328-trust-strip') || document.querySelector('.v327-home-strip') || target.firstChild;
    if(ref && ref.parentNode) ref.parentNode.insertBefore(strip, ref.nextSibling);
    else target.insertBefore(strip,target.firstChild);
  }
  function addFollowButtons(){
    document.querySelectorAll('.match-card,.live-card,.value-card,.card').forEach(function(card){
      var txt=(card.textContent||'').toLowerCase();
      if(!txt.includes('vs') && !txt.includes('live') && !txt.includes('partido')) return;
      if(card.querySelector('.v329-follow-btn')) return;
      var a=document.createElement('a');
      a.href='/cliente/favorites-following';
      a.className='v329-follow-btn';
      a.textContent='⭐ Seguir';
      card.appendChild(a);
    });
  }
  function boot(){
    document.documentElement.classList.add('v329-favorites-following-ready');
    insertFollowStrip();
    addFollowButtons();
    document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
    document.body.style.overflowY='auto';
    document.documentElement.style.overflowY='auto';
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  setTimeout(boot,900);
})();
