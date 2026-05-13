(function(){
  const cards=document.querySelectorAll('.v160-card,.v160-panel');
  cards.forEach((card,i)=>{card.style.animationDelay=(i*45)+'ms';card.classList.add('v160-ready');});
})();
