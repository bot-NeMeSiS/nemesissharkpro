(function(){
  const root=document.querySelector('[data-telegram-live]');
  if(!root) return;
  async function refresh(){
    try{
      const r=await fetch('/api/v162/telegram-live',{headers:{'Accept':'application/json'}});
      const data=await r.json();
      root.dataset.liveScore=data.live_score||0;
    }catch(e){root.dataset.liveScore='offline';}
  }
  refresh();
  setInterval(refresh,60000);
})();
