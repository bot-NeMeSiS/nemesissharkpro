
(function(){
function injectNormalizerStrip(){
  if(document.querySelector('.v347-data-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;

  var strip=document.createElement('section');
  strip.className='v347-data-strip';
  strip.innerHTML='<div><strong>🛡️ Live Normalizer & Crests</strong><small>Equipos, marcador, minuto, escudos y 1X2 con formato único.</small></div><a href="/cliente/live-normalizer">Revisar normalizador</a>';
  var ref=document.querySelector('.v346-data-strip') || document.querySelector('.v345-shell') || target.firstChild;
  if(ref && ref.parentNode){ref.parentNode.insertBefore(strip,ref.nextSibling);}else{target.insertBefore(strip,target.firstChild);}
}

function fixBrokenCrests(){
  document.querySelectorAll('img').forEach(function(img){
    var src=(img.getAttribute('src')||'').trim();
    var alt=(img.getAttribute('alt')||'Equipo').trim();
    if(!src || src === '#' || src.toLowerCase().includes('undefined') || src.toLowerCase().includes('null')){
      var span=document.createElement('span');
      span.className='team-crest-fallback';
      span.style.width=(img.width||34)+'px';
      span.style.height=(img.height||34)+'px';
      span.textContent=(alt.split(/\s+/).slice(0,2).map(function(x){return x[0]||''}).join('')||'FC').toUpperCase();
      img.replaceWith(span);
    }else{
      img.addEventListener('error',function(){
        var fb=document.createElement('span');
        fb.className='team-crest-fallback';
        fb.style.width=(img.width||34)+'px';
        fb.style.height=(img.height||34)+'px';
        fb.textContent=(alt.split(/\s+/).slice(0,2).map(function(x){return x[0]||''}).join('')||'FC').toUpperCase();
        img.replaceWith(fb);
      },{once:true});
    }
  });
}

function boot(){
  document.documentElement.classList.add('v347-live-normalizer-ready');
  injectNormalizerStrip();
  fixBrokenCrests();
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setTimeout(boot,900);
})();
