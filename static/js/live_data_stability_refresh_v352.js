
(function(){
function injectLiveStabilityStrip(){
  if(document.querySelector('.v352-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;
  var strip=document.createElement('section');
  strip.className='v352-strip';
  strip.innerHTML='<div><strong>🔥 Live Stability & Refresh</strong><small>Control de frescura para live, fixtures, 1X2, escudos y LOW DATA.</small></div><a href="/cliente/live-stability">Revisar live</a>';
  var ref=document.querySelector('.v351-strip') || document.querySelector('.v350-client-strip') || target.firstChild;
  if(ref && ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling);}else{target.insertBefore(strip,target.firstChild);}
}
function addLivePulse(){
  document.querySelectorAll('.live-card,.match-card,.v337-live-command,.v348-match-card,.v347-match').forEach(function(el){
    var txt=(el.textContent||'').toLowerCase();
    if(txt.includes('live') || txt.includes("'") || txt.includes('min') || txt.includes('gol')){
      el.classList.add('v352-live-pulse');
    }
  });
}
function boot(){
  document.documentElement.classList.add('v352-live-stability-ready');
  injectLiveStabilityStrip();
  addLivePulse();
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setTimeout(boot,900);
})();
