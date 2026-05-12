
async function nemesisPushStatus(){
  const r = await fetch('/api/v182/push/status');
  return await r.json();
}
