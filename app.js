// The browser reads JSON from our server and updates normal HTML elements.
let data = { reviews: [], businesses: [], reviewers: [], audit: [] };
let selectedId = null;
let saving = false;
const byId = id => document.getElementById(id);

// Escape stored text before displaying it as HTML.
function escapeHtml(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}
function risk(score) {
  if (score >= 60) return "High risk";
  if (score >= 30) return "Watchlist";
  return "Low risk";
}
function scoreBadge(score) {
  const color = score >= 60 ? "high" : score >= 30 ? "medium" : "low";
  return '<span class="badge ' + color + '">' + score + ' / 100</span>';
}
function average(reviews) {
  if (!reviews.length) return "0.0";
  let total = 0;
  for (const review of reviews) total += review.rating;
  return (total / reviews.length).toFixed(1);
}

// Navigation: show one section at a time.
function showPage(page) {
  const titles = {
    overview: "A clearer picture of trust.",
    reviews: "Every review tells a story.",
    businesses: "Know who is being reviewed.",
    reviewers: "Follow account activity.",
    database: "Behind the insights."
  };
  for (const name of Object.keys(titles)) byId(name).hidden = name !== page;
  for (const button of document.querySelectorAll("nav button")) {
    button.classList.toggle("active", button.dataset.page === page);
  }
  byId("title").textContent = titles[page];
  byId("breadcrumb").textContent = page[0].toUpperCase() + page.slice(1);
}
for (const button of document.querySelectorAll("nav button")) {
  button.onclick = () => showPage(button.dataset.page);
}
byId("view-all").onclick = () => showPage("reviews");

// READ data from MySQL through the backend.
async function loadData() {
  const response = await fetch("/api/data");
  const result = await response.json();
  if (!response.ok) throw new Error(result.error);
  data = result;
  renderOverview();
  renderReviews();
  renderBusinesses();
  renderReviewers();
  renderAudit();
  byId("business-select").innerHTML = data.businesses.map(b =>
    '<option value="' + b.id + '">' + escapeHtml(b.name) + '</option>').join("");
  byId("reviewer-select").innerHTML = data.reviewers.map(u =>
    '<option value="' + u.id + '">' + escapeHtml(u.name) + '</option>').join("");
}

function reviewTable(reviews) {
  if (!reviews.length) return '<p class="empty">No matching reviews.</p>';
  let html = '<table><thead><tr><th>REVIEW / BUSINESS</th><th>REVIEWER</th><th>RATING</th><th>SCORE</th><th>STATUS</th><th></th></tr></thead><tbody>';
  for (const review of reviews) {
    html += '<tr><td><b>' + escapeHtml(review.business) + '</b><small class="excerpt">' +
      escapeHtml(review.body) + '</small></td><td>' + escapeHtml(review.reviewer) +
      '<small>Account #' + review.reviewer_id + '</small></td><td><span class="stars">' +
      "★".repeat(review.rating) + '</span><small>' + escapeHtml(review.posted.slice(0, 10)) +
      '</small></td><td>' + scoreBadge(review.score) + '</td><td>' +
      escapeHtml(review.status) + '</td><td><button data-review="' + review.id +
      '">Inspect ↗</button></td></tr>';
  }
  return html + '</tbody></table>';
}

function renderOverview() {
  const high = data.reviews.filter(r => r.score >= 60);
  const cards = [
    ["Total reviews", data.reviews.length, "Across " + data.businesses.length + " businesses"],
    ["High risk reviews", high.length, "Prioritized for investigation"],
    ["Reviewer accounts", data.reviewers.length, "Linked activity patterns"],
    ["Average rating", average(data.reviews) + " / 5", "All recorded reviews"]
  ];
  byId("stats").innerHTML = cards.map(c =>
    '<article class="stat"><p>' + c[0] + '</p><strong>' + c[1] +
    '</strong><small>' + c[2] + '</small></article>').join("");
  byId("top-reviews").innerHTML = reviewTable([...high].sort((a,b) => b.score-a.score).slice(0,5));
  byId("total").textContent = data.reviews.length;
  const counts = ["Low risk", "Watchlist", "High risk"].map(name =>
    data.reviews.filter(r => risk(r.score) === name).length);
  byId("distribution").innerHTML = counts.map((count, i) =>
    '<div class="risk-row"><span>' + ["Low risk", "Watchlist", "High risk"][i] +
    '</span><b>' + count + '</b></div>').join("");
  const total = Math.max(1, data.reviews.length);
  const highPercent = counts[2] / total * 100;
  const mediumPercent = counts[1] / total * 100;
  byId("donut").style.background = "conic-gradient(#dc925b 0 " + highPercent +
    "%,#dfc375 " + highPercent + "% " + (highPercent+mediumPercent) + "%,#88b39b 0)";
  const daily = [];
  for (let day=1; day<=26; day++) {
    const date = "2026-10-" + String(day).padStart(2,"0");
    const rows = data.reviews.filter(r => r.posted.startsWith(date));
    daily.push({ day, total: rows.length, high: rows.filter(r => r.score>=60).length });
  }
  const max = Math.max(1, ...daily.map(d => d.total));
  byId("chart").innerHTML = daily.map(d =>
    '<div class="bar-space" title="October ' + d.day + ': ' + d.total +
    ' reviews, ' + d.high + ' high risk"><div class="bar" style="height:' +
    d.total/max*100 + '%"><div style="height:' +
    (d.total ? d.high/d.total*100 : 0) + '%"></div></div></div>').join("");
}

