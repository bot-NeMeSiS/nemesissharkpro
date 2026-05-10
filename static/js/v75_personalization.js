
(function(){
  function uid(){ return window.NSP_USER_ID || localStorage.getItem("nsp_user_id") || "anonymous"; }
  try {
    fetch("/api/personalization/refresh?user_id=" + encodeURIComponent(uid()), {keepalive:true}).catch(function(){});
  } catch(e){}
})();
