
async function nemesisMLStatus(){
  const r = await fetch('/api/v189/ml/status');
  return await r.json();
}
async function nemesisMLBuildFeatureStore(){
  const r = await fetch('/api/v189/ml/build-feature-store', {method:'POST'});
  return await r.json();
}
