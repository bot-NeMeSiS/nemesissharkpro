
/* V248 · Unified Match Center Pro */
window.NMS_MATCH_CENTER_V248 = {
  realOnly: true,
  renderMatch: function(raw){
    const binder = window.NMS_LIVE_BINDING_V247;
    if(!binder || !raw) return;
    const m = binder.normalizeMatch(raw);
    const score = binder.scoreText(m);
    const minute = binder.minuteText(m);
    const set = (id, val) => { const el=document.getElementById(id); if(el) el.textContent=val; };
    set("v248-home-name", m.home_name);
    set("v248-away-name", m.away_name);
    set("v248-score", score);
    set("v248-minute", minute);
    set("v248-status", m.status || "Pendiente de estado real");
    const crest = (id, name, logo) => {
      const el=document.getElementById(id); if(!el) return;
      const helper = window.NMS_LIVE_SCORE_CRESTS_V246;
      if(helper && helper.setCrest){ helper.setCrest(el, name, logo); }
      else { el.textContent = (name||"EQ").split(/\s+/).slice(0,2).map(x=>x[0]).join("").toUpperCase(); }
    };
    crest("v248-home-crest", m.home_name, m.home_logo);
    crest("v248-away-crest", m.away_name, m.away_logo);
  }
};
