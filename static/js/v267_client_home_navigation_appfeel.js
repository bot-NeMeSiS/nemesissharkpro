// V267 · client navigation active state + duplicate nav guard
(function(){
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  const aliases = {
    '/cliente/pro':'/clientes', '/cliente':'/clientes', '/match-center-unified':'/partidos',
    '/fixtures/today-pro':'/partidos', '/live-command-center':'/partidos',
    '/smart-value-detection':'/picks', '/value-edge-engine':'/picks', '/bankroll-edge':'/clientes'
  };
  const normalized = aliases[path] || path;
  document.querySelectorAll('.nav a,.client-app-nav-v308 a').forEach(a=>{
    try{
      const href = (new URL(a.getAttribute('href'), location.origin)).pathname.replace(/\/$/, '') || '/';
      if(href === normalized || (href !== '/' && normalized.startsWith(href + '/'))) a.classList.add('is-active');
    }catch(e){}
  });
  // Avoid two install banners fighting visually.
  const legacy = document.getElementById('nemesis-pwa-banner');
  const modern = document.querySelector('[data-v170-install-card]');
  if(legacy && modern) legacy.setAttribute('data-v267-secondary-banner','true');
})();
