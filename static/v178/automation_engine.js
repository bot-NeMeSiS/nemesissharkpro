async function runJob(key){
  const r = await fetch(`/api/v178/automation/run/${key}`, {method:'POST'});
  const j = await r.json();
  alert(j.message || JSON.stringify(j));
  location.reload();
}
async function runDue(){
  const r = await fetch('/api/v178/automation/run-due', {method:'POST'});
  const j = await r.json();
  alert(`Ejecutados: ${j.ran || 0}`);
  location.reload();
}
