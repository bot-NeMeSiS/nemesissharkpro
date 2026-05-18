
(function(){
  var NAV_ITEMS = [
    ['🏠','Inicio','/cliente/pro',''],
    ['📅','Partidos','/fixtures/today-pro',''],
    ['🎯','Picks','/picks',''],
    ['👑','1X2','/cliente/1x2','v349-primary'],
    ['🔥','Live','/cliente/live-command-center',''],
    ['📊','Match','/cliente/match-center-premium',''],
    ['⭐','Favs','/cliente/favorites-following','']
  ];

  function cleanOldNav(){
    document.querySelectorAll('.v319-quick-injected,.v320-1x2-tab,.v321-force-1x2,[data-v319-1x2],[data-v320-1x2],[data-v321-1x2],[data-v319-floating-1x2],[data-v320-floating-1x2]').forEach(function(el){
      el.remove();
    });

    // Remove previous bottom navs to avoid stacked bars.
    document.querySelectorAll('.v325-bottom-nav,.v349-bottom-nav').forEach(function(el){ el.remove(); });

    // Dedupe visible duplicated high-value links outside nav areas.
    var seen = {};
    Array.from(document.querySelectorAll('a')).forEach(function(a){
      if(a.closest('nav') || a.closest('header') || a.closest('.v349-bottom-nav')) return;
      var href=(a.getAttribute('href')||'').trim();
      var txt=(a.textContent||'').trim().toLowerCase().replace(/\s+/g,' ');
      if(!href || !txt) return;
      var key=href+'|'+txt;
      var interesting=/combis|1x2|live command|match center|favoritos|membres|shark|picks/.test(txt);
      if(interesting && seen[key]){
        a.remove();
      }else{
        seen[key]=true;
      }
    });
  }

  function createBottomNav(){
    var nav=document.createElement('nav');
    nav.className='v349-bottom-nav';
    nav.setAttribute('aria-label','Navegación principal cliente');

    var path=window.location.pathname;
    NAV_ITEMS.forEach(function(it){
      var a=document.createElement('a');
      a.href=it[2];
      if(it[3]) a.className=it[3];
      if(path===it[2] || (it[2] !== '/cliente/pro' && path.indexOf(it[2]) === 0)){
        a.classList.add('v349-active');
      }
      a.innerHTML='<span>'+it[0]+'</span><small>'+it[1]+'</small>';
      nav.appendChild(a);
    });

    document.body.appendChild(nav);
  }

  function unlockScroll(){
    [document.documentElement,document.body].forEach(function(el){
      if(!el) return;
      el.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll','prevent-scroll','disable-scroll');
      el.style.overflowY='auto';
      el.style.overflowX='hidden';
      el.style.height='auto';
      el.style.position='static';
    });
  }

  function unblockHiddenOverlays(){
    document.querySelectorAll('.overlay.hidden,.modal.hidden,.backdrop.hidden,.drawer.hidden,[aria-hidden="true"].overlay,[aria-hidden="true"].modal,[aria-hidden="true"].backdrop,[hidden]').forEach(function(el){
      el.style.pointerEvents='none';
    });
  }

  function boot(){
    document.body.classList.add('v349-client-nav-ready');
    document.documentElement.classList.add('v349-client-nav-ready');
    cleanOldNav();
    createBottomNav();
    unlockScroll();
    unblockHiddenOverlays();
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot);
  else boot();

  setTimeout(boot,700);
  setTimeout(boot,1800);
})();
