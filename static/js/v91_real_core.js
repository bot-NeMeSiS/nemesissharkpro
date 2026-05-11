
window.NSP_V91_REAL_CORE = true;
document.addEventListener("DOMContentLoaded", function(){
  document.querySelectorAll("*").forEach(function(el){
    if (!el.childNodes || el.childNodes.length !== 1 || el.childNodes[0].nodeType !== 3) return;
    var text = el.textContent || "";
    if (text.includes("h Madrid")) {
      el.textContent = text.replace(" h Madrid", "").replace("h Madrid", "");
    }
  });
});
