
(function(){
  function add(){
    var sels=['.v313-main-actions','.client-tabs','.dashboard-tabs','.nav-tabs','.bottom-nav','.mobile-bottom-nav','.app-bottom-nav'];
    sels.forEach(function(sel){document.querySelectorAll(sel).forEach(function(c){if(c.querySelector('[data-v319-1x2]'))return;var a=document.createElement('a');a.href='/cliente/1x2';a.textContent='Combis 1X2';a.dataset.v319_1x2='1';a.className='v319-quick-injected';c.appendChild(a);});});
    var buttons=Array.from(document.querySelectorAll('a,button')).filter(function(el){return /partidos hoy|picks hoy|en directo|live/i.test(el.textContent||'');});
    if(buttons.length&&!document.querySelector('[data-v319-floating-1x2]')){var p=buttons[0].parentElement;if(p&&!p.querySelector('[data-v319-1x2]')){var l=document.createElement('a');l.href='/cliente/1x2';l.textContent='Combis 1X2';l.dataset.v319Floating1x2='1';l.className='v319-quick-injected';p.appendChild(l);}}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',add);else add();
})();
