(function(){
  const root=document.querySelector('[data-v159-live]');
  if(!root) return;
  fetch('/api/v159/live-ecosystem').then(r=>r.json()).then(data=>{
    root.dataset.v159Ok = data && data.ok ? '1' : '0';
  }).catch(()=>{ root.dataset.v159Ok='0'; });
})();
