
(function () {
  function uid() {
    return window.NSP_USER_ID || localStorage.getItem("nsp_user_id") || "anonymous";
  }

  function toast(text) {
    var el = document.querySelector(".v84-toast");
    if (!el) {
      el = document.createElement("div");
      el.className = "v84-toast";
      document.body.appendChild(el);
    }
    el.textContent = text;
    el.classList.add("show");
    setTimeout(function(){ el.classList.remove("show"); }, 2800);
  }

  function track(type, title) {
    try {
      var p = new URLSearchParams({
        user_id: uid(),
        event_type: type,
        title: title || document.title
      });
      fetch("/api/premium-experience/event?" + p.toString(), {keepalive:true}).catch(function(){});
    } catch(e) {}
  }

  function addXp(amount, reason) {
    try {
      var p = new URLSearchParams({
        user_id: uid(),
        amount: String(amount || 5),
        reason: reason || "Actividad SHARK"
      });
      fetch("/api/premium-experience/xp?" + p.toString(), {keepalive:true})
        .then(function(){ toast("+" + (amount || 5) + " XP · " + (reason || "Actividad SHARK")); })
        .catch(function(){});
    } catch(e) {}
  }

  function completeMission(key) {
    try {
      var p = new URLSearchParams({user_id: uid(), mission_key: key});
      fetch("/api/premium-experience/mission?" + p.toString(), {keepalive:true})
        .then(function(){ toast("Misión completada · +" + key); })
        .catch(function(){});
    } catch(e) {}
  }

  window.NSPV84 = { track: track, addXp: addXp, completeMission: completeMission, toast: toast };

  function attach() {
    track("PAGE_VIEW", document.title);
    document.querySelectorAll("[data-v84-xp]").forEach(function(el){
      el.addEventListener("click", function(){
        addXp(Number(el.getAttribute("data-v84-xp") || "5"), el.getAttribute("data-v84-reason") || "Interacción premium");
      });
    });
    document.querySelectorAll("[data-v84-mission]").forEach(function(el){
      el.addEventListener("click", function(){
        completeMission(el.getAttribute("data-v84-mission"));
      });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", attach);
  else attach();
})();
