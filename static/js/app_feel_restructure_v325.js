
(function(){
function cleanOld(){document.querySelectorAll('.v319-quick-injected,.v320-1x2-tab,.v321-force-1x2').forEach(function(el){el.remove();});}
function createNav(){document.querySelectorAll('.v325-bottom-nav').forEach(function(el){el.remove();});var nav=document.createElement('nav');nav.className='v325-bottom-nav';nav.setAttribute('aria-label','Navegación principal cliente');[['🏠','Inicio','/cliente/pro',''],['🎯','Picks','/picks',''],['📅','Partidos','/fixtures/today-pro',''],['👑','1X2','/cliente/1x2','v325-primary'],['🔥','Live','/cliente/live-central',''],['⭐','Favoritos','/cliente/favoritos',''],['🦈','SHARK','/cliente/shark-ai-pro','']].forEach(function(it){var a=document.createElement('a');a.href=it[2];if(it[3])a.className=it[3];a.innerHTML='<span>'+it[0]+'</span><small>'+it[1]+'</small>';nav.appendChild(a);});document.body.appendChild(nav);}
function boot(){document.body.classList.add('v325-app-feel-ready');cleanOld();createNav();document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');document.documentElement.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');document.body.style.overflowY='auto';document.documentElement.style.overflowY='auto';}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();setTimeout(boot,700);
})();
