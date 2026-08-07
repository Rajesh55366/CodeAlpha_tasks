const log = document.getElementById("log");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const chipsEl = document.getElementById("chips");

function scrollToBottom() {
  log.scrollTop = log.scrollHeight;
}

function addUserMessage(text) {
  const el = document.createElement("div");
  el.className = "msg user";
  el.innerHTML = `<div class="bubble"></div>`;
  el.querySelector(".bubble").textContent = text;
  log.appendChild(el);
  scrollToBottom();
}

function gaugeSVG(pct) {
  // Semi-circle gauge, needle rotates from -90deg (0%) to +90deg (100%)
  const angle = -90 + (pct / 100) * 180;
  return `
  <svg class="gauge" viewBox="0 0 60 34" width="42" height="24" aria-hidden="true">
    <path d="M4 30 A26 26 0 0 1 56 30" fill="none" stroke="#3a434b" stroke-width="5" stroke-linecap="round"/>
    <path d="M4 30 A26 26 0 0 1 56 30" fill="none" stroke="${pct >= 60 ? '#6bcf7f' : pct >= 30 ? '#ff5a1f' : '#c94f3a'}"
          stroke-width="5" stroke-linecap="round"
          stroke-dasharray="${(pct/100) * 81.6} 200"/>
    <line x1="30" y1="30" x2="${30 + 20 * Math.cos((angle * Math.PI) / 180)}"
          y2="${30 + 20 * Math.sin((angle * Math.PI) / 180)}"
          stroke="#f3f1ec" stroke-width="2" stroke-linecap="round"/>
    <circle cx="30" cy="30" r="2.5" fill="#f3f1ec"/>
  </svg>`;
}

function addBotMessage(result) {
  const el = document.createElement("div");
  el.className = "msg bot";

  let metaHTML;
  if (result.source === "ai") {
    metaHTML = `<span class="gauge-label">🤖 <span class="gauge-pct">AI</span> · not from the FAQ list</span>`;
  } else {
    const pct = Math.round(result.confidence * 100);
    const matchedLine = result.matched_question
      ? `Matched: “${result.matched_question}”`
      : "No confident match";
    metaHTML = `${gaugeSVG(pct)}<span class="gauge-label">MATCH <span class="gauge-pct">${pct}%</span> · ${matchedLine}</span>`;
  }

  el.innerHTML = `
    <div class="bubble">
      ${result.answer}
      <div class="bot-meta">${metaHTML}</div>
    </div>`;
  log.appendChild(el);
  scrollToBottom();
}

function addTyping() {
  const el = document.createElement("div");
  el.className = "msg bot typing";
  el.innerHTML = `<div class="bubble">thinking…</div>`;
  el.id = "typing-indicator";
  log.appendChild(el);
  scrollToBottom();
}

function removeTyping() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

async function sendMessage(text) {
  addUserMessage(text);
  addTyping();
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    removeTyping();
    addBotMessage(data);
  } catch (err) {
    removeTyping();
    addBotMessage({
      answer: "Couldn't reach the help desk server. Is the Flask app running?",
      confidence: 0,
      matched_question: null,
    });
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendMessage(text);
});

async function loadChips() {
  try {
    const res = await fetch("/api/faqs");
    const faqs = await res.json();
    const sample = faqs
      .map((f) => f.question)
      .sort(() => Math.random() - 0.5)
      .slice(0, 4);
    chipsEl.innerHTML = "";
    sample.forEach((q) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "chip";
      chip.textContent = q;
      chip.addEventListener("click", () => sendMessage(q));
      chipsEl.appendChild(chip);
    });
  } catch (err) {
    // silently skip suggestion chips if the API isn't reachable
  }
}

loadChips();
