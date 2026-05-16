async function loadV324(){
  const root=document.getElementById('v324-content');
  try{
    const res=await fetch('/api/v324/live-performance', {headers:{'Accept':'application/json'}});
    const data=await res.json();
    const focus=(data.focus||[]).map(x=>`<div class="item"><span class="badge">${x.label}</span><div class="metric">${x.value}</div><p>${x.detail}</p></div>`).join('');
    const actions=(data.performance_actions||[]).map(x=>`<div class="item">${x}</div>`).join('');
    const impact=(data.client_impact||[]).map(x=>`<div class="item"><strong>${x.title}</strong><p>${x.text}</p></div>`).join('');
    root.innerHTML=`
      <article class="v324-card pulse"><span class="badge">Estado</span><div class="metric">${data.score}/100</div><p>${data.status}</p></article>
      <article class="v324-card wide"><span class="badge">Foco cliente</span><div class="list">${focus}</div></article>
      <article class="v324-card wide"><span class="badge">Acciones de rendimiento</span><div class="list">${actions}</div></article>
      <article class="v324-card"><span class="badge">API extra</span><div class="metric">0</div><p>Esta capa no consume cuotas al abrir.</p></article>
      <article class="v324-card full"><span class="badge">Impacto premium</span><div class="list">${impact}</div></article>`;
  }catch(e){root.innerHTML='<article class="v324-card full"><h2>Modo seguro</h2><p>No se pudo cargar la API V324, pero la app sigue funcionando.</p></article>';}
}
loadV324();
