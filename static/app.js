
(function(){
  const box = document.getElementById("sharkBox");
  const open = document.getElementById("sharkOpen");
  const close = document.getElementById("sharkClose");
  const form = document.getElementById("sharkForm");
  const input = document.getElementById("sharkInput");
  const log = document.getElementById("sharkLog");

  function add(cls,text){
    if(!log) return;
    const div=document.createElement("div");
    div.className=cls;
    div.textContent=text;
    log.appendChild(div);
    log.scrollTop=log.scrollHeight;
  }

  function addRouteButton(container, hint){
    if(!container || !hint || !hint.url) return;
    const a=document.createElement("a");
    a.className="btn ai-route-btn";
    a.href=hint.url;
    a.textContent=hint.label || "Abrir sección";
    container.appendChild(a);
    container.scrollTop=container.scrollHeight;
  }


  function addSmartCards(container, data){
    if(!container || !data || !data.snapshot) return;
    const snap=data.snapshot || {};
    const answer=(data.answer || '').toLowerCase();
    const hint=(data.route_hint && data.route_hint.url) || '';
    let items=[];
    let kind='pick';
    if(hint.includes('partidos') || answer.includes('partidos reales') || answer.includes('centro live')){
      items=snap.matches || []; kind='match';
    }else{
      items=snap.picks || []; kind='pick';
    }
    if(!items.length) return;
    const wrap=document.createElement('div');
    wrap.className='ai-smart-cards';
    items.slice(0,3).forEach((it)=>{
      const card=document.createElement('a');
      card.className='ai-smart-card';
      card.href=kind==='match' ? '/partidos' : '/picks';
      const title=it.title || 'Partido real';
      const pick=it.pick || (kind==='match' ? (it.live_status || 'PROGRAMADO') : 'Pick real');
      const cuota=it.cuota ? ` @ ${it.cuota}` : '';
      const score=it.score ? `SHARK ${it.score}` : 'REAL ONLY';
      const ev=it.ev ? `EV ${it.ev}` : '';
      const live=[it.live_status,it.live_score,it.live_minute].filter(Boolean).join(' · ');
      card.innerHTML=`<strong>${title}</strong><span>${pick}${cuota}</span><small>${score}${ev ? ' · '+ev : ''}${live ? ' · '+live : ''}</small>`;
      wrap.appendChild(card);
    });
    container.appendChild(wrap);
    container.scrollTop=container.scrollHeight;
  }

  async function ask(text){
    if(!text) return;
    add("me",text);
    if(input) input.value="";
    add("ai","Analizando...");
    try{
      const res=await fetch("/api/shark-ai",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text})});
      const data=await res.json();
      if(log.lastChild) log.lastChild.remove();
      add("ai",data.answer || "No he podido responder.");
      addSmartCards(log, data);
      addRouteButton(log, data.route_hint);
      resetFloatingSharkIdle();
    }catch(e){
      if(log.lastChild) log.lastChild.remove();
      add("ai","No he podido conectar con SHARK AI.");
      resetFloatingSharkIdle();
    }
  }

  // SHARK AI flotante: cierre automático por inactividad.
  // No afecta a la página completa /shark-ai, solo a la ventanita flotante.
  const SHARK_IDLE_MS = 90000; // 90 segundos
  let sharkIdleTimer = null;

  function closeFloatingShark(){
    if(box) box.hidden = true;
    if(sharkIdleTimer){
      clearTimeout(sharkIdleTimer);
      sharkIdleTimer = null;
    }
  }

  function resetFloatingSharkIdle(){
    if(!box || box.hidden) return;
    if(sharkIdleTimer) clearTimeout(sharkIdleTimer);
    sharkIdleTimer = setTimeout(closeFloatingShark, SHARK_IDLE_MS);
  }

  function openFloatingShark(){
    if(!box) return;
    box.hidden = false;
    resetFloatingSharkIdle();
    if(input) setTimeout(()=>input.focus(), 80);
  }

  if(open) open.onclick=()=>openFloatingShark();
  if(close) close.onclick=()=>closeFloatingShark();
  if(box){
    ["mousemove", "mousedown", "keydown", "touchstart", "scroll"].forEach(evt=>{
      box.addEventListener(evt, resetFloatingSharkIdle, {passive:true});
    });
  }
  if(input) input.addEventListener("input", resetFloatingSharkIdle);
  if(form) form.onsubmit=(e)=>{e.preventDefault();resetFloatingSharkIdle();ask(input.value.trim());};
  document.querySelectorAll("#sharkBox [data-prompt]").forEach(b=>b.onclick=()=>{resetFloatingSharkIdle();ask(b.dataset.prompt);});

  const pageForm = document.getElementById("pageSharkForm");
  const pageInput = document.getElementById("pageSharkInput");
  const pageLog = document.getElementById("pageSharkLog");
  const insights = document.getElementById("aiInsights");

  function addPage(cls,text){
    if(!pageLog) return;
    const div=document.createElement("div");
    div.className=cls;
    div.textContent=text;
    pageLog.appendChild(div);
    pageLog.scrollTop=pageLog.scrollHeight;
  }

  async function askPage(text){
    if(!text) return;
    addPage("me",text);
    if(pageInput) pageInput.value="";
    addPage("ai","Analizando contexto real...");
    try{
      const res=await fetch("/api/shark-ai",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text})});
      const data=await res.json();
      if(pageLog.lastChild) pageLog.lastChild.remove();
      addPage("ai",data.answer || "No he podido responder.");
      addSmartCards(pageLog, data);
      addRouteButton(pageLog, data.route_hint);
    }catch(e){
      if(pageLog.lastChild) pageLog.lastChild.remove();
      addPage("ai","No he podido conectar con SHARK AI.");
    }
  }

  if(pageForm) pageForm.onsubmit=(e)=>{e.preventDefault();askPage(pageInput.value.trim());};
  document.querySelectorAll(".shark-ai-panel [data-prompt]").forEach(b=>b.addEventListener("click",()=>{
    if(pageLog) askPage(b.dataset.prompt);
  }));

  async function loadInsights(){
    if(!insights) return;
    try{
      const res=await fetch("/api/shark-ai/insights");
      const data=await res.json();
      const best=data.best_pick;
      const matches=(data.matches || []).length;
      if(best){
        insights.textContent=`Motor real conectado:\nPicks reales: ${(data.snapshot && data.snapshot.counts && data.snapshot.counts.picks) || 1} · Partidos reales: ${matches}\nMejor pick detectado:\n${best.title || 'Partido'} · ${best.pick || 'Pick'} @ ${best.cuota || '-'}\nCalidad: ${best.quality || '-'}\nStake sugerido: ${Number(data.risk.recommended_stake || 0).toFixed(2)}€ (${Number(data.risk.recommended_percent || 0).toFixed(2)}%)`;
      }else{
        insights.textContent=`Motor real conectado. Picks reales: 0 · Partidos reales: ${matches}. Cuando entren oportunidades reales, SHARK AI las mostrará aquí.`;
      }
    }catch(e){
      insights.textContent="Insights no disponibles.";
    }
  }
  loadInsights();

  async function loadOpenAiStatus(){
    const status = document.getElementById("openaiStatus");
    const mode = document.getElementById("sharkMode");
    try{
      const res=await fetch("/api/openai-status");
      const data=await res.json();
      const label=data.configured ? `OpenAI activo · ${data.model}` : "Fallback local activo";
      if(status){
        status.textContent=label;
        status.classList.toggle("openai", !!data.configured);
        status.classList.toggle("local", !data.configured);
      }
      if(mode) mode.textContent=label;
    }catch(e){
      if(status) status.textContent="Estado IA no disponible";
      if(mode) mode.textContent="Modo IA";
    }
  }
  loadOpenAiStatus();


  // Mostrar/ocultar contraseña en formularios de acceso.
  function initPasswordToggles(){
    document.querySelectorAll('input[type="password"]').forEach((input)=>{
      if(input.dataset.toggleReady === '1') return;
      input.dataset.toggleReady = '1';
      const wrap = document.createElement('span');
      wrap.className = 'password-wrap';
      input.parentNode.insertBefore(wrap, input);
      wrap.appendChild(input);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'password-eye';
      btn.setAttribute('aria-label', 'Mostrar contraseña');
      btn.textContent = '👁️';
      btn.addEventListener('click', ()=>{
        const showing = input.type === 'text';
        input.type = showing ? 'password' : 'text';
        btn.textContent = showing ? '👁️' : '🙈';
        btn.setAttribute('aria-label', showing ? 'Mostrar contraseña' : 'Ocultar contraseña');
      });
      wrap.appendChild(btn);
    });
  }
  initPasswordToggles();


  // V26.7: actualización de banca en euros sin perder persistencia.
  const bankrollForm = document.getElementById('bankrollForm');
  if(bankrollForm){
    bankrollForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const msg = document.getElementById('bankrollMsg');
      const value = document.getElementById('bankrollValue');
      try{
        const res = await fetch('/cliente/bankroll', {
          method: 'POST',
          headers: {'X-Requested-With':'XMLHttpRequest'},
          body: new FormData(bankrollForm)
        });
        const data = await res.json();
        if(data.ok){
          const amount = Number(data.balance || 0).toFixed(2) + '€';
          if(value) value.textContent = amount;
          const input = bankrollForm.querySelector('input[name="balance"]');
          if(input) input.value = Number(data.balance || 0).toFixed(2);
          if(msg) msg.textContent = 'Banca actualizada correctamente en euros (€).';
        }else{
          if(msg) msg.textContent = 'No se pudo actualizar la banca.';
        }
      }catch(err){
        bankrollForm.submit();
      }
    });
  }

  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();
