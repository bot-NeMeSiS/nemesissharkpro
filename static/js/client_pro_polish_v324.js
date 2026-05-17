
(function(){
  function polishClient(){
    try{
      document.documentElement.classList.add('v324-client-polish-ready');

      // Quita restos duplicados de inyecciones antiguas 1X2, manteniendo el link limpio V323.
      document.querySelectorAll('.v319-quick-injected,.v320-1x2-tab,.v321-force-1x2').forEach(function(el){
        el.remove();
      });

      // Si hay múltiples Combis 1X2, deja solo el primero visible.
      var oneX2 = Array.from(document.querySelectorAll('a')).filter(function(a){
        return /combis\s*1x2/i.test(a.textContent || '') && (a.getAttribute('href') || '').includes('/cliente');
      });
      oneX2.forEach(function(a, i){
        if(i === 0){
          a.classList.add('v323-1x2-clean-link');
          a.style.display = 'inline-flex';
        }else{
          a.remove();
        }
      });

      // Mejora tarjetas vacías o pequeñas sin romperlas.
      document.querySelectorAll('.card,.panel,.widget,.box').forEach(function(el){
        if((el.textContent || '').trim().length < 18){
          el.classList.add('empty-state');
        }
      });

      // Mantiene scroll desbloqueado después de navegación dinámica.
      document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
      document.documentElement.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
      document.body.style.overflowY = 'auto';
      document.documentElement.style.overflowY = 'auto';
    }catch(e){
      console.warn('V324 polish skipped', e);
    }
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', polishClient);
  else polishClient();
  setTimeout(polishClient, 700);
})();
