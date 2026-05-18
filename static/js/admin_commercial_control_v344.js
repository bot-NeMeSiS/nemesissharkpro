
(function(){
function boot(){
  document.documentElement.classList.add('v344-admin-commercial-ready');
  document.body.classList.remove('no-scroll','modal-open','scroll-lock','lock-scroll');
  document.body.style.overflowY='auto';
  document.documentElement.style.overflowY='auto';
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
