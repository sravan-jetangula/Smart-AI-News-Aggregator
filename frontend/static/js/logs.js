/**
 * logs.js — Broadcast Logs page logic
 */

const API = "";

document.addEventListener("DOMContentLoaded", loadLogs);

async function loadLogs() {
  try {
    const res  = await fetch(`${API}/api/broadcast/logs`);
    const data = await res.json();

    document.getElementById("loadingState").style.display = "none";

    if (!data.logs || data.logs.length === 0) {
      document.getElementById("emptyState").classList.remove("d-none");
      return;
    }

    document.getElementById("logCount").innerHTML =
      `<i class="fas fa-satellite-dish me-1"></i>${data.total} broadcast${data.total !== 1 ? "s" : ""} logged`;

    const tbody = document.getElementById("logsTableBody");
    tbody.innerHTML = data.logs.map((log, idx) => `
      <tr>
        <td style="color:var(--text-muted);font-size:11px;">${idx + 1}</td>
        <td><span class="platform-tag ${log.platform}">${platformIcon(log.platform)} ${cap(log.platform)}</span></td>
        <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escHtml(log.article_title)}">
          ${escHtml(log.article_title)}
        </td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text-muted);font-size:12px;" title="${escHtml(log.caption_used || '')}">
          ${escHtml((log.caption_used || "—").slice(0, 80))}
        </td>
        <td><span class="status-tag">${log.status}</span></td>
        <td style="color:var(--text-muted);font-size:12px;white-space:nowrap;">${formatDate(log.broadcasted_at)}</td>
      </tr>
    `).join("");

    document.getElementById("logsContainer").classList.remove("d-none");

  } catch (err) {
    document.getElementById("loadingState").innerHTML =
      `<p class="text-danger text-center">Failed to load logs. Is the backend running?</p>`;
  }
}

function platformIcon(p) {
  const icons = { email: "📧", linkedin: "🔗", whatsapp: "💬" };
  return icons[p] || "📡";
}

function cap(str) { return str.charAt(0).toUpperCase() + str.slice(1); }

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
  });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
