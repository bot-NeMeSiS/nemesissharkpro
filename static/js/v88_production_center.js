
(function(){
  function classifyStatuses(){
    document.querySelectorAll("[data-v88-status]").forEach(function(el){
      var value = (el.getAttribute("data-v88-status") || "").toUpperCase();
      if (value === "OK" || value.includes("FUERTE")) el.classList.add("ok");
      else if (value.includes("MISSING") || value.includes("RIESGO")) el.classList.add("bad");
      else el.classList.add("warn");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", classifyStatuses);
  } else {
    classifyStatuses();
  }
})();
