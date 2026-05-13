
/*
 NeMeSiS SHARK PRO V74 — UX tracking ligero
 No bloquea la app si falla.
*/
(function () {
  function getUserId() {
    return window.NSP_USER_ID || localStorage.getItem("nsp_user_id") || "anonymous";
  }

  function track(eventType, value) {
    try {
      const params = new URLSearchParams({
        user_id: getUserId(),
        event_type: eventType,
        event_value: value || "",
        page: window.location.pathname,
        source: "PWA"
      });
      fetch("/api/ux/track?" + params.toString(), { method: "GET", keepalive: true }).catch(function(){});
    } catch (e) {}
  }

  window.NSPTrack = track;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      track("PAGE_VIEW", document.title || window.location.pathname);
    });
  } else {
    track("PAGE_VIEW", document.title || window.location.pathname);
  }
})();
