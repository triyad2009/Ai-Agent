let sessionId=null, recognition=null, listening=false;

const $=id=>document.getElementById(id);
const messages=$("messages"), mic=$("mic"), text=$("text"), send=$("send"), orb=$("orb");

function add(role,content){const d=document.createElement("div");d.className="msg "+role;d.textContent=content;messages.appendChild(d);messages.scrollTop=messages.scrollHeight}
function setStatus(t,ok=true){$("status").textContent=t;$("dot").style.background=ok?"#4bd38b":"#f0ad4e"}
function speak(t){if("speechSynthesis" in window){speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);u.lang=$("lang").value;speechSynthesis.speak(u)}}

async function init(){
  const r=await fetch("/api/session",{method:"POST"}); const d=await r.json(); sessionId=d.session_id;
  setStatus("Ready"); add("agent","Ready. Click the microphone and tell me what you want done on your Windows PC.");
  if(!("SpeechRecognition" in window || "webkitSpeechRecognition" in window)){ $("heroText").textContent="Voice recognition unavailable in this browser"; mic.disabled=true; }
}
async function sendCommand(value){
  const msg=value.trim(); if(!msg)return; add("user",msg); text.value=""; $("heroText").textContent="Working…"; setStatus("Agent working…");
  try{
    const r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:sessionId,message:msg})});
    const d=await r.json();
    if(d.confirmation_required){showConfirm(d);return}
    if(d.error){add("agent","Error: "+d.error);setStatus("Error",false);return}
    add("agent",d.answer||"Done."); speak(d.answer||"Done."); setStatus("Ready"); $("heroText").textContent="Speak a command";
  }catch(e){add("agent","Connection error: "+e);setStatus("Offline",false)}
}
function showConfirm(d){$("confirmTitle").textContent="Allow "+(d.tool||"this action")+"?";$("confirmBody").textContent=d.message||JSON.stringify(d.args||{},null,2);$("confirm").classList.remove("hidden");setStatus("Waiting for confirmation",false)}
async function resolve(approved){
  $("confirm").classList.add("hidden"); setStatus("Continuing…");
  const r=await fetch("/api/confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({session_id:sessionId,approved})});
  const d=await r.json(); if(d.confirmation_required){showConfirm(d);return}
  add("agent",d.answer|| (approved?"Action completed.":"Action cancelled.")); speak(d.answer||"Action completed."); setStatus("Ready");$("heroText").textContent="Speak a command";
}
$("allow").onclick=()=>resolve(true); $("deny").onclick=()=>resolve(false); send.onclick=()=>sendCommand(text.value); text.onkeydown=e=>{if(e.key==="Enter")sendCommand(text.value)}
$("clear").onclick=()=>messages.innerHTML="";

function setupVoice(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;if(!SR)return;
  recognition=new SR(); recognition.lang=$("lang").value; recognition.interimResults=true; recognition.continuous=false;
  recognition.onstart=()=>{listening=true;orb.classList.add("listening");mic.textContent="Listening…";$("heroText").textContent="Listening…"};
  recognition.onresult=e=>{let final="", interim="";for(let i=e.resultIndex;i<e.results.length;i++){const s=e.results[i][0].transcript;if(e.results[i].isFinal)final+=s;else interim+=s}$("transcript").textContent=final||interim;if(final)sendCommand(final)};
  recognition.onerror=e=>{add("agent","Voice error: "+e.error);};
  recognition.onend=()=>{listening=false;orb.classList.remove("listening");mic.textContent="Hold / Click to Talk";if($("heroText").textContent==="Listening…")$("heroText").textContent="Speak a command"};
  $("lang").onchange=()=>{if(recognition)recognition.lang=$("lang").value}; mic.onclick=()=>{if(listening)recognition.stop();else {recognition.lang=$("lang").value;recognition.start()}};
}
init().then(setupVoice);
