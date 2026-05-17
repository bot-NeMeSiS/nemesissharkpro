
(function(){
function unlock(){
 try{
  [document.documentElement,document.body].forEach(function(el){
   if(!el)return;
   el.style.overflowY='auto';el.style.overflowX='hidden';el.style.height='auto';el.style.minHeight='100%';el.style.position='static';
   el.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll','prevent-scroll','disable-scroll');
  });
  document.querySelectorAll('.no-scroll,.modal-open,.scroll-lock,.lock-scroll,.prevent-scroll,.disable-scroll').forEach(function(el){
   if(el!==document.body&&el!==document.documentElement)el.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll','prevent-scroll','disable-scroll');
  });
  document.querySelectorAll('main,.app,.page,.container,.content,.dashboard,.client-dashboard,.cliente-dashboard,.client-page,.cliente-page,.layout,.wrapper').forEach(function(el){
   el.style.overflow='visible';el.style.maxHeight='none';el.style.height='auto';
  });
  document.documentElement.classList.add('v322-scroll-fixed');
 }catch(e){}
}
function boot(){unlock();setTimeout(unlock,250);setTimeout(unlock,1200);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
