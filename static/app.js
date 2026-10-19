// Chat widget: sends the question + recent history to /api/chat and renders the streamed answer.
const chat = document.getElementById("chat");
const body = document.getElementById("chat-body");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const suggestions = document.getElementById("suggestions");
const launcher = document.getElementById("chat-launcher");

const history = []; // conversation memory sent with each request
let agentName = "Saksham";
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
    addMessage("bot", `Hi! I'm the AI version of ${agentName}. Ask me about my education, projects, skills, internship or how to reach me.`);
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

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Minimal, safe Markdown: text is HTML-escaped FIRST, then only bold, bullets and links are added.
function renderMarkdown(text) {
  const cleaned = text.replace(/【[^】]*】/g, "").replace(/\[source:[^\]]*\]/gi, "");
  return escapeHtml(cleaned)
    .split("\n")
    .map((line) => {
      let l = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      l = l.replace(/https?:\/\/[^\s<)]+/g, (url) => {
        const trail = url.match(/[.,;:!?]+$/)?.[0] || "";
        const href = url.slice(0, url.length - trail.length);
        return `<a href="${href}" target="_blank" rel="noopener">${href}</a>${trail}`;
      });
      return /^\s*[-*•] /.test(line) ? "• " + l.replace(/^\s*[-*•] /, "") : l;
    })
    .join("<br>");
}

function setMessage(el, role, text) {
  if (role === "bot") el.innerHTML = renderMarkdown(text);
  else el.textContent = text; // user text is never interpreted as HTML
}

function addMessage(role, text) {
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  setMessage(el, role, text);
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
      setMessage(botEl, "bot", answer);
      body.scrollTop = body.scrollHeight;
    }
  } catch (e) {
    answer = typeof e.message === "string" ? e.message : "Something went wrong. Please try again.";
    setMessage(botEl, "bot", answer);
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
