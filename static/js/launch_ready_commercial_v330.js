
(function(){
  function injectLaunchStrip(){
    if(document.querySelector('.v330-launch-strip')) return;
    var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
    if(!target) return;
    var strip=document.createElement('section');
    strip.className='v330-launch-strip';
    strip.innerHTML='<div><strong>🦈 Modo Beta Comercial</strong><br><small>App lista para enseñar a clientes en beta controlada. REAL ONLY activo.</small></div><a href="/launch-ready-v330">Revisar puesta en marcha</a>';
    target.insertBefore(strip,target.firstChild);
  }
  function boot(){
    document.documentElement.classList.add('v330-launch-ready');
    document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
    document.body.style.overflowY='auto';
    document.documentElement.style.overflowY='auto';
    injectLaunchStrip();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  setTimeout(boot,900);
})();
