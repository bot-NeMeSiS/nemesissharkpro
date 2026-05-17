
(function(){
  function injectTrustStrip(){
    if(document.querySelector('.v328-trust-strip')) return;
    var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
    if(!target) return;
    var strip=document.createElement('section');
    strip.className='v328-trust-strip';
    strip.innerHTML=[
      '<div class="v328-trust-item real"><strong>✅ Datos reales</strong><small>Si falta información, la app no inventa señales.</small></div>',
      '<div class="v328-trust-item wait"><strong>⏳ Esperar también cuenta</strong><small>LOW DATA significa que es mejor no forzar decisión.</small></div>',
      '<div class="v328-trust-item risk"><strong>🎯 Decide simple</strong><small>Mira partido, revisa 1X2, pregunta a SHARK.</small></div>'
    ].join('');
    var ref=document.querySelector('.v327-home-strip') || target.firstChild;
    if(ref && ref.parentNode) ref.parentNode.insertBefore(strip, ref.nextSibling);
    else target.insertBefore(strip,target.firstChild);
  }
  function addHints(){
    document.querySelectorAll('.low-data,.empty-state,.no-data').forEach(function(el){
      if(el.querySelector('.v328-action-hint')) return;
      var hint=document.createElement('span');
      hint.className='v328-action-hint';
      hint.textContent='Esperar datos reales';
      el.appendChild(hint);
    });
  }
  function boot(){
    document.documentElement.classList.add('v328-trust-clarity-ready');
    injectTrustStrip();
    addHints();
    document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
    document.body.style.overflowY='auto';
    document.documentElement.style.overflowY='auto';
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
  setTimeout(boot,800);
})();
