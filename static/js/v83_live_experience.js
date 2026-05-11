
(function () {
  function updateCountdowns() {
    document.querySelectorAll("[data-v83-start]").forEach(function (el) {
      var raw = el.getAttribute("data-v83-start");
      if (!raw) return;
      var start = new Date(raw);
      if (isNaN(start.getTime())) return;

      var now = new Date();
      var diffMin = Math.floor((start.getTime() - now.getTime()) / 60000);
      var text = "";

      if (diffMin <= -130) text = "FINALIZADO";
      else if (diffMin <= 0) text = "LIVE";
      else if (diffMin < 60) text = "Empieza en " + diffMin + " min";
      else if (diffMin < 1440) text = "Empieza en " + Math.floor(diffMin / 60) + " h";
      else text = "Empieza en " + Math.floor(diffMin / 1440) + " días";

      el.textContent = text;
    });
  }

  function tick() {
    updateCountdowns();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tick);
  } else {
    tick();
  }

  setInterval(tick, 30000);
})();
