
async function nemesisSportsVisualMatches(limit=30){
  const r = await fetch(`/api/v185/visual/matches?limit=${limit}`);
  return await r.json();
}
async function nemesisTeamAsset(name){
  const r = await fetch(`/api/v185/visual/team?name=${encodeURIComponent(name)}`);
  return await r.json();
}
