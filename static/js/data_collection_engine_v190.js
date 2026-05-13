
async function nemesisDataCollectionStatus(){
  const r = await fetch('/api/v190/data-collection/status');
  return await r.json();
}
async function nemesisRunDataCollection(){
  const r = await fetch('/api/v190/data-collection/run', {method:'POST'});
  return await r.json();
}
