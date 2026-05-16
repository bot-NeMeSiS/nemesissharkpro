async function loadCopilot(){
  const res = await fetch('/api/v322/shark-copilot');
  const data = await res.json();
  document.getElementById('subheadline').textContent = data.subheadline || '';
  document.getElementById('mode').textContent = data.copilot_mode || 'SHARK';
  document.getElementById('message').textContent = data.main_message || 'Copiloto activo.';
  const metrics = document.getElementById('metrics-grid');
  metrics.innerHTML = (data.context_cards||[]).map(c=>`<article class="metric"><span>${c.label}</span><strong>${c.value}${c.suffix||''}</strong></article>`).join('');
  const insights = document.getElementById('insights-grid');
  insights.innerHTML = (data.insights||[]).map(i=>`<article class="insight"><span>Insight</span><h3>${i.title}</h3><p>${i.text}</p></article>`).join('');
}
loadCopilot().catch(()=>{});
