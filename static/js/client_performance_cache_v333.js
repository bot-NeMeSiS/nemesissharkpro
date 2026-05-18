
(function(){
  function injectPerfStrip(){
    if(document.querySelector('.v333-perf-strip')) return;
    var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
    if(!target) return;
    var strip=document.createElement('section');
    strip.className='v333-perf-strip';
    strip.innerHTML=[
      '<div class="v333-perf-item"><strong>⚡ Carga más fluida</strong><small>Estados visuales para reducir sensación de espera.</small></div>',
      '<div class="v333-perf-item"><strong>💾 Cache ready</strong><small>Base para live, partidos, 1X2 y Match Center.</small></div>',
      '<div class="v333-perf-item"><strong>🛡️ Ahorro API</strong><small>Preparado para pedir menos y reutilizar mejor.</small></div>'
    ].join('');
    var ref=document.querySelector('.v332-decision-flow') || document.querySelector('.v331-feed') || target.firstChild;
    if(ref && ref.parentNode) ref.parentNode.insertBefore(strip, ref.nextSibling);
    else target.insertBefore(strip,target.firstChild);
  }
  function tagSlowCards(){
    document.querySelectorAll('.card,.panel,.widget,.match-card,.live-card').forEach(function(el){
      var txt=(el.textContent||'').trim();
      if(txt.length<12 && !el.classList.contains('v333-skeleton')) el.classList.add('v333-skeleton');
    });
  }
  function boot(){
    document.documentElement.classList.add('v333-performance-cache-ready');
    injectPerfStrip();
    tagSlowCards();
    document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
    document.body.style.overflowY='auto';
    document.documentElement.style.overflowY='auto';
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  setTimeout(boot,900);
})();
