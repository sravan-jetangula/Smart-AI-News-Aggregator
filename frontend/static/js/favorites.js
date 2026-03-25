/**
 * favorites.js — Favorites page logic
 */

const API = "";
let activeBroadcastId = null;
let broadcastModal, toastEl;

document.addEventListener("DOMContentLoaded", () => {
  broadcastModal = new bootstrap.Modal(document.getElementById("broadcastModal"));
  toastEl = new bootstrap.Toast(document.getElementById("liveToast"), { delay: 3000 });
  loadFavorites();
});

async function loadFavorites() {
  try {
    const res  = await fetch(`${API}/api/favorites/`);
    const data = await res.json();

    document.getElementById("loadingState").style.display = "none";

    if (!data.articles || data.articles.length === 0) {
      document.getElementById("emptyState").classList.remove("d-none");
      return;
    }

    const grid = document.getElementById("favoritesGrid");
    grid.innerHTML = data.articles.map(buildCard).join("");

  } catch (err) {
    document.getElementById("loadingState").innerHTML =
      `<p class="text-danger">Failed to load favorites. Is the backend running?</p>`;
  }
}

function buildCard(a) {
  const date = a.published_at
    ? new Date(a.published_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    : "Unknown date";

  const summary  = a.ai_summary || a.summary || "No summary available.";
  const summaryLabel = a.ai_summary ? "AI Summary" : "Summary";
  const aiClass  = a.ai_summary ? "ai-summary-box" : "card-summary";

  return `
    <div class="news-card" id="card-${a.id}">
      <div class="card-source-row">
        <span class="source-badge">${escHtml(a.source || "Unknown")}</span>
        <span class="card-date"><i class="far fa-clock me-1"></i>${date}</span>
      </div>

      <div class="card-title">
        <a href="${escHtml(a.url)}" target="_blank" rel="noopener">${escHtml(a.title)}</a>
      </div>

      <div class="${aiClass}">
        ${a.ai_summary ? `<strong><i class="fas fa-robot me-1"></i>${summaryLabel}</strong>` : ""}
        ${escHtml(summary)}
      </div>

      <div class="card-actions">
        <button class="action-btn fav-btn favorited" onclick="removeFavorite(${a.id})">
          <i class="fas fa-star"></i>Remove
        </button>
        <button class="action-btn broadcast-btn" onclick="openBroadcast(${a.id}, '${escHtml(a.title.replace(/'/g, "\\'"))}')">
          <i class="fas fa-satellite-dish"></i>Broadcast
        </button>
        <a href="${escHtml(a.url)}" target="_blank" class="action-btn" style="text-decoration:none;">
          <i class="fas fa-external-link-alt"></i>Read
        </a>
      </div>
    </div>`;
}

async function removeFavorite(id) {
  try {
    await fetch(`${API}/api/favorites/${id}`, { method: "DELETE" });
    const card = document.getElementById(`card-${id}`);
    card.style.opacity = "0";
    card.style.transform = "scale(0.95)";
    card.style.transition = "all 0.3s ease";
    setTimeout(() => { card.remove(); checkEmpty(); }, 300);
    showToast("Removed from favorites", "success");
  } catch (err) {
    showToast("Failed to remove.", "danger");
  }
}

function checkEmpty() {
  const grid = document.getElementById("favoritesGrid");
  if (!grid.children.length) {
    document.getElementById("emptyState").classList.remove("d-none");
  }
}

function openBroadcast(id, title) {
  activeBroadcastId = id;
  document.getElementById("modalArticleTitle").textContent = title;
  document.getElementById("broadcastResult").classList.add("d-none");
  broadcastModal.show();
}

async function doBroadcast(platform) {
  if (!activeBroadcastId) return;
  const resultBox = document.getElementById("broadcastResult");

  try {
    const res = await fetch(`${API}/api/broadcast/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ article_id: activeBroadcastId, platform })
    });
    const data = await res.json();
    resultBox.innerHTML = `<i class="fas fa-check-circle me-2"></i>${data.message}<br>
      <small class="d-block mt-1 opacity-75">${data.note}</small>`;
    resultBox.classList.remove("d-none");
    showToast(`Broadcast simulated on ${platform} ✅`, "success");
  } catch {
    resultBox.innerHTML = `<span class="text-danger">Broadcast failed.</span>`;
    resultBox.classList.remove("d-none");
  }
}

function showToast(msg, type) {
  const el = document.getElementById("liveToast");
  el.className = `toast align-items-center text-white border-0 bg-${type === "success" ? "success" : "danger"}`;
  document.getElementById("toastMsg").textContent = msg;
  toastEl.show();
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
