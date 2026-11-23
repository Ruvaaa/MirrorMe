const state = {
  feed: [],
  feedIndex: 0,
  feedFilter: "All",
  journalEditing: null,
  preferences: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json().catch(() => ({ error: "The server returned an unreadable response." }));
  if (!response.ok) throw new Error(body.error || "Something went wrong.");
  return body;
}

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  clearTimeout(toast.timeout);
  toast.timeout = setTimeout(() => element.classList.remove("show"), 2400);
}

function escapeHtml(value) {
  const element = document.createElement("span");
  element.textContent = value;
  return element.innerHTML;
}

function setView(view) {
  $$(".view").forEach((element) => element.classList.remove("active"));
  $(`#view-${view}`).classList.add("active");
  $$(".nav-item").forEach((element) => element.classList.toggle("active", element.dataset.view === view));
  const names = {
    mirror: ["Your reflective companion", "Good evening"],
    journal: ["Private reflections", "My journal"],
    discover: ["Selected for your interests", "Discover"],
    growth: ["Patterns, not judgments", "Personal growth"],
    music: ["Mood and music", "Spotify Mood Sync"],
    settings: ["Your preferences", "Settings"],
  };
  $("#view-eyebrow").textContent = names[view][0];
  $("#view-title").textContent = names[view][1];
  if (view === "growth") loadDashboard();
  if (view === "journal") loadJournal();
  if (view === "discover") loadFeed();
  if (view === "settings") loadSettings();
  if (view === "music") loadSpotify();
}

$$("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));

async function sendChat(event) {
  event.preventEvent?.();
  event.preventDefault();
  const input = $("#chat-input");
  const message = input.value.trim();
  if (!message) return;
  appendMessage("user", message);
  input.value = "";
  const typing = appendMessage("bot", "Thinking…", true);
  $("#mirri-status").textContent = "Reflecting";
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, context: $("#chat-context").value }),
    });
    typing.remove();
    appendMessage("bot", data.response);
    $("#mood-estimate").textContent = `${capitalize(data.emotion)} · estimated ${Math.round(data.confidence * 100)}% confidence`;
    setMoodVisual(data.emotion);
    $$(".mood-options button").forEach((button) => button.classList.toggle("selected", button.dataset.mood === data.emotion));
  } catch (error) {
    typing.remove();
    appendMessage("bot", "I'm offline from the local response service. Your message is safe here, but Mirri couldn't answer it just now.");
    toast(error.message);
  } finally {
    $("#mirri-status").textContent = "Here with you";
  }
}

function appendMessage(type, text, typing = false) {
  const message = document.createElement("div");
  message.className = `message ${type}${typing ? " typing" : ""}`;
  message.innerHTML = `<span class="message-copy">${escapeHtml(text)}</span>`;
  const log = $("#chat-log");
  log.appendChild(message);
  log.scrollTop = log.scrollHeight;
  return message;
}

function capitalize(value) {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : "";
}

const moodImages = {
  happy: "happy.jpg",
  excited: "excited.jpg",
  sad: "sad.jpg",
  anxious: "anxious.jpg",
  angry: "angry.jpg",
  motivated: "motivated.jpg",
  neutral: "pic.jpg",
};

function setMoodVisual(emotion) {
  const image = $("#mood-image");
  const filename = moodImages[emotion] || moodImages.neutral;
  image.classList.add("changing");
  image.onload = () => image.classList.remove("changing");
  image.onerror = () => {
    image.onerror = null;
    image.src = "/pic.jpg";
    image.classList.remove("changing");
  };
  image.src = `/${filename}`;
  image.alt = `${capitalize(emotion in moodImages ? emotion : "neutral")} mood reflection artwork`;
}

$("#chat-form").addEventListener("submit", sendChat);

$$(".mood-options button").forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      await api("/api/moods", { method: "POST", body: JSON.stringify({ emotion: button.dataset.mood }) });
      $$(".mood-options button").forEach((item) => item.classList.remove("selected"));
      button.classList.add("selected");
      $("#mood-estimate").textContent = `${capitalize(button.dataset.mood)} · recorded from your check-in`;
      setMoodVisual(button.dataset.mood);
      toast("Mood recorded");
    } catch (error) {
      toast(error.message);
    }
  });
});
$("#open-mood").addEventListener("click", () => {
  $(".mood-options").scrollIntoView({ behavior: "smooth", block: "nearest" });
  $(".mood-options button").focus();
});

