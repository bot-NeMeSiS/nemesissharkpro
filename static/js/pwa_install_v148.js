
let nemesisDeferredPrompt = null;

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  nemesisDeferredPrompt = event;
  const banner = document.getElementById("nemesis-pwa-banner");
  if (banner) banner.classList.add("show");
});

window.addEventListener("appinstalled", () => {
  const banner = document.getElementById("nemesis-pwa-banner");
  if (banner) banner.classList.remove("show");
  nemesisDeferredPrompt = null;
});

document.addEventListener("DOMContentLoaded", () => {
  const installBtn = document.getElementById("nemesis-pwa-install");
  const closeBtn = document.getElementById("nemesis-pwa-close");

  if (installBtn) {
    installBtn.addEventListener("click", async () => {
      if (!nemesisDeferredPrompt) {
        alert("Si tu navegador lo permite, usa el menú del navegador y pulsa 'Instalar aplicación' o 'Añadir a pantalla de inicio'.");
        return;
      }
      nemesisDeferredPrompt.prompt();
      await nemesisDeferredPrompt.userChoice;
      nemesisDeferredPrompt = null;
      const banner = document.getElementById("nemesis-pwa-banner");
      if (banner) banner.classList.remove("show");
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      const banner = document.getElementById("nemesis-pwa-banner");
      if (banner) banner.classList.remove("show");
    });
  }

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  }
});
