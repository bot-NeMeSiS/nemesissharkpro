(function(){
  document.querySelectorAll('.quick button').forEach(function(btn){
    btn.addEventListener('click', function(){
      btn.textContent = 'SHARK analiza solo datos reales';
    });
  });
})();
