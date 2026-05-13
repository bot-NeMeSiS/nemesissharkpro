async function startCheckout(plan){
  const box=document.getElementById('billingResult');
  if(box) box.textContent='Preparando checkout real para '+plan+'...';
  try{
    const res=await fetch('/api/v166/create-checkout-session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({plan})});
    const data=await res.json();
    if(data.ok && data.checkout_url){ window.location.href=data.checkout_url; return; }
    if(box) box.textContent=(data.error||'Checkout no disponible')+'\n\n'+JSON.stringify(data.billing?.stripe||{},null,2);
  }catch(e){ if(box) box.textContent='Error preparando checkout: '+e.message; }
}
