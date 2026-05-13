
(function(){
  function pad(n){ return String(n).padStart(2, "0"); }

  function formatCardDates(){
    document.querySelectorAll("[data-v85-utc]").forEach(function(el){
      var raw = el.getAttribute("data-v85-utc");
      if (!raw) return;
      var d = new Date(raw);
      if (isNaN(d.getTime())) return;

      var date = new Intl.DateTimeFormat("es-ES", {
        weekday: "short",
        day: "2-digit",
        month: "short"
      }).format(d).replace(".", "").toUpperCase();

      var time = new Intl.DateTimeFormat("es-ES", {
        hour: "2-digit",
        minute: "2-digit"
      }).format(d);

      var dateTarget = el.querySelector("[data-v85-date]");
      var timeTarget = el.querySelector("[data-v85-time]");
      if (dateTarget) dateTarget.textContent = date;
      if (timeTarget) timeTarget.textContent = time;
    });
  }

  function addCardEvents(){
    document.querySelectorAll(".v85-card").forEach(function(card){
      card.addEventListener("mouseenter", function(){
        card.style.transform = "translateY(-2px)";
      });
      card.addEventListener("mouseleave", function(){
        card.style.transform = "";
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function(){
      formatCardDates();
      addCardEvents();
    });
  } else {
    formatCardDates();
    addCardEvents();
  }
})();
