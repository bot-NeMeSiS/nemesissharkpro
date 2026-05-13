(function(){
  const INSTALLED_KEY='nemesis_pwa_installed_v170';
  const DISMISSED_KEY='nemesis_pwa_dismissed_until_v170';
  let deferredPrompt=null;
  const isStandalone=()=> window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone===true || localStorage.getItem(INSTALLED_KEY)==='1';
  const dismissed=()=>{const until=parseInt(localStorage.getItem(DISMISSED_KEY)||'0',10);return until && Date.now()<until;};
  const markInstalled=()=>{localStorage.setItem(INSTALLED_KEY,'1');document.body.classList.add('v170-pwa-installed');document.querySelectorAll('[data-v170-install-card],.v170-smart-install-floating').forEach(e=>e.remove());};
  const show=()=>{
    if(isStandalone()) return markInstalled();
    if(dismissed()) return;
    document.querySelectorAll('[data-v170-install-card]').forEach(el=>el.classList.remove('is-hidden'));
    if(!document.querySelector('.v170-smart-install-floating')){
      const bar=document.createElement('div');bar.className='v170-smart-install-floating';
      bar.innerHTML='<div><strong>Instalar NeMeSiS</strong><small>App rápida para PC y móvil</small></div><button data-v170-install>Instalar</button><button class="v170-close" data-v170-install-close>×</button>';
      document.body.appendChild(bar);
    }
  };
  window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;show();});
  window.addEventListener('appinstalled',markInstalled);
  document.addEventListener('click',async e=>{
    const install=e.target.closest('[data-v170-install]');
    if(install){
      if(deferredPrompt){deferredPrompt.prompt();try{const choice=await deferredPrompt.userChoice;if(choice&&choice.outcome==='accepted') markInstalled();}catch(_){} deferredPrompt=null;}
      else { alert('En PC: usa el icono de instalar de Chrome/Edge en la barra. En móvil: menú del navegador → Añadir a pantalla de inicio.'); }
    }
    if(e.target.closest('[data-v170-install-close]')){localStorage.setItem(DISMISSED_KEY,String(Date.now()+1000*60*60*24*7));document.querySelectorAll('[data-v170-install-card],.v170-smart-install-floating').forEach(el=>el.remove());}
  });
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>{ if(isStandalone()) markInstalled(); else setTimeout(show,1200); }); else { if(isStandalone()) markInstalled(); else setTimeout(show,1200); }
})();
