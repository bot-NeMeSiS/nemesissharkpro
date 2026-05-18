
(function(){
function inject(){
 if(document.querySelector('.v355-strip')) return;
 var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
 if(!target) return;
 var strip=document.createElement('section'); strip.className='v355-strip';
 strip.innerHTML='<div><strong>📊 Match Center Real Data</strong><small>Match Center enlazado a cuotas reales/cacheadas y recomendación 1X2.</small></div><a href="/cliente/match-center-real">Abrir Match Real</a>';
 var ref=document.querySelector('.v354-strip')||document.querySelector('.v353-strip')||target.firstChild;
 if(ref&&ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling)}else{target.insertBefore(strip,target.firstChild)}
}
function boot(){document.documentElement.classList.add('v355-match-real-ready');inject();document.body.style.overflowY='auto';document.documentElement.style.overflowY='auto'}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();setTimeout(boot,900);
})();
