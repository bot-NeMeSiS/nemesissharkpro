
(function(){
function injectPersonal(){
 if(document.querySelector('.v336-personal-strip')) return;
 var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
 if(!target) return;

 var box=document.createElement('section');
 box.className='v336-personal-strip';

 box.innerHTML='<div class="v336-head"><h2>Personalized SHARK Experience</h2><span class="v336-badge">ADAPTIVE USER MODE</span></div><div class="v336-grid"><div class="v336-panel"><span class="v336-profile">🦈 Perfil detectado: Equilibrado · 1X2 Player</span><div class="v336-items"><div class="v336-item v336-green"><strong>Premier League favorita</strong><small>Sueles revisar partidos ingleses y live intensos.</small></div><div class="v336-item"><strong>Live frecuente</strong><small>Tu uso reciente muestra interés en partidos activos.</small></div><div class="v336-item v336-gold"><strong>1X2 prioritario</strong><small>La app mostrará antes las mejores combis.</small></div><div class="v336-item"><strong>Favoritos activos</strong><small>Equipos seguidos aparecerán primero.</small></div></div><div class="v336-alerts"><div class="v336-alert">🔥 Tu equipo favorito entra en live.</div><div class="v336-alert">👑 SHARK detecta valor interesante en una liga seguida.</div><div class="v336-alert">📊 Partido parecido a los que normalmente analizas.</div></div></div><div class="v336-panel"><strong>Adaptive Home</strong><p style="color:#a8b9d1;line-height:1.5;">La app empieza a reorganizar contenido según comportamiento, ligas favoritas y tipo de apuestas.</p></div></div><div class="v336-cta"><a href="/cliente/live-central"><strong>🔥 Live personalizado</strong><small>Prioriza lo que sigues.</small></a><a href="/cliente/1x2"><strong>👑 1X2 adaptativo</strong><small>Más alineado contigo.</small></a><a href="/cliente/favorites-following"><strong>⭐ Favoritos</strong><small>Base de personalización.</small></a><a href="/cliente/shark-ai-pro"><strong>🦈 SHARK</strong><small>Lectura más personal.</small></a></div>';

 var ref=document.querySelector('.v335-intel-strip') || document.querySelector('.v334-onboarding') || target.firstChild;

 if(ref && ref.parentNode){
   ref.parentNode.insertBefore(box,ref.nextSibling);
 }else{
   target.insertBefore(box,target.firstChild);
 }
}
function boot(){
 document.documentElement.classList.add('v336-personal-ready');
 injectPersonal();
 document.body.style.overflowY='auto';
 document.documentElement.style.overflowY='auto';
}
if(document.readyState==='loading'){
 document.addEventListener('DOMContentLoaded',boot);
}else{
 boot();
}
setTimeout(boot,900);
})();
