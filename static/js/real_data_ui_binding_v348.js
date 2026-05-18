
(function(){
function crest(initials, url){
  if(url){
    return '<span class="v348-crest"><img src="'+url+'" alt="'+initials+'"></span>';
  }
  return '<span class="v348-crest">'+(initials||'FC')+'</span>';
}
function matchCard(m){
  var h=m.home||'Local', a=m.away||'Visitante';
  var hi=(m.crests&&m.crests.home&&m.crests.home.initials)||h.split(/\s+/).slice(0,2).map(x=>x[0]||'').join('').toUpperCase();
  var ai=(m.crests&&m.crests.away&&m.crests.away.initials)||a.split(/\s+/).slice(0,2).map(x=>x[0]||'').join('').toUpperCase();
  var hu=(m.crests&&m.crests.home&&m.crests.home.url)||null;
  var au=(m.crests&&m.crests.away&&m.crests.away.url)||null;
  var score=(m.score&&m.score.text)||'vs';
  var minute=(m.minute&&m.minute.text)||'Pre';
  var league=m.league||'Competición';
  var o=m.odds_1x2||{};
  return '<article class="v348-match-card">'+
    '<div class="v348-match-top"><span class="v348-league">'+league+'</span><span class="v348-minute">'+minute+'</span></div>'+
    '<div class="v348-teams">'+crest(hi,hu)+'<div class="v348-team-name">'+h+'</div><div class="v348-score">'+score+'</div></div>'+
    '<div class="v348-teams">'+crest(ai,au)+'<div class="v348-team-name">'+a+'</div><div></div></div>'+
    '<div class="v348-odds"><div class="v348-odd"><strong>1</strong><small>'+(o["1"]||'--')+'</small></div><div class="v348-odd"><strong>X</strong><small>'+(o["X"]||'--')+'</small></div><div class="v348-odd"><strong>2</strong><small>'+(o["2"]||'--')+'</small></div></div>'+
    '<div class="v348-actions"><a class="gold" href="/cliente/1x2">1X2</a><a href="/cliente/match-center-premium">Detalle</a></div>'+
  '</article>';
}
async function injectBinding(){
  if(document.querySelector('.v348-ui-strip')) return;
  var target=document.querySelector('.client-dashboard,.cliente-dashboard,.dashboard,.client-page,.cliente-page,main,.content');
  if(!target) return;
  var box=document.createElement('section');
  box.className='v348-ui-strip';
  box.innerHTML='<div class="v348-ui-head"><h2>Real Data UI Binding</h2><span class="v348-badge">NORMALIZED UI</span></div><div class="v348-low-data">Cargando muestra normalizada real...</div>';
  var ref=document.querySelector('.v347-data-strip') || document.querySelector('.v346-data-strip') || target.firstChild;
  if(ref && ref.parentNode){ref.parentNode.insertBefore(box,ref.nextSibling);}else{target.insertBefore(box,target.firstChild);}
  try{
    var res=await fetch('/api/live/normalizer/sample-v347?limit=3',{cache:'no-store'});
    var data=await res.json();
    var matches=(data&&data.matches)||[];
    if(matches.length){
      box.innerHTML='<div class="v348-ui-head"><h2>Real Data UI Binding</h2><span class="v348-badge">NORMALIZED UI</span></div><div class="v348-match-grid">'+matches.map(matchCard).join('')+'</div>';
    }else{
      box.innerHTML='<div class="v348-ui-head"><h2>Real Data UI Binding</h2><span class="v348-badge">LOW DATA</span></div><div class="v348-low-data">Esperando partidos reales normalizados. Revisa /api/live/normalizer/sample-v347.</div>';
    }
  }catch(e){
    box.innerHTML='<div class="v348-ui-head"><h2>Real Data UI Binding</h2><span class="v348-badge">LOW DATA</span></div><div class="v348-low-data">No se pudo cargar la muestra normalizada. El fallback visual está activo.</div>';
  }
}
function boot(){
  document.documentElement.classList.add('v348-real-data-ui-ready');
  injectBinding();
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setTimeout(boot,900);
})();
