// V193 APP FEEL ULTRA PREMIUM · microinteracciones en español, sin tocar datos reales
(function(){
  const prefersReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const reveal = () => {
    const nodes = document.querySelectorAll('.v193-reveal:not(.is-visible), .card:not(.v193-ready), .quick-card:not(.v193-ready), .pick-card:not(.v193-ready), .match-card:not(.v193-ready), .fixture-card:not(.v193-ready)');
    if (!('IntersectionObserver' in window) || prefersReduced) { nodes.forEach(n=>{n.classList.add('is-visible','v193-ready')}); return; }
    const io = new IntersectionObserver((entries)=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('is-visible','v193-ready');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px',threshold:.08});
    nodes.forEach(n=>io.observe(n));
  };
  const improveEmptyStates = () => {
    const badTexts = ['no hay feed real','estado vacío premium','no hay datos','sin datos'];
    document.querySelectorAll('body *').forEach(el=>{
      if(el.children.length || !el.textContent) return;
      const t = el.textContent.trim().toLowerCase();
      if(badTexts.some(x=>t.includes(x))){
        el.classList.add('v193-empty');
        el.innerHTML = '<strong>Aún no hay datos reales disponibles</strong><span>Cuando entren fixtures, señales o snapshots reales, este bloque se actualizará automáticamente. No mostramos datos inventados.</span>';
      }
    });
  };
  const tactile = () => {
    document.addEventListener('pointerdown', e=>{ const x=e.target.closest('button,.btn,a,.v193-btn'); if(x) x.classList.add('v193-pressing'); }, {passive:true});
    document.addEventListener('pointerup', ()=>document.querySelectorAll('.v193-pressing').forEach(x=>x.classList.remove('v193-pressing')), {passive:true});
  };
  const track = (event_type, payload={}) => {
    try{ fetch('/api/v193/app-feel/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_type,payload,page:location.pathname})}).catch(()=>{}); }catch(e){}
  };
  const boot = () => { reveal(); improveEmptyStates(); tactile(); track('vista_app_feel', {ruta: location.pathname}); };
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
