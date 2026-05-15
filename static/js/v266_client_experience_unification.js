
// V266 · CLIENT EXPERIENCE UNIFICATION PRO
(function(){
  const path = location.pathname || '/';
  const clientHints = ['/cliente','/clientes','/picks','/partidos','/fixtures','/live','/match','/alertas','/favoritos','/clasificaciones','/shark-ai','/smart-value','/match-priority','/real-match','/hot-match','/live-data','/real-alert'];
  if (clientHints.some(p => path.startsWith(p))) document.body.classList.add('v266-client-unified');
  document.body.classList.add('v266-app-shell');
  // Marca links activos de forma uniforme.
  document.querySelectorAll('a[href]').forEach(a=>{
    try{ const u=new URL(a.getAttribute('href'), location.origin); if(u.pathname===path) a.classList.add('is-active','active'); }catch(e){}
  });
  // Limpia banners PWA duplicados antiguos si aparece el nuevo de V170.
  const banners=[...document.querySelectorAll('#nemesis-pwa-banner,[data-v170-install-card]')];
  if(banners.length>1){ banners.slice(1).forEach(b=>{ if(b.id==='nemesis-pwa-banner') b.remove(); }); }
})();
