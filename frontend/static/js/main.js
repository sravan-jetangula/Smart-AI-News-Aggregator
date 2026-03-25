/**
 * main.js — News Feed page logic
 *
 * Handles:
 *  - Fetching and rendering news articles with pagination
 *  - Favoriting/unfavoriting articles
 *  - Opening the broadcast modal and submitting broadcasts
 *  - Opening the AI enrich modal and calling the enrich endpoint
 *  - Source filtering
 */

const API = "";         // Same origin
let currentPage = 1;
let currentSource = "";
let totalArticles = 0;
const PAGE_SIZE = 20;

// Currently selected article for broadcast modal
let activeBroadcastId = null;

// ─────────────────────────────────────────────
// Bootstrap instances
// ─────────────────────────────────────────────
let broadcastModal, enrichModal, toastEl;

document.addEventListener("DOMContentLoaded", () => {
  broadcastModal = new bootstrap.Modal(document.getElementById("broadcastModal"));
  enrichModal    = new bootstrap.Modal(document.getElementById("enrichModal"));
  toastEl        = new bootstrap.Toast(document.getElementById("liveToast"), { delay: 3000 });
  loadNews();
});

// ─────────────────────────────────────────────
// Load news articles from API
// ─────────────────────────────────────────────
async function loadNews() {
  showLoading(true);

  try {
    const params = new URLSearchParams({ page: currentPage, limit: PAGE_SIZE });
    if (currentSource) params.append("source", currentSource);

    const res  = await fetch(`${API}/api/news/?${params}`);
    const data = await res.json();

    totalArticles = data.total;
    renderGrid(data.articles);
    updatePagination(data.total, currentPage);
    document.querySelector("#totalStat span").textContent = data.total;

  } catch (err) {
    showToast("Failed to load news. Is the backend running?", "danger");
    console.error(err);
  } finally {
    showLoading(false);
  }
}

// ─────────────────────────────────────────────
// Render news cards into the grid
// ─────────────────────────────────────────────
function renderGrid(articles) {
  const grid = document.getElementById("newsGrid");
  const empty = document.getElementById("emptyState");

  if (!articles || articles.length === 0) {
    grid.innerHTML = "";
    empty.classList.remove("d-none");
    return;
  }

  empty.classList.add("d-none");
  grid.innerHTML = articles.map(buildCard).join("");
}

function buildCard(a) {
  const date = a.published_at
    ? new Date(a.published_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
    : "Unknown date";

  const favIcon   = a.is_favorited ? "fas fa-star" : "far fa-star";
  const favClass  = a.is_favorited ? "favorited" : "";
  const favLabel  = a.is_favorited ? "Saved" : "Save";
  const summary   = a.summary || "No summary available.";

  const aiBox = a.ai_summary
    ? `<div class="ai-summary-box"><strong><i class="fas fa-robot me-1"></i>AI Summary</strong>${a.ai_summary}</div>`
    : "";

  return `
    <div class="news-card" id="card-${a.id}">
      <div class="card-source-row">
        <span class="source-badge">${escHtml(a.source || "Unknown")}</span>
        <span class="card-date"><i class="far fa-clock me-1"></i>${date}</span>
      </div>

      <div class="card-title">
        <a href="${escHtml(a.url)}" target="_blank" rel="noopener">${escHtml(a.title)}</a>
      </div>

      <div class="card-summary">${escHtml(summary)}</div>

      ${aiBox}

      <div class="card-actions">
        <button class="action-btn fav-btn ${favClass}" id="fav-${a.id}" onclick="toggleFavorite(${a.id})">
          <i class="${favIcon}"></i>${favLabel}
        </button>
        <button class="action-btn broadcast-btn" onclick="openBroadcast(${a.id}, '${escHtml(a.title.replace(/'/g, "\\'"))}')">
          <i class="fas fa-satellite-dish"></i>Broadcast
        </button>
        <button class="action-btn ai-btn" onclick="openEnrich(${a.id})">
          <i class="fas fa-robot"></i>AI Summary
        </button>
      </div>
    </div>
  `;
}

// ─────────────────────────────────────────────
// Favorite / Unfavorite
// ─────────────────────────────────────────────
async function toggleFavorite(id) {
  const btn = document.getElementById(`fav-${id}`);
  const isFav = btn.classList.contains("favorited");

  try {
    const method = isFav ? "DELETE" : "POST";
    const res = await fetch(`${API}/api/favorites/${id}`, { method });
    const data = await res.json();

    if (isFav) {
      btn.classList.remove("favorited");
      btn.innerHTML = `<i class="far fa-star"></i>Save`;
    } else {
      btn.classList.add("favorited");
      btn.innerHTML = `<i class="fas fa-star"></i>Saved`;
    }

    showToast(isFav ? "Removed from favorites" : "Added to favorites ⭐", "success");
  } catch (err) {
    showToast("Failed to update favorites.", "danger");
    console.error(err);
  }
}

// ─────────────────────────────────────────────
// Broadcast Modal
// ─────────────────────────────────────────────
function openBroadcast(id, title) {
  activeBroadcastId = id;
  document.getElementById("modalArticleTitle").textContent = title;
  document.getElementById("broadcastResult").classList.add("d-none");
  document.getElementById("broadcastResult").innerHTML = "";
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

    resultBox.innerHTML = `<i class="fas fa-check-circle me-2"></i>${data.message}
      <br><small class="d-block mt-1 opacity-75">${data.note}</small>`;
    resultBox.classList.remove("d-none");
    showToast(`Broadcast simulated on ${platform} ✅`, "success");

  } catch (err) {
    resultBox.innerHTML = `<span class="text-danger">Broadcast failed. Try again.</span>`;
    resultBox.classList.remove("d-none");
  }
}

