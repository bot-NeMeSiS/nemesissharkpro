
(function(){
  const cards=[...document.querySelectorAll('.v176-card,.v176-signal,.v176-match')];
  cards.forEach((el,i)=>{el.style.opacity='0';el.style.transform='translateY(10px)';setTimeout(()=>{el.style.transition='opacity .35s ease, transform .35s ease';el.style.opacity='1';el.style.transform='translateY(0)'},60+i*22)});
})();
