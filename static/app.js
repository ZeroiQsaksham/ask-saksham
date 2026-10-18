// Chat widget: sends the question + recent history to /api/chat and renders the streamed answer.
const chat = document.getElementById("chat");
const body = document.getElementById("chat-body");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const suggestions = document.getElementById("suggestions");
const launcher = document.getElementById("chat-launcher");

const history = []; // conversation memory sent with each request
let agentName = "XYZ";
let busy = false;

fetch("/api/config")
  .then((r) => r.json())
  .then((cfg) => {
    agentName = cfg.agent_name;
    document.querySelectorAll(".agent-name").forEach((el) => (el.textContent = agentName));
  })
  .catch(() => {});

function openChat() {
  chat.hidden = false;
  launcher.hidden = true;
  if (!body.children.length) {
    addMessage("bot", `Hi! I'm ${agentName}, Saksham's AI assistant. Ask me about his skills, projects, education or how to reach him.`);
  }
  input.focus();
}
function closeChat() {
  chat.hidden = true;
  launcher.hidden = false;
}
launcher.addEventListener("click", openChat);
document.getElementById("open-chat-hero").addEventListener("click", openChat);
document.getElementById("chat-close").addEventListener("click", closeChat);

function addMessage(role, text) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  el.textContent = text; // textContent, never innerHTML: no HTML injection from model output
  body.appendChild(el);
  body.scrollTop = body.scrollHeight;
  return el;
}

async function ask(question) {
  if (busy || !question.trim()) return;
  busy = true;
  suggestions.hidden = true;
  form.querySelector("button").disabled = true;

  addMessage("user", question);
  const botEl = addMessage("bot", "");
  botEl.classList.add("typing");

  let answer = "";
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history: history.slice(-10) }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${res.status})`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      answer += decoder.decode(value, { stream: true });
      botEl.textContent = answer;
      body.scrollTop = body.scrollHeight;
    }
  } catch (e) {
    answer = typeof e.message === "string" ? e.message : "Something went wrong. Please try again.";
    botEl.textContent = answer;
  } finally {
    botEl.classList.remove("typing");
    history.push({ role: "user", content: question }, { role: "assistant", content: answer });
    busy = false;
    form.querySelector("button").disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value;
  input.value = "";
  ask(q);
});
suggestions.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => ask(b.textContent)));
