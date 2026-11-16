// Expense Tracker frontend — vanilla JavaScript, no framework.
// Talks to the FastAPI backend on the same origin.

const $ = (id) => document.getElementById(id);

const money = (n) => "$" + Number(n).toFixed(2);

async function fetchJSON(url, options) {
  const resp = await fetch(url, options);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || ("Request failed: " + resp.status));
  }
  return resp.status === 204 ? null : resp.json();
}

function currentMonth() {
  return new Date().toISOString().slice(0, 7);
}

async function loadCategories() {
  const data = await fetchJSON("/api/categories");
  for (const select of [$("category"), $("filter-category")]) {
    for (const cat of data.categories) {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat;
      select.appendChild(opt);
    }
  }
}

async function loadExpenses() {
  const category = $("filter-category").value;
  const month = $("month").value;
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (month) params.set("month", month);
  const expenses = await fetchJSON("/api/expenses?" + params.toString());
  const tbody = $("expense-rows");
  tbody.innerHTML = "";
  $("empty-note").textContent = expenses.length === 0 ? "No expenses match." : "";
  for (const e of expenses) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      "<td>" + e.date + "</td>" +
      "<td>" + e.category + "</td>" +
      "<td></td>" +
      '<td class="right">' + money(e.amount) + "</td>" +
      "<td></td>";
    tr.children[2].textContent = e.note;
    const delBtn = document.createElement("button");
    delBtn.textContent = "Delete";
    delBtn.addEventListener("click", async () => {
      await fetchJSON("/api/expenses/" + e.id, { method: "DELETE" });
      await refresh();
    });
    tr.children[4].appendChild(delBtn);
    tbody.appendChild(tr);
  }
}

function drawChart(byCategory) {
  const canvas = $("chart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const entries = Object.entries(byCategory);
  if (entries.length === 0) {
    ctx.font = "14px sans-serif";
    ctx.fillStyle = "#666";
    ctx.fillText("No expenses this month.", 10, 30);
    return;
  }
  const max = Math.max(...entries.map(([, v]) => v));
  const barHeight = 24;
  const gap = 10;
  const labelWidth = 110;
  entries.forEach(([cat, total], i) => {
    const y = 10 + i * (barHeight + gap);
    const width = (total / max) * (canvas.width - labelWidth - 90);
    ctx.font = "13px sans-serif";
    ctx.fillStyle = "#222";
    ctx.fillText(cat, 0, y + 16);
    ctx.fillStyle = "#1a73e8";
    ctx.fillRect(labelWidth, y, width, barHeight);
    ctx.fillStyle = "#222";
    ctx.fillText(money(total), labelWidth + width + 8, y + 16);
  });
}

async function loadSummary() {
  const month = $("month").value;
  const summary = await fetchJSON("/api/summary?month=" + month);
  $("summary-line").textContent =
    summary.month + ": " + summary.count + " expense(s), total " + money(summary.total);
  drawChart(summary.by_category);
}

async function refresh() {
  await loadExpenses();
  await loadSummary();
}

$("add-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("form-error").textContent = "";
  const payload = {
    amount: parseFloat($("amount").value),
    category: $("category").value,
    date: $("date").value,
    note: $("note").value,
  };
  try {
    await fetchJSON("/api/expenses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    event.target.reset();
    $("date").value = new Date().toISOString().slice(0, 10);
    await refresh();
  } catch (err) {
    $("form-error").textContent = err.message;
  }
});

$("filter-category").addEventListener("change", loadExpenses);
$("month").addEventListener("change", refresh);

(async function init() {
  $("month").value = currentMonth();
  $("date").value = new Date().toISOString().slice(0, 10);
  await loadCategories();
  await refresh();
})();
