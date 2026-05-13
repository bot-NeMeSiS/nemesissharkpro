// V194 · Flechas de navegación sin recargar lógica pesada
(function(){
  function ready(fn){ if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', fn); else fn(); }
  ready(function(){
    var back=document.querySelector('[data-v194-back]');
    var forward=document.querySelector('[data-v194-forward]');
    if(back){ back.addEventListener('click', function(){ if(window.history.length>1){ window.history.back(); } else { window.location.href='/clientes'; } }); }
    if(forward){ forward.addEventListener('click', function(){ window.history.forward(); }); }
  });
})();
