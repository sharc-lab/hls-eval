const DATA_URL = "data/leaderboard.json";

const taskSelect = document.getElementById("task-select");
const metricSelect = document.getElementById("metric-select");
const kSelect = document.getElementById("k-select");
const tableBody = document.querySelector("#leaderboard-table tbody");
const emptyState = document.getElementById("empty-state");

const lastUpdated = document.getElementById("last-updated");
const taskCount = document.getElementById("task-count");
const modelCount = document.getElementById("model-count");

const tableHeaders = document.querySelectorAll("#leaderboard-table th[data-sort-key]");
let sortState = { key: "pass_synth", direction: "desc" };

let leaderboardData = null;

function createOption(value, label) {
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  return option;
}

function formatPercent(value) {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function clearChildren(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function populateFilters() {
  clearChildren(taskSelect);
  clearChildren(metricSelect);

  leaderboardData.tasks.forEach((task) => {
    taskSelect.appendChild(createOption(task.id, task.label));
  });

  leaderboardData.metrics.forEach((metric) => {
    metricSelect.appendChild(createOption(metric.id, metric.label));
  });
}

function updateMeta() {
  if (lastUpdated) {
    lastUpdated.textContent = leaderboardData.generated_at || "—";
  }
  if (taskCount) {
    taskCount.textContent = leaderboardData.tasks.length;
  }
  if (modelCount) {
    modelCount.textContent = leaderboardData.models.length;
  }
}

function getSelectedResults() {
  const taskId = taskSelect.value;
  const metricId = metricSelect.value;
  const k = Number(kSelect.value);

  const task = leaderboardData.results.find((entry) => entry.task_id === taskId);
  if (!task) return [];

  const metric = task.metrics.find((entry) => entry.metric_id === metricId);
  if (!metric) return [];

  const kEntry = metric.k_values.find((entry) => entry.k === k);
  return kEntry ? kEntry.runs : [];
}

function renderTable() {
  clearChildren(tableBody);
  const results = getSelectedResults();

  if (!results.length) {
    emptyState.hidden = false;
    return;
  }

  emptyState.hidden = true;

  const sorted = [...results].sort((a, b) => {
    const { key, direction } = sortState;
    const dir = direction === "asc" ? 1 : -1;

    if (key === "model") {
      return a.model_label.localeCompare(b.model_label) * dir;
    }

    const aVal = a.breakdown[key] ?? 0;
    const bVal = b.breakdown[key] ?? 0;
    if (aVal === bVal) {
      return a.model_label.localeCompare(b.model_label);
    }
    return (aVal - bVal) * dir;
  });

  sorted.forEach((row, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.model_label}</td>
      <td>${formatPercent(row.breakdown.pass_parse)}</td>
      <td>${formatPercent(row.breakdown.pass_compile)}</td>
      <td>${formatPercent(row.breakdown.pass_tb)}</td>
      <td>${formatPercent(row.breakdown.pass_synth)}</td>
    `;
    tableBody.appendChild(tr);
  });
}

function attachListeners() {
  [taskSelect, metricSelect, kSelect].forEach((select) => {
    select.addEventListener("change", renderTable);
  });

  tableHeaders.forEach((header) => {
    header.addEventListener("click", () => {
      const key = header.dataset.sortKey;
      if (sortState.key === key) {
        sortState.direction = sortState.direction === "asc" ? "desc" : "asc";
      } else {
        sortState = { key, direction: "desc" };
      }
      updateSortIndicators();
      renderTable();
    });
  });
}

function updateSortIndicators() {
  tableHeaders.forEach((header) => {
    const key = header.dataset.sortKey;
    if (key === sortState.key) {
      header.setAttribute("data-sort", "active");
      header.setAttribute("data-sort-direction", sortState.direction);
    } else {
      header.removeAttribute("data-sort");
      header.removeAttribute("data-sort-direction");
    }
  });
}

async function init() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) {
      throw new Error(`Failed to load ${DATA_URL}`);
    }
    leaderboardData = await response.json();
    populateFilters();
    updateMeta();
    attachListeners();
    updateSortIndicators();
    renderTable();
  } catch (err) {
    emptyState.hidden = false;
    emptyState.textContent = "Could not load leaderboard data.";
    console.error(err);
  }
}

init();
