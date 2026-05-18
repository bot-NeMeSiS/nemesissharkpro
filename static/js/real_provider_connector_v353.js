
(function(){
function injectProviderStrip(){
  if(document.querySelector('.v353-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;
  var strip=document.createElement('section');
  strip.className='v353-strip';
  strip.innerHTML='<div><strong>📡 Provider Connector</strong><small>API → caché → normalizador → UI → cliente, con LOW DATA si falla proveedor.</small></div><a href="/cliente/provider-connector">Revisar proveedor</a>';
  var ref=document.querySelector('.v352-strip') || document.querySelector('.v351-strip') || target.firstChild;
  if(ref && ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling);}else{target.insertBefore(strip,target.firstChild);}
}
function boot(){
  document.documentElement.classList.add('v353-provider-ready');
  injectProviderStrip();
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setTimeout(boot,900);
})();
