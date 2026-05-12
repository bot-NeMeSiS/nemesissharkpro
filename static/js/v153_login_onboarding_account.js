document.addEventListener('click', (ev) => {
  const btn = ev.target.closest('[data-toggle-password]');
  if (!btn) return;
  const input = document.querySelector(btn.getAttribute('data-toggle-password'));
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
});
