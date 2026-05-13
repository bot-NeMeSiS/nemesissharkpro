
/*
 NeMeSiS SHARK PRO V70 — Premium UI JS
 Ligero, sin dependencias, seguro para Render/PWA.
*/

(function () {
  function animateCounters() {
    const counters = document.querySelectorAll("[data-nsp-counter]");
    counters.forEach((el) => {
      const raw = el.getAttribute("data-nsp-counter");
      const target = Number(raw || "0");
      if (!Number.isFinite(target)) return;

      const suffix = el.getAttribute("data-nsp-suffix") || "";
      const duration = 650;
      const start = performance.now();

      function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(target * eased);
        el.textContent = value + suffix;
        if (progress < 1) requestAnimationFrame(tick);
      }

      requestAnimationFrame(tick);
    });
  }

  function markActiveMobileNav() {
    const path = window.location.pathname;
    document.querySelectorAll(".nsp-mobile-bottom a").forEach((a) => {
      if (a.getAttribute("href") === path) a.classList.add("active");
    });
  }

  function enhanceTables() {
    document.querySelectorAll("table").forEach((table) => {
      if (!table.classList.contains("nsp-table")) {
        table.classList.add("nsp-table");
      }
    });
  }

  function init() {
    animateCounters();
    markActiveMobileNav();
    enhanceTables();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