function renderReviews() {
  const search = byId("search").value.toLowerCase();
  const selectedRisk = byId("risk").value;
  const reviews = data.reviews.filter(r =>
    (r.business+" "+r.reviewer+" "+r.body).toLowerCase().includes(search) &&
    (selectedRisk === "All reviews" || risk(r.score) === selectedRisk));
  byId("review-table").innerHTML = reviewTable(reviews);
}
byId("search").oninput = renderReviews;
byId("risk").onchange = renderReviews;

function renderBusinesses() {
  byId("business-list").innerHTML = data.businesses.map(b => {
    const reviews = data.reviews.filter(r => r.business_id === b.id);
    return '<article class="card"><small class="eyebrow">' + escapeHtml(b.category) +
      ' · ' + escapeHtml(b.city) + '</small><h2>' + escapeHtml(b.name) +
      '</h2><strong class="business-rating">' + average(reviews) +
      ' <span class="stars">★</span></strong><p>' + reviews.length + ' reviews · ' +
      reviews.filter(r=>r.score>=60).length + ' high risk</p><button data-business="' +
      b.id + '">Explore reviews ↗</button></article>';
  }).join("");
}
function renderReviewers() {
  let html = '<table><thead><tr><th>ACCOUNT</th><th>JOINED</th><th>REVIEWS</th><th>BUSINESSES</th><th>HIGH RISK</th></tr></thead><tbody>';
  for (const user of data.reviewers) {
    const reviews = data.reviews.filter(r => r.reviewer_id === user.id);
    html += '<tr><td><b>' + escapeHtml(user.name) + '</b><small>#' + user.id +
      '</small></td><td>' + escapeHtml(user.joined) + '</td><td>' + reviews.length +
      '</td><td>' + new Set(reviews.map(r=>r.business_id)).size + '</td><td>' +
      reviews.filter(r=>r.score>=60).length + '</td></tr>';
  }
  byId("reviewer-list").innerHTML = html + '</tbody></table>';
}
function renderAudit() {
  byId("audit-list").innerHTML = data.audit.map(a =>
    '<div class="audit"><span>' + escapeHtml(a.action) + '</span><small>' +
    escapeHtml(new Date(a.created).toLocaleString()) + '</small></div>').join("");
}

// One click handler catches buttons created inside tables.
document.addEventListener("click", event => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.review) openReview(Number(button.dataset.review));
  if (button.dataset.business) {
    byId("search").value = data.businesses.find(b=>b.id===Number(button.dataset.business)).name;
    byId("risk").value = "All reviews";
    renderReviews();
    showPage("reviews");
  }
  if (button.dataset.close) byId(button.dataset.close).close();
});

function openReview(id) {
  const review = data.reviews.find(r => r.id === id);
  selectedId = id;
  byId("review-error").textContent = "";
  byId("review-detail").innerHTML = '<small class="eyebrow">REVIEW #' + id +
    '</small><h2>' + escapeHtml(review.business) + '</h2><p>' +
    escapeHtml(review.reviewer) + ' · ' + review.rating + ' stars</p><blockquote>' +
    escapeHtml(review.body) + '</blockquote><h3>Suspiciousness score ' +
    scoreBadge(review.score) + '</h3>' + review.signals.map(s =>
      '<div class="signal-row"><div><b>' + escapeHtml(s.name) + '</b><small>' +
      escapeHtml(s.detail) + '</small></div><strong>+' + s.points + '</strong></div>').join("");
  byId("review-dialog").showModal();
}

// CREATE / UPDATE / DELETE are sent to the backend, never directly to MySQL.
async function saveReview(change) {
  if (saving) return false;
  saving = true;
  document.querySelectorAll("dialog button").forEach(button => button.disabled = true);
  try {
    const response = await fetch("/api/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(change)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    byId("review-dialog").close();
    byId("add-dialog").close();
    await loadData();
    byId("message").textContent = "Database updated. Scores recalculated.";
    return true;
  } catch (error) {
    byId("form-error").textContent = error.message;
    byId("review-error").textContent = error.message;
    byId("message").textContent = error.message;
    return false;
  } finally {
    saving = false;
    document.querySelectorAll("dialog button").forEach(button => button.disabled = false);
  }
}
byId("mark-reviewed").onclick = () => saveReview({action:"status",id:selectedId,status:"Reviewed"});
byId("dismiss").onclick = () => saveReview({action:"status",id:selectedId,status:"Dismissed"});
byId("delete-review").onclick = () => {
  if (confirm("Delete this review? Its record will be removed from MySQL.")) {
    saveReview({action:"delete",id:selectedId});
  }
};
byId("add").onclick = () => {
  byId("form-error").textContent = "";
  byId("add-dialog").showModal();
};
byId("review-form").onsubmit = async event => {
  event.preventDefault();
  const fields = Object.fromEntries(new FormData(event.target));
  if (await saveReview({action:"add",...fields})) event.target.reset();
};
byId("export").onclick = () => {
  const file = new Blob([JSON.stringify(data,null,2)], {type:"application/json"});
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = "trustcheck-dataset.json";
  link.click();
  URL.revokeObjectURL(url);
};
loadData().catch(error => { byId("message").textContent = error.message; });
