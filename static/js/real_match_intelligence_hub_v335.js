
(function(){
function injectHub(){
 if(document.querySelector('.v335-intel-strip')) return;
 var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
 if(!target) return;

 var box=document.createElement('section');
 box.className='v335-intel-strip';
 box.innerHTML='<div class="v335-top"><h2>Match Intelligence Hub</h2><span class="v335-badge">SHARK ANALYST MODE</span></div><div class="v335-grid"><div class="v335-panel"><strong>Lectura inteligente del partido</strong><div class="v335-states"><div class="v335-state v335-green"><strong>Local dominando</strong><small>Presión ofensiva estable y control del ritmo.</small></div><div class="v335-state v335-gold"><strong>Momentum visitante</strong><small>Empieza a crecer en transición.</small></div><div class="v335-state"><strong>Partido caliente</strong><small>Ritmo alto y posibilidad de cambios rápidos.</small></div><div class="v335-state v335-red"><strong>Riesgo sorpresa</strong><small>Entrar tarde puede ser peligroso.</small></div></div><div class="v335-bars"><div><div class="v335-bar-head"><span>Ataque local</span><span>82%</span></div><div class="v335-bar"><div class="v335-fill blue"></div></div></div><div><div class="v335-bar-head"><span>Confianza SHARK</span><span>74%</span></div><div class="v335-bar"><div class="v335-fill green"></div></div></div><div><div class="v335-bar-head"><span>Riesgo entrada</span><span>58%</span></div><div class="v335-bar"><div class="v335-fill gold"></div></div></div></div></div><div class="v335-panel"><strong>SHARK Analyst</strong><div class="v335-analyst">SHARK vigilaría la evolución live antes de entrar fuerte al 1X2. El contexto favorece al local, pero el riesgo sorpresa sigue activo.</div></div></div><div class="v335-cta"><a href="/cliente/1x2"><strong>👑 Ver 1X2</strong><small>Entender por qué 1/X/2.</small></a><a href="/cliente/match-center-premium"><strong>📊 Match Center</strong><small>Contexto completo.</small></a><a href="/cliente/live-central"><strong>🔥 Live</strong><small>Revisar minuto y marcador.</small></a><a href="/cliente/shark-ai-pro"><strong>🦈 SHARK</strong><small>Lectura rápida IA.</small></a></div>';
 var ref=document.querySelector('.v334-onboarding') || document.querySelector('.v333-perf-strip') || target.firstChild;
 if(ref && ref.parentNode){ref.parentNode.insertBefore(box,ref.nextSibling);} else {target.insertBefore(box,target.firstChild);}
}
function boot(){
 document.documentElement.classList.add('v335-intelligence-ready');
 injectHub();
 document.body.style.overflowY='auto';
 document.documentElement.style.overflowY='auto';
}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',boot);} else {boot();}
setTimeout(boot,900);
})();
