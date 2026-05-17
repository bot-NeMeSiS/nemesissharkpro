
(function(){
  function hideVapidWarnings(){
    var selectors = ['.vapid-warning','.vapid-alert','.push-warning','.push-config-warning','[data-vapid-warning="true"]'];
    selectors.forEach(function(sel){
      document.querySelectorAll(sel).forEach(function(el){ el.style.display = 'none'; });
    });
    document.body.classList.add('v314-live-reliability-ready');
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', hideVapidWarnings);
  else hideVapidWarnings();
})();
