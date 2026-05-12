(function(){
  const root = document.documentElement;
  root.classList.add('v165-ready');
  fetch('/api/v165/ui-health').then(r=>r.json()).then(data=>{
    root.dataset.v165Health = data.health_score || '0';
  }).catch(()=>{});
})();
