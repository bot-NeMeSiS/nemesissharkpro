(function(){
  const $ = (id)=>document.getElementById(id);
  const txt = (id,v)=>{ const el=$(id); if(el) el.textContent = (v ?? '—'); };
  const meter = (id,pid,v)=>{ const pct=Math.max(0,Math.min(100,Number(v||0))); const el=$(id); if(el) el.style.width=pct+'%'; txt(pid,pct.toFixed(1)+'%'); };
  function providerLine(name,p){
    const ok = p && p.enabled && p.key;
    const cls = ok ? 'ok' : (p && p.enabled ? 'warn' : 'bad');
    return `<div class="v250-pill ${cls}"><b>${name}</b><br>Activo: ${p?.enabled?'sí':'no'} · Clave: ${p?.key?'sí':'no'} · Caché: ${p?.cache_minutes ?? p?.days_ahead ?? '—'}</div>`;
  }
  function render(data){
    const c=data.counts||{}, q=data.quality||{};
    txt('k-active',c.picks_active); txt('k-today',c.fixtures_today); txt('k-score',c.live_with_score); txt('k-minute',c.live_with_minute); txt('k-odds',c.with_odds); txt('k-cache',`${c.api_cache_valid||0}/${c.api_cache_rows||0}`);
    meter('m-score','p-score',q.score_coverage_pct); meter('m-minute','p-minute',q.minute_coverage_pct); meter('m-odds','p-odds',q.odds_coverage_pct); meter('m-source','p-source',q.real_source_pct);
    const p=data.providers||{}; $('v250-providers').innerHTML = providerLine('The Odds API',p.the_odds_api)+providerLine('TheSportsDB',p.thesportsdb)+providerLine('API-Football',p.api_football);
    const alerts=(data.alerts||[]); $('v250-alerts').innerHTML = alerts.length ? alerts.map(a=>`<div class="v250-pill ${a.level==='warning'?'warn':a.level==='error'?'bad':'ok'}">${a.text}</div>`).join('') : '<div class="v250-pill ok">Sin alertas críticas de datos.</div>';
    const recs=(data.recommendations||[]); $('v250-recommendations').innerHTML = recs.length ? recs.map(r=>`<div class="v250-pill">${r}</div>`).join('') : '<div class="v250-empty">Sin recomendaciones pendientes.</div>';
    const matches=(data.sample_matches||[]); $('v250-matches').innerHTML = matches.length ? matches.map(m=>`<div class="v250-match"><div><h3>${m.title||'Partido real guardado'}</h3><p>${m.league||'Liga sin etiqueta'} · ${m.kickoff_time||'hora pendiente'} · ${m.source||'fuente pendiente'}</p><p>Minuto: ${m.live_minute||'—'} · Cuota: ${m.odds_decimal||'—'} ${m.odds_bookmaker?('· '+m.odds_bookmaker):''}</p></div><div class="v250-score">${m.live_score||'— : —'}</div></div>`).join('') : '<div class="v250-empty">No hay partidos reales guardados todavía.</div>';
  }
  async function load(){
    try{ const r=await fetch('/api/v250/real-data-health/status',{cache:'no-store'}); render(await r.json()); }
    catch(e){ $('v250-alerts').innerHTML='<div class="v250-pill bad">No se pudo cargar el diagnóstico real.</div>'; }
  }
  async function refreshReal(){
    const btn=$('v250-refresh-real'); if(btn){btn.disabled=true;btn.textContent='Actualizando datos reales…'}
    try{ await fetch('/api/v250/real-data-health/refresh',{method:'POST'}); await load(); }
    finally{ if(btn){btn.disabled=false;btn.textContent='Refresh real controlado'} }
  }
  document.addEventListener('DOMContentLoaded',()=>{ load(); $('v250-refresh-ui')?.addEventListener('click',load); $('v250-refresh-real')?.addEventListener('click',refreshReal); });
})();
