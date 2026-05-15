(function(){
  const $=id=>document.getElementById(id);
  function esc(s){return String(s||'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
  function pct(v){v=Number(v||0);return Math.max(0,Math.min(100,v));}
  function meter(label,value){return `<div class="meter"><div class="meter-top"><span>${label}</span><b>${pct(value)}%</b></div><div class="bar"><i style="width:${pct(value)}%"></i></div></div>`}
  function crest(url,name){return url?`<img class="crest" src="${esc(url)}" alt="${esc(name)}">`:`<span class="crest no-crest">—</span>`}
  function render(data){
    const s=data.summary||{}; $('k-total').textContent=s.total??'—'; $('k-complete').textContent=s.complete??'—'; $('k-attention').textContent=s.needs_attention??'—'; $('k-crests').textContent=s.with_crest_pair??'—';
    const c=data.coverage||{};
    $('coverage').innerHTML=[meter('Hora real',c.kickoff_time_pct),meter('Marcador',c.live_score_pct),meter('Minuto',c.live_minute_pct),meter('Cuotas',c.odds_pct),meter('Fuente real',c.real_source_pct),meter('ID externo',c.external_event_id_pct)].join('');
    const rows=data.matches||[];
    $('matches').innerHTML=rows.length?rows.map(m=>{
      const missing=(m.missing||[]).map(x=>`<span class="chip bad">Falta ${esc(x)}</span>`).join('') || '<span class="chip ok">Completo</span>';
      return `<article class="v251-match"><div><div class="teams">${crest(m.home_logo,m.home)}<span>${esc(m.home||m.title)}</span><span>vs</span><span>${esc(m.away||'—')}</span>${crest(m.away_logo,m.away)}</div><div class="sub">${esc(m.league)} · ${esc(m.sport)} · ${esc(m.kickoff_time||'hora pendiente')}</div></div><div class="live"><div>${esc(m.live_status||'PROGRAMADO')}</div><div class="score">${esc(m.live_score||'— : —')} ${esc(m.live_minute||'')}</div><div class="sub">${esc(m.source||'fuente pendiente')}</div></div><div class="chips"><span class="chip">Cuota ${esc(m.odds||'—')}</span><span class="chip">${esc(m.bookmaker||'bookmaker pendiente')}</span><span class="chip">${esc(m.external_event_id?'ID real':'ID pendiente')}</span>${missing}</div></article>`;
    }).join(''):'<div class="v251-empty">No hay partidos reales guardados ahora mismo. Ejecuta refresh real desde admin o revisa proveedores.</div>';
  }
  async function load(){
    try{ const r=await fetch('/api/v251/live-coverage-matrix/status?limit=100',{cache:'no-store'}); render(await r.json()); }
    catch(e){ $('matches').innerHTML='<div class="v251-empty">No se pudo cargar la matriz real.</div>'; }
  }
  document.addEventListener('DOMContentLoaded',()=>{ const b=$('reload'); if(b)b.onclick=load; load(); });
})();
