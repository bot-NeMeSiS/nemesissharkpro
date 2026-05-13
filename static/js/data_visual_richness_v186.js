
async function nemesisVisualComponents(){
  const r = await fetch('/api/v186/visual-components');
  return await r.json();
}
function nemesisRenderRing(value,color='#22d3ee'){
  return `<div class="nms-ring" style="--v:${value};--c:${color}"><span>${value}%</span></div>`;
}
