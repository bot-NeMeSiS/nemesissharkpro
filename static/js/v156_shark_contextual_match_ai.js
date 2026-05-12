(function(){
  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded',fn); }
  ready(function(){
    var panel=document.querySelector('.v156-ai[data-match-id]');
    if(!panel) return;
    var matchId=panel.getAttribute('data-match-id');
    var answer=document.getElementById('v156-answer');
    panel.querySelectorAll('[data-q]').forEach(function(btn){
      btn.addEventListener('click',function(){
        var q=btn.getAttribute('data-q')||'resumen';
        if(answer){ answer.className='v156-answer loading'; answer.textContent='SHARK está leyendo el contexto real del partido...'; }
        fetch('/api/v156/shark-context?match_id='+encodeURIComponent(matchId)+'&q='+encodeURIComponent(q),{headers:{'Accept':'application/json'}})
          .then(function(r){return r.json();})
          .then(function(data){
            if(answer){ answer.className='v156-answer ok'; answer.textContent=data.answer || data.message || 'Sin lectura disponible ahora mismo.'; }
          })
          .catch(function(){
            if(answer){ answer.className='v156-answer'; answer.textContent='No se pudo consultar SHARK ahora mismo. El partido sigue disponible con datos reales.'; }
          });
      });
    });
  });
})();
