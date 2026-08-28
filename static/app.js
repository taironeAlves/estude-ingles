// --- Navegação lateral ---
function switchView(view) {
  document.querySelectorAll(".nav-item[data-view]").forEach((b) => {
    b.classList.toggle("active", b.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.getElementById(`view-${view}`).classList.add("active");

  if (view === "listen-type" && currentListenId === null) loadListenChallenge();
  if (view === "fill-blank" && currentFillId === null) loadFillChallenge();
}

document.querySelectorAll(".nav-item[data-view]").forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.view));
});

document.querySelectorAll("[data-goto]").forEach((btn) => {
  btn.addEventListener("click", () => switchView(btn.dataset.goto));
});

// --- Dicionário ---
const wordForm = document.getElementById("word-form");
const wordFormMsg = document.getElementById("word-form-msg");
const wordsTbody = document.getElementById("words-tbody");
const wordsEmpty = document.getElementById("words-empty");
const searchInput = document.getElementById("search-input");

async function loadWords(query) {
  const url = query ? `/api/words?q=${encodeURIComponent(query)}` : "/api/words";
  const res = await fetch(url);
  const words = await res.json();
  wordsTbody.innerHTML = "";
  wordsEmpty.hidden = words.length > 0;

  const statEl = document.getElementById("stat-word-count");
  if (statEl && !query) statEl.textContent = words.length;

  for (const w of words) {
    const tr = document.createElement("tr");

    const audioCell = w.audio_filename
      ? `<audio controls src="/audio/${w.audio_filename}"></audio>`
      : "—";

    tr.innerHTML = `
      <td>${escapeHtml(w.word)}</td>
      <td>${escapeHtml(w.translation)}</td>
      <td>${escapeHtml(w.example_sentence || "")}</td>
      <td>${audioCell}</td>
      <td><button class="delete-btn" data-id="${w.id}">Excluir</button></td>
    `;
    wordsTbody.appendChild(tr);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

wordsTbody.addEventListener("click", async (e) => {
  if (!e.target.classList.contains("delete-btn")) return;
  const id = e.target.dataset.id;
  await fetch(`/api/words/${id}`, { method: "DELETE" });
  loadWords(searchInput.value.trim());
});

wordForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const word = document.getElementById("word-input").value.trim();
  const translation = document.getElementById("translation-input").value.trim();
  const example_sentence = document.getElementById("example-input").value.trim() || null;

  wordFormMsg.textContent = "Salvando (gerando áudio se necessário)...";
  const res = await fetch("/api/words", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ word, translation, example_sentence }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    wordFormMsg.textContent = err.detail || "Erro ao salvar a palavra.";
    return;
  }

  wordFormMsg.textContent = "Palavra salva!";
  wordForm.reset();
  loadWords(searchInput.value.trim());
  setTimeout(() => (wordFormMsg.textContent = ""), 2000);
});

let searchTimeout;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => loadWords(searchInput.value.trim()), 250);
});

// --- Treinamento: Ouvir e digitar ---
const listenAudio = document.getElementById("listen-audio");
const listenForm = document.getElementById("listen-form");
const listenInput = document.getElementById("listen-input");
const listenFeedback = document.getElementById("listen-feedback");
const listenNext = document.getElementById("listen-next");
let currentListenId = null;

async function loadListenChallenge() {
  listenFeedback.textContent = "";
  listenFeedback.className = "feedback";
  listenInput.value = "";
  const res = await fetch("/api/training/listen-and-type");
  if (!res.ok) {
    listenFeedback.textContent = "Cadastre palavras com áudio para treinar.";
    listenAudio.removeAttribute("src");
    return;
  }
  const data = await res.json();
  currentListenId = data.id;
  listenAudio.src = data.audio_url;
}

listenForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (currentListenId === null) return;
  const res = await fetch("/api/training/listen-and-type/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: currentListenId, answer: listenInput.value }),
  });
  const data = await res.json();
  if (data.correct) {
    listenFeedback.textContent = "Correto!";
    listenFeedback.className = "feedback correct";
  } else {
    listenFeedback.textContent = `Errado. Resposta certa: ${data.word} (${data.translation})`;
    listenFeedback.className = "feedback wrong";
  }
});

listenNext.addEventListener("click", loadListenChallenge);

// --- Treinamento: Complete a frase ---
const fillSentence = document.getElementById("fill-sentence");
const fillForm = document.getElementById("fill-form");
const fillInput = document.getElementById("fill-input");
const fillFeedback = document.getElementById("fill-feedback");
const fillNext = document.getElementById("fill-next");
let currentFillId = null;

async function loadFillChallenge() {
  fillFeedback.textContent = "";
  fillFeedback.className = "feedback";
  fillInput.value = "";
  const res = await fetch("/api/training/fill-blank");
  if (!res.ok) {
    fillSentence.textContent = "Cadastre palavras com frase de exemplo para treinar.";
    currentFillId = null;
    return;
  }
  const data = await res.json();
  currentFillId = data.id;
  fillSentence.textContent = data.sentence;
}

fillForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (currentFillId === null) return;
  const res = await fetch("/api/training/fill-blank/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: currentFillId, answer: fillInput.value }),
  });
  const data = await res.json();
  if (data.correct) {
    fillFeedback.textContent = "Correto!";
    fillFeedback.className = "feedback correct";
  } else {
    fillFeedback.textContent = `Errado. Resposta certa: ${data.word} (${data.translation})`;
    fillFeedback.className = "feedback wrong";
  }
});

fillNext.addEventListener("click", loadFillChallenge);

// --- Init ---
// A tela inicial é a de boas-vindas; os treinamentos carregam sob demanda
// quando o usuário abre cada um pela primeira vez (ver switchView).
loadWords();
