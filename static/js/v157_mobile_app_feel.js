// V157_MOBILE_APP_FEEL_AND_LIVE_POLISH_PRO
(function(){
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function qs(s,root=document){return root.querySelector(s)}
  function qsa(s,root=document){return Array.from(root.querySelectorAll(s))}
  function markActiveNav(){
    const path = location.pathname.replace(/\/$/,'') || '/';
    qsa('.bottom-mobile-nav-v283 a,.client-app-nav-v308 a,.v151-bottom a,.v155-topbar a').forEach(a=>{
      try{ const href=(new URL(a.href)).pathname.replace(/\/$/,'')||'/'; if(href===path || (path.includes('partido')&&href.includes('partidos'))) a.classList.add('v157-active'); }catch(e){}
    });
  }
  function injectLiveStrip(){
    if(qs('[data-v157-live-strip]')) return;
    const targets=[qs('.v151-main'),qs('.v155-shell'),qs('.container')].filter(Boolean);
    const target=targets[0]; if(!target) return;
    const el=document.createElement('div'); el.className='v157-live-strip'; el.setAttribute('data-v157-live-strip',''); el.innerHTML='<b><i class="v157-live-dot off"></i>SHARK Live</b><span>Preparando lectura real...</span>';
    target.insertBefore(el,target.children[1]||target.firstChild);
  }
  async function refreshLiveStrip(){
    const el=qs('[data-v157-live-strip]'); if(!el) return;
    try{
      const res=await fetch('/api/v157/app-feel',{headers:{'Accept':'application/json'}});
      const data=await res.json();
      const live=Number(data.live_count||0); const signals=Number(data.signal_count||0);
      el.innerHTML='<b><i class="v157-live-dot '+(live?'':'off')+'"></i>SHARK Live</b><span>'+live+' en directo · '+signals+' señales reales · PWA '+(data.pwa||'ready')+'</span>';
    }catch(e){ el.innerHTML='<b><i class="v157-live-dot off"></i>SHARK Live</b><span>Real Core sin respuesta ahora mismo</span>'; }
  }
  function enhanceClicks(){
    if(reduce) return;
    qsa('a,button').forEach(el=>{
      el.addEventListener('pointerdown',()=>el.classList.add('v157-tap'),{passive:true});
      ['pointerup','pointercancel','mouseleave'].forEach(ev=>el.addEventListener(ev,()=>el.classList.remove('v157-tap'),{passive:true}));
    });
  }
  document.addEventListener('DOMContentLoaded',()=>{markActiveNav();injectLiveStrip();refreshLiveStrip();enhanceClicks();setInterval(refreshLiveStrip,45000);});
})();