let timerInterval = null;
let remainingSeconds = 25 * 60;
function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}
function renderTimer() {
  $("#timer-display").textContent = formatTime(remainingSeconds);
}
$("#timer-start").addEventListener("click", async () => {
  if (timerInterval) return;
  try {
    await api("/start_timer", { method: "POST", body: JSON.stringify({ minutes: 25 }) });
  } catch (error) {
    toast(error.message);
  }
  timerInterval = setInterval(() => {
    remainingSeconds = Math.max(0, remainingSeconds - 1);
    renderTimer();
    if (!remainingSeconds) {
      clearInterval(timerInterval);
      timerInterval = null;
      toast("Focus session complete");
    }
  }, 1000);
});
$("#timer-stop").addEventListener("click", async () => {
  clearInterval(timerInterval);
  timerInterval = null;
  remainingSeconds = 25 * 60;
  renderTimer();
  try { await api("/stop_timer", { method: "POST", body: "{}" }); } catch (_) {}
});

const prompts = [
  "What feels different from when you began today?",
  "What is asking for more of your attention right now?",
  "What choice this week felt most true to you?",
  "What would make tomorrow feel slightly lighter?",
  "What did you learn about yourself today?",
];
let promptIndex = 0;
$("#new-prompt").addEventListener("click", () => {
  promptIndex = (promptIndex + 1) % prompts.length;
  $("#journal-prompt").textContent = prompts[promptIndex];
});
$("#new-entry").addEventListener("click", () => {
  state.journalEditing = null;
  $("#journal-title").value = "";
  $("#journal-body").value = "";
  $("#journal-mood").value = "neutral";
  $("#journal-title").focus();
});
$("#journal-search").addEventListener("input", () => loadJournal($("#journal-search").value));

async function loadJournal(query = "") {
  try {
    const entries = await api(`/api/journal${query ? `?q=${encodeURIComponent(query)}` : ""}`);
    const list = $("#journal-list");
    if (!entries.length) {
      list.innerHTML = '<div class="empty-state">No reflections here yet.</div>';
      return;
    }
    list.innerHTML = entries.map((entry) => `
      <button class="journal-item" type="button" data-id="${escapeHtml(entry.id)}">
        <strong>${escapeHtml(entry.title)}</strong>
        <span>${escapeHtml(entry.body)}</span>
      </button>`).join("");
    $$(".journal-item").forEach((button) => button.addEventListener("click", () => openJournalEntry(entries.find((item) => item.id === button.dataset.id))));
  } catch (error) {
    toast(error.message);
  }
}
function openJournalEntry(entry) {
  state.journalEditing = entry.id;
  $("#journal-title").value = entry.title;
  $("#journal-body").value = entry.body;
  $("#journal-mood").value = entry.mood || "neutral";
  $("#journal-body").focus();
}
$("#save-entry").addEventListener("click", async () => {
  const payload = { title: $("#journal-title").value, body: $("#journal-body").value, mood: $("#journal-mood").value };
  try {
    if (state.journalEditing) await api(`/api/journal/${state.journalEditing}`, { method: "PUT", body: JSON.stringify(payload) });
    else await api("/api/journal", { method: "POST", body: JSON.stringify(payload) });
    toast("Reflection saved privately");
    await loadJournal();
  } catch (error) {
    toast(error.message);
  }
});

async function loadFeed() {
  try {
    state.feed = await api("/api/feed");
    if (state.feedIndex >= state.feed.length) state.feedIndex = 0;
    renderFeed();
  } catch (error) {
    toast(error.message);
  }
}
function getVisibleFeed() {
 return state.feedFilter === "All"
   ? state.feed
   : state.feed.filter((item) => item.category === state.feedFilter);
}

