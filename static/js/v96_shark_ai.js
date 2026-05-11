document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('sharkForm');
  const input = document.getElementById('sharkQuestion');
  const answer = document.getElementById('answer');
  const recs = document.getElementById('recommendations');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const question = (input.value || '').trim();
    answer.textContent = 'SHARK está leyendo Real Core...';
    try {
      const response = await fetch('/api/v96/shark-ai', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({question})
      });
      const data = await response.json();
      answer.textContent = data.answer || 'Sin respuesta disponible.';
      recs.innerHTML = (data.recommended_matches || []).map(item => `
        <article class="match-card">
          <div class="topline"><span>${item.league || ''}</span><b>${item.entry_level || ''}</b></div>
          <h2>${item.title || ''}</h2>
          <p class="time">${item.status || ''} · ${item.date || ''} · ${item.time || ''}</p>
          <div class="pickbox"><span>Lectura</span><strong>${item.selection || 'Mercado pendiente'}</strong></div>
          <p>${item.shark_reading || ''}</p>
        </article>`).join('');
    } catch (error) {
      answer.textContent = 'No se pudo consultar SHARK AI ahora mismo.';
    }
  });
});
