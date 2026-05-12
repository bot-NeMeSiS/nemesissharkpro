
(function(){
  const path = window.location.pathname || "";
  if(path.startsWith("/cliente") || path === "/en-directo"){
    document.body.classList.add("client-mode");
    const badWords = ["DEBUG", "debug", "endpoint", "mock", "fake", "demo admin", "admin only"];
    document.querySelectorAll("body *").forEach((el)=>{
      if(!el || !el.childNodes || el.children.length > 0) return;
      const txt = (el.textContent || "").trim();
      if(!txt) return;
      const lower = txt.toLowerCase();
      if(badWords.some(w => lower.includes(w.toLowerCase()))){
        el.classList.add("technical-only");
      }
    });
  }
})();
