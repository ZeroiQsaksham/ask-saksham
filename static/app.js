// Chat widget with two modes:
//   "about" - AI version of Saksham (answers from knowledge/*.md)
//   "astro" - Astrologer mode (answers from the astrology book, with chapter/page citations)
const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const launcher = document.getElementById("chat-launcher");
const sendBtn = form.querySelector("button");
const titleEl = document.getElementById("chat-title");
const subEl = document.getElementById("chat-sub");
const noteEl = document.getElementById("chat-note");
const tabs = document.querySelectorAll(".mode-tab");

const MODES = {
  about: {
    title: "Saksham",
    sub: "AI version of me · ask me anything",
    note: "",
    placeholder: "Ask about my education, projects, skills...",
    greeting: "Hi! I'm the AI version of Saksham. Ask me about my education, projects, skills, internship or how to reach me.",
    suggestions: ["What are your skills?", "Tell me about your projects", "How can I contact you?"],
  },
  astro: {
    title: "Ask Saksham (Astrologer)",
    sub: "Vedic astrology, answered from one book",
    note: "Answers come only from the book, with chapter and page references. For learning and reflection, not professional advice.",
    placeholder: "Ask about rasis, houses, dasas, yogas...",
    greeting:
      "Namaste! I'm the astrologer mode of Ask Saksham. I answer Vedic astrology questions strictly from the book " +
      "**Vedic Astrology: An Integrated Approach** by P.V.R. Narasimha Rao, and tell you the chapter and page each answer comes from.",
    suggestions: ["What is Vimsottari dasa?", "What is Gaja Kesari yoga?", "What does the arudha lagna show?"],
  },
};

const state = {
  mode: "about",
  busy: false,
  history: { about: [], astro: [] },
  bodies: { about: document.getElementById("chat-body-about"), astro: document.getElementById("chat-body-astro") },
  suggestions: {
    about: document.getElementById("suggestions-about"),
    astro: document.getElementById("suggestions-astro"),
  },
};

fetch("/api/config")
  .then((r) => r.json())
  .then((cfg) => {
    if (cfg.agent_name) MODES.about.title = cfg.agent_name;
    if (cfg.astro_name) MODES.astro.title = cfg.astro_name;
    if (!cfg.astro_enabled) {
      document.querySelectorAll("[data-astro]").forEach((el) => (el.hidden = true));
    }
    applyMode(state.mode);
  })
  .catch(() => {});

// ---------- rendering ----------
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// Minimal, safe Markdown: text is HTML-escaped FIRST, then only bold, bullets, links and citations are added.
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
      // Book citations like (Chapter 16: Vimsottari Dasa, p. 210) become small badges
      l = l.replace(/[([]((?:Chapter|Ch\.|Front matter)[^()[\]]*?p{1,2}\.\s*(?:front )?[\d\-–, ]+)[)\]]/g, '<span class="cite">$1</span>');
      return /^\s*[-*•] /.test(line) ? "• " + l.replace(/^\s*[-*•] /, "") : l;
    })
    .join("<br>");
}

function setMessage(el, role, text) {
  if (role === "bot") el.innerHTML = renderMarkdown(text);
  else el.textContent = text; // user text is never interpreted as HTML
}

function addMessage(mode, role, text) {
  const body = state.bodies[mode];
  const el = document.createElement("div");
  el.className = `msg ${role}`;
  setMessage(el, role, text);
  body.appendChild(el);
  body.scrollTop = body.scrollHeight;
  return el;
}

// ---------- modes ----------
function applyMode(mode) {
  state.mode = mode;
  const m = MODES[mode];
  chat.classList.toggle("astro", mode === "astro");
  titleEl.textContent = m.title;
  subEl.textContent = m.sub;
  noteEl.textContent = m.note;
  noteEl.hidden = !m.note;
  input.placeholder = m.placeholder;
  tabs.forEach((t) => t.setAttribute("aria-selected", String(t.dataset.mode === mode)));
  for (const k of Object.keys(state.bodies)) {
    state.bodies[k].hidden = k !== mode;
    state.suggestions[k].hidden = k !== mode || state.history[k].length > 0;
  }
  if (!state.bodies[mode].children.length) addMessage(mode, "bot", m.greeting);
}

function buildSuggestions() {
  for (const [mode, box] of Object.entries(state.suggestions)) {
    box.innerHTML = "";
    for (const q of MODES[mode].suggestions) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = q;
      b.addEventListener("click", () => ask(q));
      box.appendChild(b);
    }
  }
}

function openChat(mode = state.mode) {
  chat.hidden = false;
  launcher.hidden = true;
  applyMode(mode);
  input.focus();
}
function closeChat() {
  chat.hidden = true;
  launcher.hidden = false;
}

launcher.addEventListener("click", () => openChat());
document.getElementById("chat-close").addEventListener("click", closeChat);
document.querySelectorAll("[data-open-chat]").forEach((b) => b.addEventListener("click", () => openChat(b.dataset.openChat)));
tabs.forEach((t) => t.addEventListener("click", () => !state.busy && applyMode(t.dataset.mode)));

// ---------- asking ----------
async function ask(question) {
  if (state.busy || !question.trim()) return;
  const mode = state.mode;
  state.busy = true;
  state.suggestions[mode].hidden = true;
  sendBtn.disabled = true;

  addMessage(mode, "user", question);
  const botEl = addMessage(mode, "bot", "");
  botEl.classList.add("typing");
  const body = state.bodies[mode];

  let answer = "";
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history: state.history[mode].slice(-10), mode }),
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
    state.history[mode].push({ role: "user", content: question }, { role: "assistant", content: answer });
    state.busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value;
  input.value = "";
  ask(q);
});

buildSuggestions();
applyMode("about");
