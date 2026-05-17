
(function(){
function injectDecisionFlow(){
if(document.querySelector('.v332-decision-flow')) return;
var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
if(!target) return;
var box=document.createElement('section');
box.className='v332-decision-flow';
box.innerHTML='<div class="v332-head"><h2>Decision Flow SHARK</h2><span class="v332-live-badge">REAL ONLY</span></div><div class="v332-grid"><div class="v332-main-card"><span class="v332-state v332-wait">⏳ ESPERAR</span><h3>SHARK vigilaría este partido</h3><p>La app guía visualmente cuándo entrar o esperar.</p><div class="v332-bars"><div><small>Confianza 78%</small><div class="v332-bar"><div class="v332-green"></div></div></div><div><small>Riesgo 61%</small><div class="v332-bar"><div class="v332-gold"></div></div></div><div><small>Momentum local 72%</small><div class="v332-bar"><div class="v332-blue"></div></div></div></div></div><div class="v332-side-card"><span class="v332-state v332-good">🟢 PARTIDO VIGILABLE</span><p>SHARK esperaría alineaciones y revisaría live antes de entrar.</p></div></div><div class="v332-cta"><a class="gold" href="/cliente/1x2"><strong>👑 Ver 1X2</strong><small>Combis rápidas.</small></a><a href="/cliente/match-center-premium"><strong>📊 Match Center</strong><small>Ficha premium.</small></a><a href="/cliente/favorites-following"><strong>⭐ Seguir</strong><small>Guardar partido.</small></a><a href="/cliente/shark-ai-pro"><strong>🦈 Preguntar SHARK</strong><small>Explicación rápida.</small></a></div>';
var ref=document.querySelector('.v331-feed') || target.firstChild;
if(ref && ref.parentNode){ref.parentNode.insertBefore(box, ref.nextSibling);}else{target.insertBefore(box,target.firstChild);}
}
function boot(){document.documentElement.classList.add('v332-decision-flow-ready');injectDecisionFlow();document.body.style.overflowY='auto';document.documentElement.style.overflowY='auto';}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',boot);}else{boot();}
setTimeout(boot,900);
})();
