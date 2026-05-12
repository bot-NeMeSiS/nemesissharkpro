
document.addEventListener("DOMContentLoaded", () => {
  const badWords = [
    "debug",
    "endpoint",
    "mock",
    "fake",
    "technical",
    "admin only"
  ];

  document.querySelectorAll("body *").forEach((el) => {
    if (!el || el.children.length > 0) return;

    const txt = (el.textContent || "").trim().toLowerCase();
    if (!txt) return;

    if (badWords.some(w => txt.includes(w))) {
      el.style.display = "none";
    }
  });
});
