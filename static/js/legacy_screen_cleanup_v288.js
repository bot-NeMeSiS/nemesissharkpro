
(function(){
  function v288Guard(){
    try{
      var navs = Array.from(document.querySelectorAll('.mobile-bottom-nav,.bottom-nav,.app-bottom-nav'));
      if(window.innerWidth > 900){
        navs.forEach(function(n){ n.style.display='none'; });
      } else if(navs.length > 1){
        navs.forEach(function(n, i){ if(i > 0) n.style.display='none'; });
      }

      document.querySelectorAll('a[href="/cliente/home-pro"],a[href="/cliente/smart-home"],a[href="/client-action-center"]').forEach(function(a){
        if(!a.dataset.v288Ready){
          a.dataset.v288Ready = "1";
          a.setAttribute('aria-label', a.textContent.trim() || 'Acceso cliente');
        }
      });
    }catch(e){
      console.warn('V288 consistency guard skipped', e);
    }
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', v288Guard);
  }else{
    v288Guard();
  }
})();
