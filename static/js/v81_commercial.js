
(function(){
  function event(type, title) {
    try {
      const p = new URLSearchParams({event_type:type, source:"PWA", title:title || document.title});
      fetch("/api/commercial/event?" + p.toString(), {keepalive:true}).catch(function(){});
    } catch(e) {}
  }
  window.NSPCommercialEvent = event;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function(){ event("PAGE_VIEW", document.title); });
  } else {
    event("PAGE_VIEW", document.title);
  }
})();
