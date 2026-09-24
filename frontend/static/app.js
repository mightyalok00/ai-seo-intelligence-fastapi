const form = document.getElementById("seo-form");
const dashboard = document.getElementById("dashboard");
const emptyState = document.getElementById("empty-state");
const results = document.getElementById("results");
const formStatus = document.getElementById("form-status");
const themeToggle = document.getElementById("theme-toggle");
let latestAudit = null;

const getSavedTheme = () => {
  try { return localStorage.getItem("seo-audit-theme"); } catch { return null; }
};

const applyTheme = (theme) => {
  const dark = theme === "dark";
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  themeToggle.textContent = dark ? "Light mode" : "Dark mode";
  themeToggle.setAttribute("aria-pressed", String(dark));
  themeToggle.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} theme`);
};

const preferredTheme = getSavedTheme()
  || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
applyTheme(preferredTheme);

themeToggle.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
  try { localStorage.setItem("seo-audit-theme", next); } catch { /* Theme still works for this visit. */ }
});

const lines = (id, keepEmpty = false) => document.getElementById(id).value
  .split("\n")
  .map((item) => item.trim())
  .filter((item) => keepEmpty || item);

const optionalNumber = (id) => {
  const value = document.getElementById(id).value;
  return value === "" ? null : Number(value);
};

const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const labels = {
  title: "Title",
  meta_description: "Meta description",
  h1_h2_structure: "H1 / H2 structure",
  content_depth: "Content depth",
  semantic_terms: "Semantic terms",
  internal_links: "Internal links",
  external_links: "External links",
  image_alt: "Image ALT",
  schema: "Schema",
  canonical: "Canonical",
  robots_indexability: "Robots / indexability",
  keyword_usage_stuffing: "Keyword usage",
  readability: "Readability",
  search_intent_match: "Intent match",
  url_quality: "URL quality",
  technical_checks: "Technical checks",
};

function renderList(id, values, emptyText) {
  const list = document.getElementById(id);
  list.innerHTML = values.length
    ? values.map((value) => `<li>${escapeHtml(value)}</li>`).join("")
    : `<li class="muted">${escapeHtml(emptyText)}</li>`;
}

function renderDashboard(data) {
  latestAudit = data;
  emptyState.hidden = true;
  dashboard.hidden = false;
  document.getElementById("overall-score").textContent = data.overall_score;
  document.getElementById("grade").textContent = data.grade;
  document.getElementById("status").textContent = `${data.search_intent} intent · ${data.keyword_density}% keyword density`;
  document.getElementById("progress-bar").style.width = `${data.overall_score}%`;
  document.getElementById("score-ring").style.setProperty("--score", `${data.overall_score * 3.6}deg`);

  document.getElementById("score-chart").innerHTML = Object.entries(data.category_scores)
    .map(([key, item]) => {
      const percent = Math.round((item.score / item.max) * 100);
      const label = labels[key] || key;
      return `<div class="chart-row" aria-label="${escapeHtml(label)}: ${item.score} out of ${item.max}">
        <span>${escapeHtml(label)}</span>
        <div class="chart-track"><i style="width:${percent}%"></i></div>
        <strong>${percent}%</strong>
      </div>`;
    }).join("");

  document.getElementById("category-grid").innerHTML = Object.entries(data.category_scores)
    .map(([key, item]) => {
      const percent = Math.round((item.score / item.max) * 100);
      const details = [...item.issues, ...item.recommendations];
      return `<article class="category-card">
        <div class="category-card__top"><h3>${labels[key] || key}</h3><strong>${item.score}<span>/${item.max}</span></strong></div>
        <div class="mini-progress"><span style="width:${percent}%"></span></div>
        <details><summary>${item.issues.length} issue${item.issues.length === 1 ? "" : "s"}</summary>
          <ul>${details.length ? details.map((text) => `<li>${escapeHtml(text)}</li>`).join("") : "<li>All strict checks passed.</li>"}</ul>
        </details>
      </article>`;
    }).join("");

  document.getElementById("critical-count").textContent = data.critical_issues.length;
  document.getElementById("warning-count").textContent = data.warnings.length;
  document.getElementById("passed-count").textContent = data.passed_checks.length;
  renderList("critical-list", data.critical_issues, "No critical issues detected.");
  renderList("warning-list", data.warnings.slice(0, 12), "No warnings detected.");
  renderList("passed-list", data.passed_checks, "No category passed every strict check yet.");
  document.getElementById("priority-list").innerHTML = data.priority_recommendations.length
    ? data.priority_recommendations.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
    : "<li>Maintain quality and re-audit after meaningful page changes.</li>";
  document.getElementById("results").scrollIntoView({ behavior: "smooth", block: "start" });
  results.focus({ preventScroll: true });
}

document.getElementById("export-json").addEventListener("click", () => {
  if (!latestAudit) return;
  const safeKeyword = latestAudit.keyword.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "seo-audit";
  const blob = new Blob([JSON.stringify(latestAudit, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${safeKeyword}-audit.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  formStatus.textContent = "JSON audit report downloaded.";
});

document.getElementById("print-report").addEventListener("click", () => {
  if (!latestAudit) return;
  window.print();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button[type='submit']");
  const robotsValue = document.getElementById("robots-indexable").value;
  let schemaValue = document.getElementById("schema").value.trim() || null;
  if (schemaValue) {
    try { schemaValue = JSON.parse(schemaValue); } catch { /* The API reports a deterministic schema issue. */ }
  }
  const payload = {
    keyword: document.getElementById("keyword").value.trim(),
    url: document.getElementById("url").value.trim(),
    title: document.getElementById("title").value.trim(),
    meta_description: document.getElementById("meta").value.trim(),
    h1: document.getElementById("h1").value.trim(),
    h2s: lines("h2s"),
    content: document.getElementById("content").value.trim(),
    semantic_terms: lines("semantic-terms"),
    internal_links: lines("internal-links"),
    external_links: lines("external-links"),
    image_alts: lines("image-alts", true),
    schema_json_ld: schemaValue,
    canonical: document.getElementById("canonical").value.trim(),
    robots_indexable: robotsValue === "unknown" ? null : robotsValue === "true",
    robots_directives: document.getElementById("robots-directives").value.trim(),
    technical: {
      https: document.getElementById("https").checked,
      mobile_friendly: document.getElementById("mobile-friendly").checked,
      page_speed_score: optionalNumber("page-speed"),
      status_code: optionalNumber("status-code"),
      has_viewport: document.getElementById("viewport").checked,
      has_favicon: document.getElementById("favicon").checked,
      has_sitemap: document.getElementById("sitemap").checked,
      broken_links: optionalNumber("broken-links"),
    },
  };

  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  form.setAttribute("aria-busy", "true");
  button.innerHTML = '<span class="spinner" aria-hidden="true"></span><span>Auditing page signals…</span>';
  formStatus.textContent = "SEO audit is running.";
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join("; ") : data.detail;
      throw new Error(detail || "The audit request failed.");
    }
    renderDashboard(data);
    formStatus.textContent = `Audit complete. Score ${data.overall_score} out of 100.`;
  } catch (error) {
    emptyState.hidden = false;
    dashboard.hidden = true;
    emptyState.querySelector("h2").textContent = "Audit could not run";
    emptyState.querySelector("p").textContent = error.message;
    formStatus.textContent = `Audit failed: ${error.message}`;
    results.focus();
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    form.removeAttribute("aria-busy");
    button.innerHTML = 'Run strict SEO audit <span aria-hidden="true">→</span>';
  }
});

