async function v174Call(url){
  const out=document.getElementById('v174-output');
  out.textContent='Ejecutando prueba real...';
  try{
    const res=await fetch(url,{method:'POST'});
    const data=await res.json();
    out.textContent=JSON.stringify(data,null,2);
  }catch(e){out.textContent='ERROR: '+e.message;}
}
function v174Handshake(){v174Call('/api/v174/telegram-admin/handshake')}
function v174TestAdmin(){v174Call('/api/v174/telegram-admin/test-admin')}
function v174TestChannel(){v174Call('/api/v174/telegram-admin/test-channel')}