function renderFeed() {
  const visibleFeed = getVisibleFeed();
  if (state.feedIndex >= visibleFeed.length) state.feedIndex = 0;
  const item = visibleFeed[state.feedIndex];
  if (!item) {
    $("#feed-category").textContent = "All clear";
    $("#feed-title").textContent = "You've reached the end";
    $("#feed-summary").textContent = "Take a breath or reset the categories in Settings.";
    $("#feed-source").textContent = "";
  } else {
    $("#feed-category").textContent = item.category;
    $("#feed-title").textContent = item.title;
    $("#feed-summary").textContent = item.summary;
    $("#feed-source").textContent = item.source;
  }
  $("#feed-position").textContent = `${visibleFeed.length ? state.feedIndex + 1 : 0} / ${visibleFeed.length}`;
  $("#feed-dots").innerHTML = visibleFeed.map((_, index) => `<i class="${index === state.feedIndex ? "active" : ""}"></i>`).join("");
  const categories = ["All", ...new Set(state.feed.map((item) => item.category))];
  $("#category-list").innerHTML = categories.map((category) => `<button class="category-chip ${category === state.feedFilter ? "active" : ""}" type="button">${escapeHtml(category)}</button>`).join("");
  $$(".category-chip").forEach((button) => button.addEventListener("click", () => {
    state.feedFilter = button.textContent;
    state.feedIndex = 0;
    $$(".category-chip").forEach((item) => item.classList.toggle("active", item === button));
    renderFeed();
  }));
}
async function feedAction(action) {
  const visibleFeed = getVisibleFeed();
  const item = visibleFeed[state.feedIndex];
  if (!item) return;
  try {
    await api("/api/feed/action", { method: "POST", body: JSON.stringify({ id: item.id, action }) });
    if (action === "save") toast("Saved to Growth");
    if (action === "like") toast("Preference noted");
    if (action === "dismiss") {
      const originalIndex = state.feed.findIndex((entry) => entry.id === item.id);
      if (originalIndex >= 0) state.feed.splice(originalIndex, 1);
      if (state.feedIndex >= getVisibleFeed().length) state.feedIndex = 0;
      renderFeed();
    }
  } catch (error) {
    toast(error.message);
  }
}
$("#feed-like").addEventListener("click", () => feedAction("like"));
$("#feed-save").addEventListener("click", () => feedAction("save"));
$("#feed-dismiss").addEventListener("click", () => feedAction("dismiss"));

function setFeedMode(mode) {
  const shorts = mode === "shorts";
  $("#curated-feed-content").hidden = shorts;
  $("#shorts-feed-content").hidden = !shorts;
  $("#curated-feed-mode").classList.toggle("active", !shorts);
  $("#shorts-feed-mode").classList.toggle("active", shorts);
  $("#feed-position").parentElement.hidden = shorts;
  if (shorts) {
    setTimeout(() => {
      const widget = $(".elfsight-app-b12c2b9d-2933-4eef-b331-b64f4c82741e");
      const hasWidgetContent = widget && widget.childElementCount > 0;
      $("#shorts-offline").style.display = hasWidgetContent ? "none" : "block";
    }, 2500);
  }
}
$("#curated-feed-mode").addEventListener("click", () => setFeedMode("curated"));
$("#shorts-feed-mode").addEventListener("click", () => setFeedMode("shorts"));
let discoverWheelLocked = false;
$("#feed-card").addEventListener("wheel", (event) => {
  if (discoverWheelLocked || Math.abs(event.deltaY) < 20) return;
  discoverWheelLocked = true;
  const length = getVisibleFeed().length;
  if (event.deltaY > 0) state.feedIndex = Math.min(length - 1, state.feedIndex + 1);
  else state.feedIndex = Math.max(0, state.feedIndex - 1);
  renderFeed();
  setTimeout(() => { discoverWheelLocked = false; }, 300);
});

async function loadDashboard() {
  try {
    const data = await api("/api/dashboard");
    $("#journal-count").textContent = data.journal_count;
    $("#journal-streak").textContent = data.journal_streak;
    const counts = data.mood_counts || {};
    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    const max = Math.max(1, ...entries.map(([, count]) => count));
    $("#mood-chart").innerHTML = entries.length ? entries.map(([name, count]) => `<div class="chart-bar" style="height:${Math.max(12, count / max * 100)}%" title="${count} check-ins"><span>${escapeHtml(name)}</span></div>`).join("") : '<div class="empty-state">Mood check-ins will appear here.</div>';
    $("#saved-list").innerHTML = data.saved_content.length ? data.saved_content.map((item) => `<div class="saved-item"><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.category)}</small></div>`).join("") : '<div class="empty-state">Save a discovery to keep it here.</div>';
  } catch (error) {
    toast(error.message);
  }
}

async function loadSpotify() {
  try {
    const status = await api("/api/spotify/status");
    $$(".mode-options button").forEach((button) => button.classList.toggle("selected", button.dataset.mode === status.mode));
    const moods = await api("/api/moods");
    const mood = moods.at(-1)?.emotion || "neutral";
    const recommendations = await api(`/api/spotify/recommendations?mood=${encodeURIComponent(mood)}`);
    $("#playlist-name").textContent = recommendations.playlist;
    $("#spotify-message").textContent = status.connected ? "Spotify is connected." : (status.configured ? "Spotify credentials are configured." : "Connect Spotify to control playback.");
    $("#spotify-connect").textContent = status.connected ? "Spotify connected" : "Connect Spotify";
  } catch (error) {
    toast(error.message);
  }
}
$$(".mode-options button").forEach((button) => button.addEventListener("click", async () => {
  $$(".mode-options button").forEach((item) => item.classList.remove("selected"));
  button.classList.add("selected");
  await savePreferences({ music_mode: button.dataset.mode });
  toast(button.dataset.mode === "match" ? "Music will match your mood" : "Music will aim to lift your mood");
}));
$("#spotify-connect").addEventListener("click", () => toast("Add Spotify credentials in the local environment to enable OAuth."));

