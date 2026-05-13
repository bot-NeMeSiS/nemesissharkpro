(function(){
  const directInstall = document.getElementById('nemesis-pwa-banner-install');
  const mainInstall = document.getElementById('nemesis-pwa-install');
  if(directInstall && mainInstall){
    directInstall.addEventListener('click', function(){ mainInstall.click(); });
  }
  const focusPlans = document.querySelector('.v152-plans.v152-focus');
  if(focusPlans){ setTimeout(()=>focusPlans.scrollIntoView({behavior:'smooth', block:'start'}), 120); }
})();
