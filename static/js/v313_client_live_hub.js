async function loadV313(){
  const focus = document.getElementById('v313Focus');
  const cards = document.getElementById('v313Cards');
  const actions = document.getElementById('v313Actions');
  const matches = document.getElementById('v313Matches');
  const headline = document.getElementById('v313Headline');
  const dataState = document.getElementById('v313DataState');
  try{
    const res = await fetch('/api/v313/client-live-hub', {headers:{'Accept':'application/json'}});
    const data = await res.json();
    const f = data.focus || {};
    focus.innerHTML = `<small>${esc(f.label||'FOCO')}</small><strong>${esc(f.title||'Sin foco')}</strong><span>${esc(f.subtitle||'')}</span><div class="v313-ring"><b>${Number(f.momentum||0)}/99</b></div><em>${esc(f.action||'Esperar señal')}</em>`;
    headline.textContent = data.headline || 'Smart Live Hub activo.';
    cards.innerHTML = (data.home_cards||[]).map(c=>`<article><strong>${esc(c.label)}</strong><span>${esc(c.value)}</span><small>${esc(c.hint)}</small></article>`).join('');
    actions.innerHTML = (data.actions||[]).map(a=>`<article><b>${esc(a.type)}</b><div><strong>${esc(a.title)}</strong><span>${esc(a.text)}</span></div></article>`).join('');
    const ds = data.data_state || {};
    dataState.innerHTML = `<strong>${esc(ds.level||'WATCH')}</strong><span>${esc(ds.text||'Estado seguro activo.')}</span>`;
    const list = data.match_center || [];
    matches.innerHTML = list.length ? list.map(renderMatchV313).join('') : '<div class="v313-empty">Todavía no hay partidos reales cacheados. Esta pantalla queda lista sin gastar API.</div>';
    requestAnimationFrame(()=>document.querySelectorAll('.v313-bar i').forEach(el=>el.style.width=el.dataset.w+'%'));
  }catch(e){
    headline.textContent = 'No se pudo cargar el Smart Live Hub.';
    matches.innerHTML = '<div class="v313-empty">Error seguro: esta capa no rompe la app.</div>';
  }
}
function renderMatchV313(m){
  const mom = Math.max(0, Math.min(99, Number(m.momentum||0)));
  const cls = (m.trigger||'watch').toLowerCase().replace(/\s+/g,'-');
  return `<article class="v313-match ${cls}">
    <div class="v313-match-top"><span>${esc(m.trigger||'WATCH')}</span><b>${esc(m.decision||'Observar')}</b></div>
    <h3>${esc(m.title||'Partido')}</h3>
    <p>${esc(m.league||'Liga')} · ${esc(m.status||'PROGRAMADO')} ${m.minute?'· '+esc(m.minute):''} ${m.scoreline?'· '+esc(m.scoreline):''}</p>
    <div class="v313-bar"><i data-w="${mom}"></i></div>
    <div class="v313-row"><strong>Momentum</strong><span>${mom}/99</span></div>
    <div class="v313-row"><strong>Pick</strong><span>${esc(m.pick||'Sin pick visible')}</span></div>
    <div class="v313-row"><strong>Cuota</strong><span>${esc(m.odds||'--')}</span></div>
    <div class="v313-why">${esc(m.why||'Señal generada por motor live.')}</div>
    <div class="v313-next">${esc(m.action||'Guardar en seguimiento.')}</div>
  </article>`;
}
function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
document.addEventListener('DOMContentLoaded', loadV313);
