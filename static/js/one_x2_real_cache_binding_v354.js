
(function(){
function card(r){
 var odds=r.odds_1x2||{};
 return '<article class="v354-pick"><div class="v354-teams"><span>'+ (r.home||'Local') +'</span><span>'+ (r.away||'Visitante') +'</span></div><div class="v354-league">'+(r.league||'Competición')+' · '+(r.minute||'Pre')+' · '+(r.score||'vs')+'</div><div class="v354-choice"><span>Recomendación</span><span>'+ (r.recommended||'LOW_DATA') +' · '+(r.confidence||0)+'/100</span></div><div class="v354-odds"><div class="v354-odd"><strong>1</strong><small>'+(odds["1"]||'--')+'</small></div><div class="v354-odd"><strong>X</strong><small>'+(odds["X"]||'--')+'</small></div><div class="v354-odd"><strong>2</strong><small>'+(odds["2"]||'--')+'</small></div></div><div class="v354-actions"><a class="gold" href="/cliente/1x2">1X2</a><a href="/cliente/match-center-premium">Detalle</a></div></article>';
}
async function inject(){
 if(document.querySelector('.v354-strip')) return;
 var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
 if(!target) return;
 var strip=document.createElement('section');strip.className='v354-strip';
 strip.innerHTML='<div><strong>👑 1X2 Real Cache Binding</strong><small>Combis enlazadas al caché real V353 con LOW DATA limpio.</small></div><a href="/cliente/1x2-real-cache">Abrir 1X2 real</a>';
 var ref=document.querySelector('.v353-strip')||document.querySelector('.v352-strip')||target.firstChild;
 if(ref&&ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling)}else{target.insertBefore(strip,target.firstChild)}
}
function boot(){document.documentElement.classList.add('v354-1x2-binding-ready');inject();document.body.style.overflowY='auto';document.documentElement.style.overflowY='auto'}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();setTimeout(boot,900);
})();
