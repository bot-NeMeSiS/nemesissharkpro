export function registerServiceWorker() {
  if (typeof window === "undefined") return;
  if (!("serviceWorker" in navigator)) return;

  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .catch((error) => {
        console.warn("Service Worker registration failed:", error);
      });
  });
}

export function canInstallPWA() {
  if (typeof window === "undefined") return false;
  return "BeforeInstallPromptEvent" in window || true;
}
