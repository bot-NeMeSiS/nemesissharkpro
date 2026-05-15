
/* V249 · Real Intelligence Engine */
window.NMS_REAL_INTELLIGENCE_V249 = {
  realOnly: true,

  setPressure: function(value){
    const fill = document.getElementById("v249-pressure-fill");
    const txt = document.getElementById("v249-pressure-text");
    if(fill){
      fill.style.width = Math.max(0, Math.min(100, value || 0)) + "%";
    }
    if(txt){
      txt.textContent = value ? `Presión detectada: ${value}%` : "Esperando datos reales suficientes.";
    }
  },

  setMomentum: function(home, away){
    const h = document.getElementById("v249-home-momentum");
    const a = document.getElementById("v249-away-momentum");
    if(h) h.style.width = Math.max(0, Math.min(100, home || 0)) + "%";
    if(a) a.style.width = Math.max(0, Math.min(100, away || 0)) + "%";
  },

  setHotMatch: function(active){
    const el = document.getElementById("v249-hot-match");
    if(!el) return;
    el.textContent = active ? "Partido caliente detectado." : "Sin actividad suficiente.";
  },

  addAlert: function(text){
    if(!text) return;
    const box = document.getElementById("v249-alerts");
    if(!box) return;

    const empty = box.querySelector(".v249-alert-empty");
    if(empty) empty.remove();

    const div = document.createElement("div");
    div.className = "v249-alert";
    div.textContent = text;
    box.appendChild(div);
  }
};
