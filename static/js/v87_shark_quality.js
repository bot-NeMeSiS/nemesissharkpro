
(function(){
  function animateScores(){
    document.querySelectorAll("[data-v87-score]").forEach(function(el){
      var score = Number(el.getAttribute("data-v87-score") || "0");
      if (score >= 82) el.classList.add("v87-status-premium");
      else if (score >= 68) el.classList.add("v87-status-caution");
      else el.classList.add("v87-status-rejected");
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", animateScores);
  else animateScores();
})();
