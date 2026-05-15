
(function(){
  function batchOneGuard(){
    try{
      var navs = Array.from(document.querySelectorAll('.mobile-bottom-nav,.bottom-nav,.app-bottom-nav'));
      if(window.innerWidth > 900){
        navs.forEach(function(n){ n.style.display='none'; });
      } else if(navs.length > 1){
        navs.forEach(function(n, i){ if(i > 0) n.style.display='none'; });
      }
      document.documentElement.classList.add('v302-batch-one-ready');
    }catch(e){ console.warn('V302 guard skipped', e); }
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', batchOneGuard);
  else batchOneGuard();
})();
