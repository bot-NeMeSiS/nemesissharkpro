async function loadV312LiveEngine(){
  const summary = document.getElementById('v312Summary');
  const matchesBox = document.getElementById('v312Matches');
  const timelineBox = document.getElementById('v312Timeline');
  const headline = document.getElementById('v312Headline');
  try{
    const res = await fetch('/api/v312/live-engine/status', {headers:{'Accept':'application/json'}});
    const data = await res.json();
    const s = data.summary || {};
    const cards = summary.querySelectorAll('article span');
    cards[0].textContent = (s.momentum_avg ?? 0) + '/99';
    cards[1].textContent = s.hot_count ?? 0;
    cards[2].textContent = s.watch_count ?? 0;
    cards[3].textContent = s.data_health || 'LOW DATA';
    headline.textContent = s.headline || 'Live Engine activo.';
    const matches = data.matches || [];
    matchesBox.innerHTML = matches.length ? matches.map(renderV312Match).join('') : '<div class="v312-empty">No hay partidos reales cacheados todavía. El motor queda preparado sin gastar API.</div>';
    requestAnimationFrame(()=>document.querySelectorAll('.v312-momentum i').forEach(el=>el.style.width=el.dataset.w+'%'));
    const events = data.timeline || [];
    timelineBox.innerHTML = events.map(ev=>`<div class="v312-event"><strong>${escapeV312(ev.label||'WATCH')}</strong><span>${escapeV312(ev.text||'Seguimiento')}</span></div>`).join('');
  }catch(e){
    headline.textContent = 'No se pudo leer el Live Engine ahora mismo.';
    matchesBox.innerHTML = '<div class="v312-empty">Error seguro: la pantalla no rompe la app.</div>';
  }
}
function renderV312Match(m){
  const cls = m.trigger === 'HOT' ? 'hot' : (m.data_health === 'LOW DATA' ? 'low' : 'watch');
  const momentum = Math.max(0, Math.min(99, Number(m.momentum || 0)));
  return `<article class="v312-card ${cls}">
    <div class="v312-top"><span class="v312-tag">${escapeV312(m.trigger || 'WATCH')}</span><span class="v312-meta">${momentum}/99</span></div>
    <div class="v312-title">${escapeV312(m.title || 'Partido')}</div>
    <div class="v312-meta">${escapeV312(m.league || 'Liga')} · ${escapeV312(m.live_status || 'PROGRAMADO')} ${m.live_minute ? '· '+escapeV312(m.live_minute) : ''} ${m.live_score ? '· '+escapeV312(m.live_score) : ''}</div>
    <div class="v312-momentum"><i data-w="${momentum}"></i></div>
    <div class="v312-action">${escapeV312(m.client_action || 'Guardar en seguimiento')}</div>
  </article>`;
}
function escapeV312(v){return String(v ?? '').replace(/[&<>'"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
document.addEventListener('DOMContentLoaded', loadV312LiveEngine);
