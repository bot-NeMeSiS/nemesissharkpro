async function loadV325(){
  const safe = (v,f)=>Array.isArray(v)?v:f;
  try{
    const res = await fetch('/api/v325/smart-match-flow',{cache:'no-store'});
    const data = await res.json();
    const flow = data.flow || data;
    const shark = data.shark || {};
    document.getElementById('subtitle').textContent = flow.subheadline || 'Experiencia cliente premium activa.';
    document.getElementById('score').textContent = flow.client_score || 95;
    document.getElementById('focusGrid').innerHTML = safe(flow.today_focus,[]).map(x=>`<article class="card"><span class="tag">${x.tone||'safe'}</span><strong>${x.value}</strong><p class="muted">${x.label}</p></article>`).join('');
    document.getElementById('flowSteps').innerHTML = safe(flow.flow_steps,[]).map(x=>`<article class="step"><span class="tag">${x.tone||'flow'}</span><h3>${x.title}</h3><p>${x.text}</p><strong>${x.action}</strong></article>`).join('');
    document.getElementById('actions').innerHTML = safe(flow.match_actions,[]).map(x=>`<article class="action"><span class="tag">${x.tag}</span><h3>${x.title}</h3><p>${x.text}</p></article>`).join('');
    document.getElementById('briefing').textContent = shark.briefing || 'SHARK listo para guiar el recorrido.';
    document.getElementById('insights').innerHTML = safe(shark.insights,[]).map(x=>`<li>${x}</li>`).join('');
  }catch(e){
    document.getElementById('subtitle').textContent='V325 activo en modo seguro.';
  }
}
loadV325();
