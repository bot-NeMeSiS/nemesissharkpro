(function(){
  const INSTALLED_KEY='nemesis_pwa_installed_v179';
  const DISMISSED_KEY='nemesis_pwa_dismissed_until_v179';
  let deferredPrompt=null;
  const standalone=()=> window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone===true || localStorage.getItem(INSTALLED_KEY)==='1';
  const hideOld=()=>document.querySelectorAll('#nemesis-pwa-banner,[data-v170-install-card],.v170-smart-install-floating').forEach(e=>{ if(standalone()) e.remove(); });
  const markInstalled=()=>{localStorage.setItem(INSTALLED_KEY,'1');document.body.classList.add('v179-pwa-installed');hideOld();};
  const dismissed=()=>{const until=parseInt(localStorage.getItem(DISMISSED_KEY)||'0',10);return until && Date.now()<until;};
  const toast=(html)=>{ if(document.querySelector('.v179-install-toast')) return; const el=document.createElement('div'); el.className='v179-install-toast'; el.innerHTML='<button type="button" data-v179-toast-close>OK</button>'+html; document.body.appendChild(el); };
  const instructions=()=>toast('<b>Instalación manual</b><br>PC Chrome/Edge: busca el icono de instalar en la barra de direcciones o menú ⋮ → Guardar y compartir → Instalar página como aplicación.<br><br>Móvil: menú ⋮ → Añadir a pantalla de inicio / Instalar app. Si ya está instalada, este aviso desaparece solo.');
  const registerSW=()=>{ if('serviceWorker' in navigator) navigator.serviceWorker.register('/service-worker.js',{scope:'/'}).catch(()=>null); };
  window.addEventListener('beforeinstallprompt',(e)=>{ e.preventDefault(); deferredPrompt=e; document.body.classList.add('v179-pwa-installable'); });
  window.addEventListener('appinstalled',markInstalled);
  document.addEventListener('click',async(e)=>{
    if(e.target.closest('[data-v179-install],#nemesis-pwa-install,#nemesis-pwa-banner-install,[data-v170-install]')){
      e.preventDefault();
      if(standalone()) return markInstalled();
      if(deferredPrompt){ deferredPrompt.prompt(); try{ const c=await deferredPrompt.userChoice; if(c && c.outcome==='accepted') markInstalled(); }catch(_){} deferredPrompt=null; }
      else instructions();
    }
    if(e.target.closest('[data-v179-toast-close]')) e.target.closest('.v179-install-toast')?.remove();
    if(e.target.closest('#nemesis-pwa-close,[data-v170-install-close]')) localStorage.setItem(DISMISSED_KEY,String(Date.now()+1000*60*60*24*7));
  }, true);
  const init=()=>{registerSW(); if(standalone()) markInstalled(); else {hideOld(); if(!dismissed()) setTimeout(()=>document.body.classList.add('v179-pwa-ready'),900);} };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
