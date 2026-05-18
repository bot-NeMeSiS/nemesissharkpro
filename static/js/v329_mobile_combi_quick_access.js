// NeMeSiS SHARK PRO · V329 UPDATE PACK · no toca app.py
(function(){
  function createBottomNav(){
    if(document.querySelector('.shark-v329-bottom-nav')) return;
    const nav=document.createElement('nav');
    nav.className='shark-v329-bottom-nav';
    nav.innerHTML='<a href="/cliente">Inicio</a><a href="/cliente/live">Live</a><a href="/cliente/combi-inteligente" class="active">Combi 1X2</a><a href="/cliente/shark-copilot">SHARK</a>';
    document.body.appendChild(nav);
  }
  function enhanceCombiButtons(){
    const labels=['combi','combinada','1x2','shark combi'];
    document.querySelectorAll('a,button').forEach(function(el){
      const text=(el.textContent||'').toLowerCase();
      if(labels.some(function(label){return text.includes(label)})){el.classList.add('shark-v329-btn');}
    });
  }
  document.addEventListener('DOMContentLoaded',function(){createBottomNav();enhanceCombiButtons();});
})();
