
(function(){
  function removeTechnicalNoise(){
    document.querySelectorAll('.debug,.debug-panel,.dev-note,.technical-note,.api-debug,.json-debug,[data-debug="true"],[data-dev="true"],.vapid-warning,.push-config-warning,.traceback,.werkzeug-debugger').forEach(function(el){
      el.remove();
    });
  }

  function cleanOldInjections(){
    document.querySelectorAll('.v319-quick-injected,.v320-1x2-tab,.v321-force-1x2,[data-v319-1x2],[data-v320-1x2],[data-v321-1x2],[data-v319-floating-1x2],[data-v320-floating-1x2]').forEach(function(el){
      el.remove();
    });

    // Dedupe excessive duplicated client links by visible text + href.
    var seen = {};
    Array.from(document.querySelectorAll('a')).forEach(function(a){
      var href = a.getAttribute('href') || '';
      var txt = (a.textContent || '').trim().toLowerCase().replace(/\s+/g,' ');
      if(!href || !txt) return;
      var interesting = /combis|1x2|membres|pro|elite|favoritos|match center|live command/.test(txt);
      if(!interesting) return;
      var key = href + '|' + txt;
      if(seen[key] && !a.closest('.v325-bottom-nav')){
        a.remove();
      }else{
        seen[key] = true;
      }
    });
  }

  function unlockScroll(){
    [document.documentElement, document.body].forEach(function(el){
      if(!el) return;
      el.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll','prevent-scroll','disable-scroll');
      el.style.overflowY = 'auto';
      el.style.overflowX = 'hidden';
      el.style.height = 'auto';
      el.style.position = 'static';
    });
  }

  function boot(){
    document.documentElement.classList.add('v345-product-hardened');
    removeTechnicalNoise();
    cleanOldInjections();
    unlockScroll();
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  setTimeout(boot, 800);
  setTimeout(boot, 1800);
})();
