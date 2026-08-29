// --- Tema (claro/escuro) ---
const THEME_KEY = "estude-ingles-theme";

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  document.querySelectorAll(".theme-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.theme === theme);
  });
}

document.querySelectorAll(".theme-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    localStorage.setItem(THEME_KEY, btn.dataset.theme);
    applyTheme(btn.dataset.theme);
  });
});

(function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  const preferred = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  applyTheme(saved || preferred);
})();

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
const wordFormTitle = document.getElementById("word-form-title");
const wordFormSubmit = document.getElementById("word-form-submit");
const wordFormCancel = document.getElementById("word-form-cancel");
const wordFormMsg = document.getElementById("word-form-msg");
const wordInput = document.getElementById("word-input");
const translationInput = document.getElementById("translation-input");
const exampleInput = document.getElementById("example-input");
const wordsTbody = document.getElementById("words-tbody");
const wordsEmpty = document.getElementById("words-empty");
const wordsTitle = document.getElementById("words-title");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchClear = document.getElementById("search-clear");

let wordsCache = [];
let editingId = null;

async function loadWordCount() {
  const statEl = document.getElementById("stat-word-count");
  if (!statEl) return;
  const res = await fetch("/api/words/count");
  const data = await res.json();
  statEl.textContent = data.total;
}

function enterEditMode(w) {
  editingId = w.id;
  wordFormTitle.textContent = "Editar palavra";
  wordFormSubmit.textContent = "Salvar alterações";
  wordFormCancel.hidden = false;
  wordInput.value = w.word;
  translationInput.value = w.translation;
  exampleInput.value = w.example_sentence || "";
  wordInput.focus();
}

function exitEditMode() {
  editingId = null;
  wordFormTitle.textContent = "Adicionar palavra";
  wordFormSubmit.textContent = "Adicionar";
  wordFormCancel.hidden = true;
  wordForm.reset();
}

wordFormCancel.addEventListener("click", exitEditMode);

async function loadWords(query) {
  const url = query ? `/api/words?q=${encodeURIComponent(query)}` : "/api/words";
  const res = await fetch(url);
  const words = await res.json();
  wordsCache = words;
  wordsTbody.innerHTML = "";
  wordsEmpty.hidden = words.length > 0;

  wordsTitle.textContent = query ? `Resultados para "${query}"` : "Últimas palavras cadastradas";
  searchClear.hidden = !query;

  for (const w of words) {
    const tr = document.createElement("tr");

    const audioCell = w.audio_filename
      ? `<audio controls src="/audio/${w.audio_filename}"></audio>`
      : "—";

    let exampleCell = escapeHtml(w.example_sentence || "");
    if (w.example_sentence) {
      if (w.example_audio_filename) {
        exampleCell += `<audio controls src="/audio/${w.example_audio_filename}"></audio>`;
        if (w.example_audio_source === "edge-tts") {
          exampleCell +=
            '<span class="audio-source-note">voz padrão (IA indisponível no momento — tente regerar depois)</span>';
        }
      }
      exampleCell += `<button class="ai-audio-btn" data-id="${w.id}" title="Gera um áudio mais humanizado da frase via OmniVoice (serviço externo, pode ser lento); se falhar, usa a voz padrão automaticamente">${
        w.example_audio_filename ? "Regerar áudio IA" : "Gerar áudio IA"
      }</button>`;
    }

    tr.innerHTML = `
      <td>${escapeHtml(w.word)}</td>
      <td>${escapeHtml(w.translation)}</td>
      <td>${exampleCell}</td>
      <td>${audioCell}</td>
      <td class="actions-cell">
        <button class="edit-btn" data-id="${w.id}">Editar</button>
        <button class="delete-btn" data-id="${w.id}">Excluir</button>
      </td>
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
  if (e.target.classList.contains("edit-btn")) {
    const id = Number(e.target.dataset.id);
    const w = wordsCache.find((item) => item.id === id);
    if (w) enterEditMode(w);
    return;
  }

  if (e.target.classList.contains("delete-btn")) {
    const id = Number(e.target.dataset.id);
    await fetch(`/api/words/${id}`, { method: "DELETE" });
    if (editingId === id) exitEditMode();
    loadWords(searchInput.value.trim());
    loadWordCount();
    return;
  }

  if (e.target.classList.contains("ai-audio-btn")) {
    const id = Number(e.target.dataset.id);
    const btn = e.target;
    btn.disabled = true;
    btn.textContent = "Gerando (pode levar até 1 min)...";
    try {
      const res = await fetch(`/api/words/${id}/example-audio`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Erro ao gerar áudio humanizado.");
      }
    } catch (err) {
      alert("Erro de conexão ao gerar áudio humanizado.");
    } finally {
      loadWords(searchInput.value.trim());
    }
  }
});

wordForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const word = wordInput.value.trim();
  const translation = translationInput.value.trim();
  const example_sentence = exampleInput.value.trim() || null;
  const isEditing = editingId !== null;

  wordFormMsg.textContent = "Salvando (gerando áudio se necessário)...";
  const res = await fetch(isEditing ? `/api/words/${editingId}` : "/api/words", {
    method: isEditing ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ word, translation, example_sentence }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    wordFormMsg.textContent = err.detail || "Erro ao salvar a palavra.";
    return;
  }

  wordFormMsg.textContent = isEditing ? "Alterações salvas!" : "Palavra salva!";
  exitEditMode();
  loadWords(searchInput.value.trim());
  loadWordCount();
  setTimeout(() => (wordFormMsg.textContent = ""), 2000);
});

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  loadWords(searchInput.value.trim());
});

searchClear.addEventListener("click", () => {
  searchInput.value = "";
  loadWords();
});

// --- Treinamento: Ouvir e digitar ---
const listenAudio = document.getElementById("listen-audio");
const listenForm = document.getElementById("listen-form");
const listenInput = document.getElementById("listen-input");
const listenFeedback = document.getElementById("listen-feedback");
const listenNext = document.getElementById("listen-next");
let currentListenId = null;
let listenSolved = false;
let listenCountdownId = null;

function clearListenCountdown() {
  if (listenCountdownId !== null) {
    clearInterval(listenCountdownId);
    listenCountdownId = null;
  }
}

async function loadListenChallenge() {
  clearListenCountdown();
  listenSolved = false;
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
  listenAudio.play().catch(() => {
    // Autoplay pode ser bloqueado pelo navegador; o usuário ainda pode
    // dar play manualmente pelo controle do áudio.
  });
}

listenForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (currentListenId === null || listenSolved) return;

  const res = await fetch("/api/training/listen-and-type/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: currentListenId, answer: listenInput.value }),
  });
  const data = await res.json();
  if (data.correct) {
    listenSolved = true;
    listenFeedback.className = "feedback correct";
    let secondsLeft = 3;
    listenFeedback.textContent = `Correto! Indo para a próxima em ${secondsLeft} segundos...`;
    listenCountdownId = setInterval(() => {
      secondsLeft -= 1;
      if (secondsLeft <= 0) {
        clearListenCountdown();
        loadListenChallenge();
        return;
      }
      listenFeedback.textContent = `Correto! Indo para a próxima em ${secondsLeft} segundos...`;
    }, 1000);
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
loadWordCount();
