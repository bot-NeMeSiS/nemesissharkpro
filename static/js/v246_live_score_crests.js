
/* V246 · Live Score + Crests Fix Pro */
window.NMS_LIVE_SCORE_CRESTS_V246 = {
  realOnly: true,
  fallbackScore: "— : —",
  fallbackMinute: "Pendiente de minuto real",
  initials: function(name){
    if(!name) return "EQ";
    return name.trim().split(/\s+/).slice(0,2).map(x=>x[0]||"").join("").toUpperCase();
  },
  setCrest: function(el, name, logoUrl){
    if(!el) return;
    if(logoUrl){
      el.innerHTML = "";
      const img = document.createElement("img");
      img.src = logoUrl;
      img.alt = name || "Escudo";
      img.onerror = function(){ el.textContent = window.NMS_LIVE_SCORE_CRESTS_V246.initials(name); };
      el.appendChild(img);
    } else {
      el.textContent = window.NMS_LIVE_SCORE_CRESTS_V246.initials(name);
    }
  },
  render: function(match){
    if(!match) return;
    const home = match.home_name || match.home || "Equipo local";
    const away = match.away_name || match.away || "Equipo visitante";
    const hs = Number.isFinite(match.home_score) ? match.home_score : null;
    const as = Number.isFinite(match.away_score) ? match.away_score : null;
    document.getElementById("v246-home-name") && (document.getElementById("v246-home-name").textContent = home);
    document.getElementById("v246-away-name") && (document.getElementById("v246-away-name").textContent = away);
    document.getElementById("v246-score") && (document.getElementById("v246-score").textContent = (hs===null || as===null) ? "— : —" : `${hs} : ${as}`);
    document.getElementById("v246-match-minute") && (document.getElementById("v246-match-minute").textContent = match.minute ? `${match.minute}'` : "Pendiente de minuto real");
    document.getElementById("v246-match-status") && (document.getElementById("v246-match-status").textContent = match.status || "En directo");
    this.setCrest(document.getElementById("v246-home-crest"), home, match.home_logo || match.home_crest);
    this.setCrest(document.getElementById("v246-away-crest"), away, match.away_logo || match.away_crest);
  }
};
