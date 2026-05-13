
document.addEventListener("DOMContentLoaded", () => {
  const clientPaths = ["/cliente", "/fixtures/today-pro", "/partidos/hoy-pro", "/home-live-real", "/favorites-pro"];
  const isClient = clientPaths.some(p => (window.location.pathname || "").startsWith(p));
  if (!isClient) return;
  document.body.classList.add("client-mode");
  const badWords = ["debug", "endpoint", "admin only", "technical", "mock", "fake"];
  document.querySelectorAll("body *").forEach(el => {
    if (!el || el.children.length > 0) return;
    const txt = (el.textContent || "").toLowerCase();
    if (badWords.some(w => txt.includes(w))) el.classList.add("technical-only");
  });
});
