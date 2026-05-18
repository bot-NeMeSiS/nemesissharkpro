
(function(){
function injectLiveCenter(){
 if(document.querySelector('.v337-live-command')) return;
 var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
 if(!target) return;

 var box=document.createElement('section');
 box.className='v337-live-command';

 box.innerHTML='<div class="v337-head"><h2>LIVE COMMAND CENTER</h2><span class="v337-badge">SHARK LIVE MODE</span></div><div class="v337-grid"><div class="v337-panel"><strong>Partidos prioritarios</strong><div class="v337-live-cards"><div class="v337-live-card v337-hot"><strong><span>🔥 Partido explotando</span><span>72'</span></strong><small>Momentum alto y ritmo ofensivo creciendo.</small></div><div class="v337-live-card v337-green"><strong><span>🟢 Entrada interesante</span><span>51'</span></strong><small>SHARK detecta estabilidad favorable.</small></div><div class="v337-live-card v337-gold"><strong><span>⚠️ Riesgo subiendo</span><span>63'</span></strong><small>El valor empieza a desaparecer.</small></div></div><div class="v337-timeline"><div class="v337-point"><strong>Min 12</strong><small>Dominio local inicial.</small></div><div class="v337-point"><strong>Min 31</strong><small>SHARK detecta peligro ofensivo.</small></div><div class="v337-point"><strong>Min 58</strong><small>Sube presión visitante.</small></div></div></div><div class="v337-panel"><strong>LIVE PRIORITY ENGINE</strong><div class="v337-alerts"><div class="v337-alert">🚨 Gol reciente detectado.</div><div class="v337-alert">👑 Partido con valor potencial.</div><div class="v337-alert">🦈 SHARK recomienda vigilar el live.</div></div></div></div><div class="v337-cta"><a href="/cliente/live-central"><strong>🔥 Abrir Live</strong><small>Centro principal de partidos.</small></a><a href="/cliente/1x2"><strong>👑 Ver 1X2</strong><small>Entradas rápidas.</small></a><a href="/cliente/intelligence-hub"><strong>📊 Intelligence</strong><small>Lectura avanzada.</small></a><a href="/cliente/shark-ai-pro"><strong>🦈 SHARK</strong><small>Modo live contextual.</small></a></div>';

 var ref=document.querySelector('.v336-personal-strip') || document.querySelector('.v335-intel-strip') || target.firstChild;

 if(ref && ref.parentNode){
   ref.parentNode.insertBefore(box,ref.nextSibling);
 }else{
   target.insertBefore(box,target.firstChild);
 }
}

function boot(){
 document.documentElement.classList.add('v337-live-command-ready');
 injectLiveCenter();
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
