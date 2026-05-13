
const NMS_LIVE_CACHE = new Map();
async function nemesisLiveLite(){
  const now = Date.now();
  const cached = NMS_LIVE_CACHE.get('lite');
  if(cached && now - cached.t < 25000) return cached.data;
  const r = await fetch('/api/v187/live-lite');
  const data = await r.json();
  NMS_LIVE_CACHE.set('lite', {t: now, data});
  return data;
}
async function nemesisWarmLiveCache(){
  const r = await fetch('/api/v187/speed/warm-cache', {method:'POST'});
  return await r.json();
}
