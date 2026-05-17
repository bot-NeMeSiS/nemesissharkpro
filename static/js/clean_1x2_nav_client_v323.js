
(function(){
  function textIs1x2(el){
    return /combis\s*1x2|1x2/i.test((el.textContent || '').trim()) &&
           (el.getAttribute('href') || '').includes('/cliente');
  }

  function removeOldDuplicates(){
    document.querySelectorAll('.v319-quick-injected,.v320-1x2-tab,.v321-force-1x2,[data-v319-1x2],[data-v320-1x2],[data-v321-1x2],[data-v319-floating-1x2],[data-v320-floating-1x2]').forEach(function(el){
      el.remove();
    });

    var links = Array.from(document.querySelectorAll('a')).filter(textIs1x2);
    links.forEach(function(el){ el.remove(); });
  }

  function findNavContainer(){
    var selectors = [
      '.nav-tabs',
      '.client-tabs',
      '.dashboard-tabs',
      'nav',
      'header',
      '.top-nav',
      '.app-nav',
      '.client-menu',
      '.menu-cliente'
    ];

    for(var i=0;i<selectors.length;i++){
      var nodes = Array.from(document.querySelectorAll(selectors[i]));
      for(var j=0;j<nodes.length;j++){
        var t = (nodes[j].textContent || '').toLowerCase();
        if(t.includes('inicio') || t.includes('picks') || t.includes('partidos') || t.includes('live') || t.includes('directo')){
          return nodes[j];
        }
      }
    }

    var buttons = Array.from(document.querySelectorAll('a,button')).filter(function(el){
      return /inicio|picks|partidos|live|directo/i.test(el.textContent || '');
    });
    return buttons.length ? buttons[0].parentElement : null;
  }

  function insertClean1x2(){
    removeOldDuplicates();

    if(document.querySelector('[data-v323-1x2-clean]')) return;

    var container = findNavContainer();
    if(!container) return;

    var a = document.createElement('a');
    a.href = '/cliente/1x2';
    a.textContent = 'Combis 1X2';
    a.dataset.v3231x2Clean = '1';
    a.className = 'v323-1x2-clean-link';

    container.appendChild(a);
  }

  function boot(){
    insertClean1x2();
    setTimeout(insertClean1x2, 350);
    setTimeout(insertClean1x2, 1200);
    document.documentElement.classList.add('v323-clean-1x2-ready');
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
