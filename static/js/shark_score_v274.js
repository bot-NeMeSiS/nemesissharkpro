
(function(){
  function clamp(n,min,max){ return Math.max(min, Math.min(max, n)); }

  window.renderSharkScore = function(container, scoreData){
    if(!container || !scoreData) return;
    var score = Number(scoreData.score || 0);
    var cls = score >= 82 ? 'shark-score-high' : (score >= 68 ? 'shark-score-mid' : 'shark-score-low');
    container.innerHTML = `
      <div class="shark-score-card ${cls}">
        <div class="shark-score-header">
          <div class="shark-score-title">🦈 SHARK SCORE</div>
          <div class="shark-score-percent">${score}%</div>
        </div>
        <div class="shark-score-bar">
          <div class="shark-score-fill" style="width:${clamp(score,1,99)}%"></div>
        </div>
        <div class="shark-score-meta">
          <div class="shark-score-pill">${scoreData.risk_badge || '🟡'} Riesgo ${scoreData.risk || '-'}</div>
          <div class="shark-score-pill">Stake ${scoreData.stake || 1}/5</div>
          <div class="shark-score-pill">${scoreData.model || 'BASIC'}</div>
        </div>
        <div class="shark-score-verdict">${scoreData.verdict || ''}</div>
      </div>`;
  };
})();
