
(function () {
  function formatMadrid(value) {
    try {
      var d = new Date(value);
      if (isNaN(d.getTime())) return null;
      var date = new Intl.DateTimeFormat("es-ES", {timeZone:"Europe/Madrid", day:"2-digit", month:"2-digit", year:"numeric"}).format(d);
      var time = new Intl.DateTimeFormat("es-ES", {timeZone:"Europe/Madrid", hour:"2-digit", minute:"2-digit"}).format(d);
      return date + " · " + time + " h Madrid";
    } catch(e) { return null; }
  }
  function run() {
    document.querySelectorAll("[data-utc-time]").forEach(function(el){
      var formatted = formatMadrid(el.getAttribute("data-utc-time"));
      if (formatted) el.textContent = formatted;
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
