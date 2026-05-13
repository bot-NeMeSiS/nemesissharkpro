
(function(){
  function refreshQualityBadges(){
    document.querySelectorAll("[data-v86-score]").forEach(function(el){
      var score = Number(el.getAttribute("data-v86-score") || "0");
      if (score >= 75) el.classList.add("ok");
      else if (score >= 55) el.classList.add("warn");
      else el.classList.add("bad");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", refreshQualityBadges);
  } else {
    refreshQualityBadges();
  }
})();
