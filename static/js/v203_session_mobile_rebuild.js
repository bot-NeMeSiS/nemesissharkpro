// V203 SESSION FIX + MOBILE UX REBUILD PRO
(function(){
  function mark(){ document.documentElement.classList.add('v203-ready'); }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mark); else mark();
  window.v203GoBack=function(){ if(history.length>1) history.back(); };
  window.v203GoForward=function(){ history.forward(); };
})();