// V26.9: gráfica de rendimiento cliente sin dependencias externas.
(function(){
  const canvas = document.getElementById('performanceChart');
  if(!canvas) return;
  const empty = document.getElementById('performanceEmpty');
  const ctx = canvas.getContext('2d');

  function resize(){
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(320, Math.floor(rect.width * dpr));
    canvas.height = Math.floor((Number(canvas.getAttribute('height')) || 170) * dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }

  function draw(points){
    resize();
    const w = canvas.getBoundingClientRect().width;
    const h = Number(canvas.getAttribute('height')) || 170;
    ctx.clearRect(0,0,w,h);
    ctx.font = '12px Arial';
    ctx.lineWidth = 1;

    const pad = 28;
    const values = points.map(p=>Number(p.profit || 0));
    if(values.length === 0){ if(empty) empty.hidden = false; return; }
    if(empty) empty.hidden = true;
    const min = Math.min(0, ...values);
    const max = Math.max(0, ...values);
    const range = Math.max(1, max-min);

    ctx.globalAlpha = .45;
    for(let i=0;i<4;i++){
      const y = pad + i*((h-pad*2)/3);
      ctx.beginPath(); ctx.moveTo(pad,y); ctx.lineTo(w-pad,y); ctx.strokeStyle='rgba(255,255,255,.16)'; ctx.stroke();
    }
    ctx.globalAlpha = 1;

    function x(i){ return pad + (points.length === 1 ? .5 : i/(points.length-1))*(w-pad*2); }
    function y(v){ return h-pad - ((v-min)/range)*(h-pad*2); }
    const zeroY = y(0);
    ctx.beginPath(); ctx.moveTo(pad,zeroY); ctx.lineTo(w-pad,zeroY); ctx.strokeStyle='rgba(77,220,255,.38)'; ctx.stroke();

    ctx.beginPath();
    values.forEach((v,i)=>{ const px=x(i), py=y(v); if(i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py); });
    ctx.strokeStyle='rgba(77,220,255,.95)'; ctx.lineWidth=3; ctx.stroke();

    values.forEach((v,i)=>{
      const px=x(i), py=y(v);
      ctx.beginPath(); ctx.arc(px,py,4,0,Math.PI*2); ctx.fillStyle='rgba(255,255,255,.95)'; ctx.fill();
    });
    ctx.fillStyle='rgba(255,255,255,.8)';
    ctx.fillText(max.toFixed(2)+'€', 4, pad+4);
    ctx.fillText(min.toFixed(2)+'€', 4, h-pad+4);
  }

  fetch('/api/cliente-performance', {cache:'no-store'})
    .then(r=>r.json())
    .then(data=>draw((data && data.points) || []))
    .catch(()=>{ if(empty){ empty.hidden=false; empty.textContent='Gráfica no disponible ahora mismo.'; }});
  window.addEventListener('resize', ()=>{
    fetch('/api/cliente-performance', {cache:'no-store'}).then(r=>r.json()).then(data=>draw((data && data.points)||[])).catch(()=>{});
  });
  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();

// V27.8 PWA install button — compatible móvil/desktop con ayuda clara
(function(){
  if('serviceWorker' in navigator){
    window.addEventListener('load', ()=>{
      navigator.serviceWorker.register('/service-worker.js', {scope:'/'}).catch(()=>{});
    });
  }
  let deferredPrompt = null;
  const banner = document.getElementById('pwaInstallBanner');
  const dismiss = document.getElementById('pwaDismissBtn');
  const buttons = [document.getElementById('installAppBtn'), document.getElementById('installAppBtnHero'), document.getElementById('pwaInstallBannerBtn')].filter(Boolean);
  const isStandalone = () => window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  function installHelp(){
    let modal = document.getElementById('installHelpModal');
    if(!modal){
      modal = document.createElement('div');
      modal.id = 'installHelpModal';
      modal.className = 'install-help-modal';
      modal.innerHTML = `
        <div class="install-help-card">
          <button class="install-help-close" type="button" aria-label="Cerrar">×</button>
          <div class="install-help-icon">📲</div>
          <h2>Instalar NeMeSiS SHARK PRO</h2>
          <p>Si el móvil no abre el instalador automático, no es fallo de la app: algunos navegadores obligan a instalar desde el menú:</p>
          <ul>
            <li><strong>Android / Chrome:</strong> menú ⋮ → “Instalar app” o “Añadir a pantalla de inicio”.</li>
            <li><strong>iPhone / Safari:</strong> compartir ⎋ → “Añadir a pantalla de inicio”.</li>
            <li><strong>PC:</strong> icono de instalar en la barra del navegador.</li>
          </ul>
          <button class="btn primary install-help-ok" type="button">Entendido</button>
        </div>`;
      document.body.appendChild(modal);
      modal.querySelector('.install-help-close').onclick = () => modal.classList.remove('show');
      modal.querySelector('.install-help-ok').onclick = () => modal.classList.remove('show');
      modal.addEventListener('click', (e)=>{ if(e.target === modal) modal.classList.remove('show'); });
    }
    modal.classList.add('show');
  }
  function setReady(){
    if(banner && !localStorage.getItem('nemesisPwaDismissed') && !isStandalone()) banner.hidden=false;
    buttons.forEach(b=>{
      b.hidden=false;
      if(isStandalone()){ b.textContent='✅ App instalada'; b.disabled=true; b.classList.remove('install-ready'); }
      else { b.classList.add('install-ready'); }
    });
  }
  if(dismiss){ dismiss.addEventListener('click', ()=>{ localStorage.setItem('nemesisPwaDismissed','1'); if(banner) banner.hidden=true; }); }
  buttons.forEach(btn=>{
    btn.hidden=false;
    btn.addEventListener('click', async ()=>{
      if(isStandalone()){ return; }
      if(deferredPrompt){
        deferredPrompt.prompt();
        try{ await deferredPrompt.userChoice; }catch(e){}
        deferredPrompt = null;
        buttons.forEach(b=>b.classList.remove('install-ready'));
      }else{
        installHelp();
      }
    });
  });
  window.addEventListener('beforeinstallprompt', (e)=>{
    e.preventDefault();
    deferredPrompt = e;
    setReady();
  });
  window.addEventListener('appinstalled', ()=>{
    buttons.forEach(b=>{ b.textContent='✅ App instalada'; b.disabled=true; b.classList.remove('install-ready'); }); if(banner) banner.hidden=true;
  });
  setReady();
  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();


// V28.1 Real Live Data Restore: refresco suave sin bloquear la UI.
(function(){
  const path = window.location.pathname;
  const livePages = ['/picks','/partidos','/clientes','/dashboard'];
  if(!livePages.includes(path)) return;
  let running = false;
  async function refreshLive(){
    if(running) return;
    running = true;
    try{
      const res = await fetch('/api/live-refresh', {method:'POST', headers:{'X-Requested-With':'fetch'}});
      const data = await res.json().catch(()=>null);
      if(data && data.ok){
        document.body.dataset.liveSync = 'ok';
        // No forzamos reload inmediato para no molestar mientras el usuario escribe un importe.
        // La información nueva aparecerá al cambiar de pestaña o recargar. En móvil evita saltos.
      }
    }catch(e){
      document.body.dataset.liveSync = 'offline';
    }finally{
      running = false;
    }
  }
  setTimeout(refreshLive, 30000);
  setInterval(refreshLive, 900000);
  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();


// V28.2 password eye global
(function(){
  document.querySelectorAll('.toggle-password').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const wrap = btn.closest('.password-wrap');
      const input = wrap ? wrap.querySelector('input') : null;
      if(!input) return;
      input.type = input.type === 'password' ? 'text' : 'password';
      btn.textContent = input.type === 'password' ? '👁️' : '🙈';
    });
  });
  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();


// V28.3 premium live auto refresh
(function(){
  const isLivePage = location.pathname.includes('/partidos');
  if(!isLivePage) return;
  let refreshTimer = null;
  const start = () => {
    if(refreshTimer) return;
    refreshTimer = setInterval(() => {
      if(document.hidden) return;
      const url = new URL(location.href);
      url.searchParams.set('_live', Date.now().toString());
      fetch(url.toString(), {headers:{'X-Requested-With':'fetch'}})
        .then(r => r.text())
        .then(html => {
          const doc = new DOMParser().parseFromString(html, 'text/html');
          const next = doc.querySelector('.premium-live-grid');
          const current = document.querySelector('.premium-live-grid');
          if(next && current) current.innerHTML = next.innerHTML;
        })
        .catch(()=>{});
    }, 45000);
  };
  start();
  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();

document.addEventListener('DOMContentLoaded', () => {
  const homeInstall = document.getElementById('homeInstallBtn');
  const navInstall = document.getElementById('installAppBtn');
  if(homeInstall && navInstall){
    homeInstall.addEventListener('click', () => navInstall.click());
  }
});


// V30.6 SHARK AI QUICK ACTIONS
(function(){
  const quickActions = {
    "Picks de valor": "/picks?sort=value",
    "Top SHARK": "/picks?sort=score",
    "Fútbol hoy": "/partidos",
    "Mi banca": "/clientes#bankroll-v30",
    "Mejor pick": "/picks?sort=best",
    "Partidos hoy": "/partidos?range=today",
    "En vivo": "/partidos?q=live",
    "Populares": "/picks?filter=popular",
    "Premium": "/picks?premium=1"
  };

  function enhanceSharkButtons(){
    const buttons = Array.from(document.querySelectorAll("button, a"));
    buttons.forEach(btn => {
      const label = (btn.textContent || "").trim();
      if(quickActions[label] && !btn.dataset.sharkQuickReady){
        btn.dataset.sharkQuickReady = "1";
        btn.classList.add("shark-quick-action-v306");
        btn.addEventListener("click", (ev) => {
          ev.preventDefault();
          window.location.href = quickActions[label];
        });
      }
    });

    const panel = document.querySelector(".shark-panel, #sharkPanel, .shark-ai-panel, .shark-chat, .shark-modal");
    if(panel && !panel.querySelector(".shark-direct-grid-v306")){
      const grid = document.createElement("div");
      grid.className = "shark-direct-grid-v306";
      grid.innerHTML = `
        <button type="button" data-go="/partidos?range=today">📅 Partidos hoy</button>
        <button type="button" data-go="/partidos?q=live">🔴 En vivo</button>
        <button type="button" data-go="/picks?sort=score">🦈 Top SHARK</button><button type="button" data-go="/partidos">⚽ Fútbol hoy</button>
        <button type="button" data-go="/picks?filter=popular">🔥 Populares</button>
        <button type="button" data-go="/picks?premium=1">💎 Premium</button>
        <button type="button" data-go="/clientes#bankroll-v30">🏦 Mi banca</button>
      `;
      const header = panel.querySelector(".shark-header, .chat-header, h2, h3") || panel.firstElementChild;
      if(header && header.parentNode){
        header.parentNode.insertBefore(grid, header.nextSibling);
      }else{
        panel.prepend(grid);
      }
      grid.querySelectorAll("button").forEach(b=>{
        b.addEventListener("click", ()=> window.location.href = b.dataset.go);
      });
    }
  }

  document.addEventListener("DOMContentLoaded", enhanceSharkButtons);
  document.addEventListener("click", () => setTimeout(enhanceSharkButtons, 80));
  setInterval(enhanceSharkButtons, 60000);
  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();


// V30.9_REAL_AI_NO_FAKE_CLIENT_CLEANER
(function(){
  const fakeNames = [
    "Real Madrid vs Manchester City",
    "Lakers vs Warriors",
    "Barcelona vs Atlético Madrid",
    "Barcelona vs Atletico Madrid",
    "Arsenal vs Liverpool"
  ];
  function cleanFakeMessages(){
    document.querySelectorAll("p,span,div,strong,small").forEach(el=>{
      if(el.children.length) return;
      const t = el.textContent || "";
      if(fakeNames.some(n => t.includes(n))){
        el.textContent = "SHARK AI está en modo real-only. Solo se muestran picks reales activos.";
      }
    });
  }
  document.addEventListener("DOMContentLoaded", cleanFakeMessages);
  document.addEventListener("click", () => setTimeout(cleanFakeMessages, 200));
  setInterval(cleanFakeMessages, 60000);
  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();


// V38.0 FINAL UX + MOBILE EXPERIENCE
(function(){
  function setActiveNav(){
    const path = window.location.pathname;
    document.querySelectorAll('.bottom-mobile-nav-v283 a,.client-app-nav-v308 a,.pro-menu-v33 a').forEach(a=>{
      try{
        const href = new URL(a.getAttribute('href'), window.location.origin).pathname;
        a.classList.toggle('active', href === path || (href !== '/' && path.startsWith(href)));
      }catch(e){}
    });
  }
  function enhanceLinks(){
    document.querySelectorAll('a[href]:not([target])').forEach(a=>{
      const href=a.getAttribute('href')||'';
      if(!href || href.startsWith('#') || href.startsWith('javascript:') || href.startsWith('mailto:')) return;
      if(a.dataset.v38) return;
      a.dataset.v38='1';
      a.addEventListener('click', ()=>{
        if(a.origin && a.origin !== location.origin) return;
        document.body.classList.add('loading-page-v38');
        if(!document.querySelector('.page-loader-v38')){
          const bar=document.createElement('div');bar.className='page-loader-v38';document.body.appendChild(bar);
        }
      });
    });
  }
  function mobileHeroShortcuts(){
    const hero=document.querySelector('.pro-hero-v33');
    if(!hero || document.querySelector('.quick-mobile-grid-v38')) return;
    const grid=document.createElement('div');
    grid.className='quick-mobile-grid-v38';
    grid.innerHTML='<a href="/partidos?date=today"><b>Hoy</b>Partidos</a><a href="/picks"><b>Top</b>Picks</a><a href="/clasificaciones"><b>Tabla</b>Ligas</a><a href="/shark-ai"><b>AI</b>SHARK</a>';
    hero.insertAdjacentElement('afterend', grid);
  }
  function clarifyBetLabels(){
    const map=[[/\bDraw\b/gi,'Empate'],[/\bHome\b/gi,'Local'],[/\bAway\b/gi,'Visitante'],[/\bh2h\b/gi,'Ganador del partido'],[/\btotals\b/gi,'Goles totales'],[/\bspreads\b/gi,'Hándicap']];
    document.querySelectorAll('.pro-bet-v33 b,.pro-exact-v33 strong,.pick-choice,.bet-choice').forEach(el=>{
      if(el.dataset.clearV38) return;
      let t=el.textContent||'';
      map.forEach(([r,v])=>t=t.replace(r,v));
      el.textContent=t.replace(/\s+/g,' ').trim();
      el.dataset.clearV38='1';
    });
  }
  function init(){setActiveNav();enhanceLinks();mobileHeroShortcuts();clarifyBetLabels();}
  document.addEventListener('DOMContentLoaded', init);
  window.addEventListener('pageshow', ()=>{document.body.classList.remove('loading-page-v38');document.querySelector('.page-loader-v38')?.remove();init();});
  setInterval(init, 60000);
  // V50.0 — Notificaciones push de la app.
  function base64UrlToUint8Array(base64String){
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
    return outputArray;
  }

  async function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    try{return await navigator.serviceWorker.register('/service-worker.js');}
    catch(e){return null;}
  }

  async function loadPushStatus(){
    const box=document.getElementById('pushStatusBox');
    const label=document.getElementById('pushStatusLabel');
    if(!box && !label) return;
    if(!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)){
      if(label) label.textContent='Este dispositivo no admite push. Telegram seguirá funcionando.';
      return;
    }
    try{
      const res=await fetch('/api/push/status');
      const data=await res.json();
      if(label){
        if(data.enabled) label.textContent='Push activo en este dispositivo.';
        else if(!data.configured) label.textContent='Push preparado. Falta activar claves VAPID en Render.';
        else label.textContent='Push disponible. Puedes activarlo aquí.';
      }
      if(box) box.classList.toggle('push-on', !!data.enabled);
    }catch(e){ if(label) label.textContent='Estado push no disponible ahora.'; }
  }

  async function enablePushNotifications(){
    const btn=document.getElementById('enablePushBtn');
    if(btn){btn.disabled=true; btn.textContent='Activando...';}
    try{
      const cfgRes=await fetch('/api/push/config');
      const cfg=await cfgRes.json();
      if(!cfg.configured || !cfg.publicKey){
        alert(cfg.reason || 'Push todavía no está configurado en Render.');
        return;
      }
      const permission=await Notification.requestPermission();
      if(permission !== 'granted'){
        alert('No has dado permiso a las notificaciones.');
        return;
      }
      const reg=await registerServiceWorker();
      if(!reg){ alert('No se pudo registrar la app para push.'); return; }
      const sub=await reg.pushManager.subscribe({userVisibleOnly:true, applicationServerKey:base64UrlToUint8Array(cfg.publicKey)});
      const save=await fetch('/api/push/subscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({subscription:sub})});
      const data=await save.json();
      alert(data.message || (data.ok ? 'Push activado.' : 'No se pudo activar push.'));
      loadPushStatus();
    }catch(e){ alert('No se pudo activar push ahora.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Activar avisos push';} }
  }

  async function testPushNotifications(){
    const btn=document.getElementById('testPushBtn');
    if(btn){btn.disabled=true; btn.textContent='Enviando...';}
    try{
      const r=await fetch('/api/push/test',{method:'POST'});
      const data=await r.json();
      alert(data.message || (data.ok ? 'Push enviado.' : 'No se pudo enviar.'));
    }catch(e){ alert('No se pudo probar push.'); }
    finally{ if(btn){btn.disabled=false; btn.textContent='Enviar prueba push';} }
  }

  async function disablePushNotifications(){
    try{
      const reg=await navigator.serviceWorker?.ready;
      const sub=await reg?.pushManager?.getSubscription();
      if(sub){
        await fetch('/api/push/unsubscribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({endpoint:sub.endpoint})});
        await sub.unsubscribe();
      }else{
        await fetch('/api/push/unsubscribe',{method:'POST'});
      }
      alert('Push desactivado en este dispositivo.');
      loadPushStatus();
    }catch(e){ alert('No se pudo desactivar push.'); }
  }

  registerServiceWorker();
  loadPushStatus();
  document.getElementById('enablePushBtn')?.addEventListener('click', enablePushNotifications);
  document.getElementById('testPushBtn')?.addEventListener('click', testPushNotifications);
  document.getElementById('disablePushBtn')?.addEventListener('click', disablePushNotifications);

})();

// V53.0 — pulido motion/UX ligero sin cargar Render.
(function(){
  try{
    document.documentElement.classList.add('v53-motion-ready');
    const path = location.pathname;
    document.querySelectorAll('.bottom-mobile-nav-v283 a, .client-app-nav-v308 a, .menu-v52 a, .nav a').forEach((el)=>{
      const href = el.getAttribute('href') || '';
      if(!href || href === '#') return;
      const clean = href.split('?')[0].split('#')[0];
      if(clean === path || (path === '/' && clean === '/') || (path.startsWith(clean) && clean !== '/')) el.classList.add('active');
    });
    // Oculta avisos PWA si ya está instalada o si el usuario los cerró.
    const standalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
    if(standalone){
      document.querySelectorAll('#pwaInstallBanner,.pwa-banner-v36,.install-mini-v38,[data-install-banner]').forEach(el=>{el.hidden = true; el.style.display='none';});
      localStorage.setItem('nemesisPwaDismissed','1');
    }
    document.querySelectorAll('[data-dismiss], .pwa-dismiss, #pwaDismissBtn').forEach(btn=>{
      btn.addEventListener('click', ()=>{
        localStorage.setItem('nemesisPwaDismissed','1');
        const box = btn.closest('#pwaInstallBanner,.pwa-banner-v36,[data-install-banner]');
        if(box){ box.hidden = true; box.style.display='none'; }
      });
    });
    // Efecto táctil sutil para cards principales.
    document.querySelectorAll('.pick-line-v52,.metrics-v52 a,.quick-v52 a,.card-v52,.live-item-v52').forEach(card=>{
      card.addEventListener('pointerdown',()=>card.classList.add('is-pressing'));
      ['pointerup','pointercancel','pointerleave'].forEach(evt=>card.addEventListener(evt,()=>card.classList.remove('is-pressing')));
    });
  }catch(e){}
})();
