(function(){
  const health = document.querySelector('.v97-health span');
  const ring = document.querySelector('.v97-health');
  if(health && ring){ ring.style.setProperty('--v97-score', health.textContent.trim()); }
})();
