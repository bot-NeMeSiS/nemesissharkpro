
(function(){
function inject(){
 if(document.querySelector('.v356-strip')) return;
 var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
 if(!target) return;
 var strip=document.createElement('section');strip.className='v356-strip';
 strip.innerHTML='<div><strong>🦈 SHARK Real Data Analyst</strong><small>SHARK ahora lee Match Center real, 1X2 y caché proveedor.</small></div><a href="/cliente/shark-real-analyst">Abrir SHARK real</a>';
 var ref=document.querySelector('.v355-strip')||document.querySelector('.v354-strip')||target.firstChild;
 if(ref&&ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling)}else{target.insertBefore(strip,target.firstChild)}
}
function boot(){document.documentElement.classList.add('v356-shark-real-ready');inject();document.body.style.overflowY='auto';document.documentElement.style.overflowY='auto'}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();setTimeout(boot,900);
})();
