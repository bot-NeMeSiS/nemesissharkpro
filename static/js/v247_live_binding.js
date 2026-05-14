
/* V247 · Live Binding + Data Integrity Pro */
window.NMS_LIVE_BINDING_V247 = {
  realOnly: true,
  fallbackScore: "— : —",
  fallbackMinute: "Pendiente de minuto real",
  normalizeMatch: function(raw){
    raw = raw || {};
    const homeScore = Number.isFinite(raw.home_score) ? raw.home_score :
      (Number.isFinite(raw.homeScore) ? raw.homeScore : null);
    const awayScore = Number.isFinite(raw.away_score) ? raw.away_score :
      (Number.isFinite(raw.awayScore) ? raw.awayScore : null);
    return {
      fixture_id: raw.fixture_id || raw.id || raw.match_id || null,
      league: raw.league || raw.competition || "",
      home_name: raw.home_name || raw.home || raw.homeTeam || "Equipo local",
      away_name: raw.away_name || raw.away || raw.awayTeam || "Equipo visitante",
      home_score: homeScore,
      away_score: awayScore,
      minute: raw.minute || raw.elapsed || raw.time || null,
      status: raw.status || raw.match_status || "Pendiente de estado real",
      home_logo: raw.home_logo || raw.home_crest || raw.homeLogo || null,
      away_logo: raw.away_logo || raw.away_crest || raw.awayLogo || null
    };
  },
  hasRealScore: function(match){
    return match && Number.isFinite(match.home_score) && Number.isFinite(match.away_score);
  },
  scoreText: function(match){
    return this.hasRealScore(match) ? `${match.home_score} : ${match.away_score}` : this.fallbackScore;
  },
  minuteText: function(match){
    return match && match.minute ? `${match.minute}'` : this.fallbackMinute;
  }
};
