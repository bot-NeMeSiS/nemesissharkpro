
(function(){
  function force1x2Visible(){
    var labels = ['Picks hoy','Partidos hoy','En directo','Live','Inicio'];
    var existing = document.querySelector('a[href="/cliente/1x2"], a[href="/cliente/combis"]');
    if(existing){
      existing.classList.add('v320-1x2-tab');
      existing.textContent = existing.textContent.trim() || 'Combis 1X2';
    }

    var containers = [];
    document.querySelectorAll('nav, header, .client-tabs, .dashboard-tabs, .nav-tabs, .bottom-nav, .mobile-bottom-nav, .app-bottom-nav, .v313-main-actions, .panel, .card').forEach(function(el){
      var t = (el.textContent || '').toLowerCase();
      if(t.includes('picks') || t.includes('partidos') || t.includes('directo') || t.includes('inicio')) containers.push(el);
    });

    containers.slice(0, 6).forEach(function(c){
      if(c.querySelector('[data-v320-1x2]')) return;
      var a = document.createElement('a');
      a.href = '/cliente/1x2';
      a.textContent = 'Combis 1X2';
      a.dataset.v320_1x2 = '1';
      a.className = 'v320-1x2-tab';
      c.appendChild(a);
    });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', force1x2Visible);
  else force1x2Visible();
})();