async function loadSettings() {
  try {
    state.preferences = await api("/api/preferences");
    $("#setting-name").value = state.preferences.name || "Friend";
    $("#setting-theme").value = state.preferences.theme || "light";
    $("#setting-memory").checked = state.preferences.memory_enabled !== false;
    document.body.classList.toggle("dark", state.preferences.theme === "dark");
    $("#theme-toggle").textContent = state.preferences.theme === "dark" ? "☀" : "◐";
    $("#profile-name").textContent = state.preferences.name || "Friend";
    $("#profile-avatar").textContent = (state.preferences.name || "F").charAt(0).toUpperCase();
    await loadMemories();
  } catch (error) {
    toast(error.message);
  }
}
async function savePreferences(patch) {
  state.preferences = await api("/api/preferences", { method: "POST", body: JSON.stringify(patch) });
}
$("#settings-save").addEventListener("click", async () => {
  try {
    await savePreferences({
      name: $("#setting-name").value.trim() || "Friend",
      theme: $("#setting-theme").value,
      memory_enabled: $("#setting-memory").checked,
    });
    document.body.classList.toggle("dark", state.preferences.theme === "dark");
    $("#theme-toggle").textContent = state.preferences.theme === "dark" ? "☀" : "◐";
    $("#profile-name").textContent = state.preferences.name;
    $("#profile-avatar").textContent = state.preferences.name.charAt(0).toUpperCase();
    toast("Settings saved");
  } catch (error) {
    toast(error.message);
  }
});
$("#theme-toggle").addEventListener("click", async () => {
  const theme = document.body.classList.contains("dark") ? "light" : "dark";
  document.body.classList.toggle("dark", theme === "dark");
  $("#theme-toggle").textContent = theme === "dark" ? "☀" : "◐";
  try { await savePreferences({ theme }); } catch (error) { toast(error.message); }
});

async function loadMemories() {
  const memories = await api("/api/memories");
  $("#memory-list").innerHTML = memories.length ? memories.map((memory) => `<span class="memory-chip">${escapeHtml(memory.text)} <button type="button" data-delete-memory="${escapeHtml(memory.id)}" aria-label="Delete memory">×</button></span>`).join("") : '<span class="empty-state">No saved memories</span>';
  $$("[data-delete-memory]").forEach((button) => button.addEventListener("click", async () => {
    await api(`/api/memories/${encodeURIComponent(button.dataset.deleteMemory)}`, { method: "DELETE" });
    await loadMemories();
  }));
}
$("#memory-save").addEventListener("click", async () => {
  const input = $("#memory-input");
  if (!input.value.trim()) return;
  try {
    await api("/api/memories", { method: "POST", body: JSON.stringify({ memory: input.value.trim() }) });
    input.value = "";
    await loadMemories();
    toast("Memory saved");
  } catch (error) {
    toast(error.message);
  }
});

async function initialize() {
  try {
    const preferences = await api("/api/preferences");
    state.preferences = preferences;
    document.body.classList.toggle("dark", preferences.theme === "dark");
    $("#theme-toggle").textContent = preferences.theme === "dark" ? "☀" : "◐";
    $("#profile-name").textContent = preferences.name || "Friend";
    $("#profile-avatar").textContent = (preferences.name || "F").charAt(0).toUpperCase();
    const moods = await api("/api/moods");
    const lastMood = moods.at(-1);
    if (lastMood) {
      setMoodVisual(lastMood.emotion);
      $("#mood-estimate").textContent = lastMood.source === "manual"
        ? `${capitalize(lastMood.emotion)} · recorded from your check-in`
        : `${capitalize(lastMood.emotion)} · estimated ${Math.round(lastMood.confidence * 100)}% confidence`;
      $$(".mood-options button").forEach((button) => button.classList.toggle("selected", button.dataset.mood === lastMood.emotion));
    }
  } catch (_) {
    toast("Running in offline interface mode");
  }
  await loadFeed();
}

initialize();
