(function(){
  function ready(fn){document.readyState==='loading'?document.addEventListener('DOMContentLoaded',fn):fn();}
  ready(function(){
    document.querySelectorAll('[data-v158-fav]').forEach(function(btn){
      btn.addEventListener('click',async function(){
        const id=btn.getAttribute('data-v158-fav');
        btn.classList.toggle('on');
        btn.textContent=btn.classList.contains('on')?'★ Favorito':'☆ Favorito';
        try{await fetch('/api/v150/favorites/toggle',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({match_id:id})});}catch(e){}
      });
    });
    const ribbon=document.querySelector('[data-v158-refresh]');
    if(ribbon){
      setInterval(function(){
        const t=ribbon.querySelector('span:last-child');
        if(t){t.textContent='Actualizado · '+new Date().toLocaleTimeString('es-ES',{hour:'2-digit',minute:'2-digit'});}
      },30000);
    }
  });
})();
