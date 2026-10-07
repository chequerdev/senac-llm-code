const form = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#sendButton");
const clearButton = document.querySelector("#clearButton");

let sessionId = crypto.randomUUID();
let busy = false;

function addMessage(text, role, isError = false) {
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "user-message" : "bot-message"}`;
  if (isError) article.classList.add("error-message");

  if (role !== "user") {
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "C";
    article.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  bubble.appendChild(paragraph);
  article.appendChild(bubble);
  messages.appendChild(article);
  scrollToBottom();
  return article;
}

function addTypingIndicator() {
  const article = document.createElement("article");
  article.className = "message bot-message";
  article.innerHTML = `
    <div class="avatar" aria-hidden="true">C</div>
    <div class="bubble"><div class="typing" aria-label="Chatão está digitando"><span></span><span></span><span></span></div></div>
  `;
  messages.appendChild(article);
  scrollToBottom();
  return article;
}

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
}

async function sendMessage(event) {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || busy) return;

  addMessage(text, "user");
  input.value = "";
  resizeInput();
  busy = true;
  sendButton.disabled = true;
  const typing = addTypingIndicator();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    const data = await response.json();
    typing.remove();
    if (!response.ok) throw new Error(data.error || "Não foi possível enviar a mensagem.");
    sessionId = data.session_id;
    addMessage(data.answer, "assistant");
  } catch (error) {
    typing.remove();
    addMessage(error.message, "assistant", true);
  } finally {
    busy = false;
    sendButton.disabled = false;
    input.focus();
  }
}

async function clearConversation() {
  if (busy) return;
  await fetch("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  }).catch(() => {});
  sessionId = crypto.randomUUID();
  messages.innerHTML = "";
  addMessage("Conversa zerada. O Chatão esqueceu tudo — uma habilidade invejável em certas segundas-feiras.", "assistant");
  input.focus();
}

form.addEventListener("submit", sendMessage);
clearButton.addEventListener("click", clearConversation);
input.addEventListener("input", resizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

input.focus();