// ─────────────────────────────────────────────
// AI Enrich Modal
// ─────────────────────────────────────────────
async function openEnrich(id) {
  document.getElementById("enrichModalBody").innerHTML = `
    <div class="text-center py-4">
      <div class="spinner-ring"></div>
      <p class="mt-3 text-muted">Asking Groq AI to summarize...</p>
    </div>`;
  enrichModal.show();

  try {
    const res = await fetch(`${API}/api/news/${id}/enrich`, { method: "POST" });
    const data = await res.json();

    // API key not set or Groq failed — show actionable error
    if (!data.success) {
      document.getElementById("enrichModalBody").innerHTML = `
        <div style="background:rgba(248,113,113,0.1);border:1px solid rgba(248,113,113,0.3);border-radius:8px;padding:16px;">
          <p style="color:#f87171;margin:0 0 8px;font-weight:600;">
            <i class="fas fa-exclamation-triangle me-2"></i>AI Enrichment Failed
          </p>
          <p style="color:#8a9ab8;font-size:13px;margin:0 0 12px;">${escHtml(data.error || "Unknown error")}</p>
          <hr style="border-color:#1f2d42;margin:12px 0;">
          <p style="color:#4a5a72;font-size:12px;margin:0;">
            <strong style="color:#8a9ab8;">To fix this:</strong><br>
            1. Get a free key at <a href="https://console.groq.com" target="_blank" style="color:#00d4ff;">console.groq.com</a><br>
            2. Add <code style="background:#0a0d12;padding:1px 6px;border-radius:4px;">GROQ_API_KEY=gsk_...</code> to your <code style="background:#0a0d12;padding:1px 6px;border-radius:4px;">.env</code> file<br>
            3. Restart the server and try again
          </p>
        </div>`;
      return;
    }

    const captionHtml = data.linkedin_caption
      ? `<div class="ai-summary-box mt-3">
           <strong><i class="fab fa-linkedin me-1"></i>LinkedIn Caption</strong>
           ${escHtml(data.linkedin_caption)}
         </div>`
      : "";

    document.getElementById("enrichModalBody").innerHTML = `
      <div class="ai-summary-box">
        <strong><i class="fas fa-robot me-1"></i>AI Summary</strong>
        ${escHtml(data.ai_summary)}
      </div>
      ${captionHtml}
      <p class="text-muted small mt-3 mb-0">
        <i class="fas fa-info-circle me-1"></i>
        Powered by Groq API (llama-3.1-8b-instant). Results cached in database.
      </p>`;

    // Update card in grid if visible
    const card = document.getElementById(`card-${id}`);
    if (card && data.ai_summary) {
      const existing = card.querySelector(".ai-summary-box");
      if (!existing) {
        const summaryEl = card.querySelector(".card-summary");
        const box = document.createElement("div");
        box.className = "ai-summary-box";
        box.innerHTML = `<strong><i class="fas fa-robot me-1"></i>AI Summary</strong>${escHtml(data.ai_summary)}`;
        summaryEl.after(box);
      }
    }

  } catch (err) {
    document.getElementById("enrichModalBody").innerHTML = `
      <p style="color:#f87171;"><i class="fas fa-exclamation-triangle me-2"></i>
      Network error — is the backend running?</p>`;
  }
}

// ─────────────────────────────────────────────
// Fetch News (trigger RSS fetch)
// ─────────────────────────────────────────────
async function fetchNews() {
  const btn = document.getElementById("fetchBtn");
  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-sync-alt fa-spin me-1"></i>Fetching...`;

  try {
    await fetch(`${API}/api/news/fetch`, { method: "POST" });
    showToast("Fetch started! Refreshing in 5 seconds...", "success");
    setTimeout(() => { loadNews(); }, 5000);
  } catch (err) {
    showToast("Fetch failed. Is the backend running?", "danger");
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.innerHTML = `<i class="fas fa-sync-alt me-1"></i>Fetch News`;
    }, 5000);
  }
}

// ─────────────────────────────────────────────
// Source Filter
// ─────────────────────────────────────────────
function filterSource(source) {
  currentSource = source;
  currentPage   = 1;

  document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  event.target.classList.add("active");
  document.getElementById("srcFilter").textContent = source || "All sources";

  loadNews();
}

// ─────────────────────────────────────────────
// Pagination
// ─────────────────────────────────────────────
function changePage(direction) {
  const maxPage = Math.ceil(totalArticles / PAGE_SIZE);
  currentPage = Math.max(1, Math.min(currentPage + direction, maxPage));
  loadNews();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updatePagination(total, page) {
  const maxPage = Math.ceil(total / PAGE_SIZE);
  document.getElementById("pageInfo").textContent = `Page ${page} of ${maxPage || 1}`;
  document.getElementById("prevBtn").disabled = page <= 1;
  document.getElementById("nextBtn").disabled = page >= maxPage;
  document.getElementById("pagination").style.display = total > PAGE_SIZE ? "flex" : "none";
}

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────
function showLoading(show) {
  document.getElementById("loadingState").style.display = show ? "block" : "none";
  document.getElementById("newsGrid").style.display     = show ? "none" : "grid";
}

function showToast(msg, type = "success") {
  const el = document.getElementById("liveToast");
  el.className = `toast align-items-center text-white border-0 bg-${type === "success" ? "success" : "danger"}`;
  document.getElementById("toastMsg").textContent = msg;
  toastEl.show();
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
