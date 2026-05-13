
async function nemesisAdvancedStats(){
  const r = await fetch('/api/v188/advanced-stats');
  return await r.json();
}
async function nemesisMLReadiness(){
  const r = await fetch('/api/v188/ml-readiness');
  return await r.json();
}
