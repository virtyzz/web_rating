const clusterServers = {
  1: ["cherno1", "cherno2", "deadfall1", "dungeon1"],
  2: ["cherno3", "cherno4", "deadfall2", "dungeon2"],
};

const state = {
  cluster: 1,
};

const clusterSwitch = document.getElementById("clusterSwitch");
const uploadFields = document.getElementById("uploadFields");
const uploadForm = document.getElementById("uploadForm");
const submitButton = document.getElementById("submitButton");
const message = document.getElementById("message");
const serverTables = document.getElementById("serverTables");
const summaryTable = document.getElementById("summaryTable");
const summaryMeta = document.getElementById("summaryMeta");
const clusterStatus = document.getElementById("clusterStatus");
const progressItems = Array.from(document.querySelectorAll("#progressList li"));

function setMessage(text, type = "") {
  message.textContent = text;
  message.className = `message ${type}`.trim();
}

function markProgress(step) {
  progressItems.forEach((item, index) => {
    item.classList.remove("active", "done");
    if (index < step) item.classList.add("done");
    if (index === step) item.classList.add("active");
  });
}

function resetProgress() {
  progressItems.forEach((item) => item.classList.remove("active", "done"));
}

function createClusterButtons() {
  clusterSwitch.innerHTML = "";
  Object.keys(clusterServers).forEach((clusterId) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `cluster-button ${Number(clusterId) === state.cluster ? "active" : ""}`.trim();
    button.textContent = `Кластер ${clusterId}`;
    button.addEventListener("click", () => {
      state.cluster = Number(clusterId);
      createClusterButtons();
      createUploadFields();
      setMessage("");
      resetProgress();
      loadClusterData();
    });
    clusterSwitch.appendChild(button);
  });
}

function createUploadFields() {
  uploadFields.innerHTML = "";
  clusterServers[state.cluster].forEach((serverName) => {
    const wrapper = document.createElement("div");
    wrapper.className = "upload-card";
    wrapper.innerHTML = `
      <label for="${serverName}">${serverName}</label>
      <input id="${serverName}" name="${serverName}" type="file" accept="image/png,image/jpeg,image/webp" required />
    `;
    uploadFields.appendChild(wrapper);
  });
}

function formatDate(value) {
  if (!value) return "Нет данных";
  return new Date(value).toLocaleString("ru-RU");
}

function renderServerTables(payload) {
  serverTables.innerHTML = "";

  payload.servers.forEach((server) => {
    const card = document.createElement("article");
    card.className = "table-card";

    const header = document.createElement("div");
    header.className = "table-header";
    header.innerHTML = `
      <h3>${server.server_name}</h3>
      <div class="table-meta">Обновлено: ${formatDate(server.updated_at)}</div>
    `;
    card.appendChild(header);

    if (!server.players.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "Для этого сервера пока нет данных.";
      card.appendChild(empty);
    } else {
      card.appendChild(
        buildTable(
          [
            ["Игрок", "name"],
            ["Ранг", "rank"],
            ["Очки", "points"],
            ["Убийства", "kills"],
          ],
          server.players,
        ),
      );
    }

    serverTables.appendChild(card);
  });

  clusterStatus.textContent = payload.is_complete
    ? `Кластер ${payload.cluster_id} заполнен`
    : `Кластер ${payload.cluster_id}: нужны все 4 скриншота`;
}

function buildTable(columns, rows) {
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach(([label]) => {
    const th = document.createElement("th");
    th.textContent = label;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach(([, key]) => {
      const td = document.createElement("td");
      td.textContent = row[key];
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  return table;
}

function renderSummary(payload) {
  summaryMeta.textContent = `Сводка по кластеру ${payload.cluster_id}. Обновлено: ${formatDate(payload.generated_at)}`;

  if (!payload.players.length) {
    summaryTable.innerHTML = '<div class="empty-state">В сводной таблице пока нет данных.</div>';
    return;
  }

  summaryTable.innerHTML = "";
  summaryTable.appendChild(
    buildTable(
      [
        ["Игрок", "name"],
        ["Лучший ранг", "best_rank"],
        ["Сумма очков", "total_points"],
        ["Сумма убийств", "total_kills"],
      ],
      payload.players,
    ),
  );
}

async function loadClusterData() {
  setMessage("");
  try {
    const serversResponse = await fetch(`/servers/${state.cluster}`);
    const serversPayload = await serversResponse.json();
    if (!serversResponse.ok) {
      throw new Error(serversPayload.detail || "Не удалось получить таблицы серверов.");
    }
    renderServerTables(serversPayload);

    const summaryResponse = await fetch(`/summary/${state.cluster}`);
    if (summaryResponse.ok) {
      renderSummary(await summaryResponse.json());
    } else {
      const summaryPayload = await summaryResponse.json();
      summaryMeta.textContent = summaryPayload.detail || "Сводка недоступна.";
      summaryTable.innerHTML = '<div class="empty-state">Сводка появится после загрузки всех 4 серверов.</div>';
    }
  } catch (error) {
    setMessage(`Не удалось загрузить данные: ${error.message}`, "error");
  }
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("");
  submitButton.disabled = true;

  try {
    markProgress(0);
    const formData = new FormData();
    const files = [];

    clusterServers[state.cluster].forEach((serverName) => {
      const input = document.getElementById(serverName);
      const file = input.files[0];
      if (!file) {
        throw new Error(`Загрузите обязательный скриншот для ${serverName}.`);
      }
      if (!file.type.startsWith("image/")) {
        throw new Error(`${serverName}: файл должен быть изображением.`);
      }
      files.push(file);
      formData.append("files", file);
      formData.append("server_names", serverName);
    });

    if (files.length !== 4) {
      throw new Error("Нужно загрузить ровно 4 скриншота.");
    }

    markProgress(1);
    const response = await fetch(`/upload/${state.cluster}`, {
      method: "POST",
      body: formData,
    });

    markProgress(2);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Ошибка загрузки.");
    }

    markProgress(3);
    await loadClusterData();
    markProgress(4);
    setMessage(payload.message, "success");
  } catch (error) {
    setMessage(error.message, "error");
    resetProgress();
  } finally {
    submitButton.disabled = false;
  }
});

createClusterButtons();
createUploadFields();
loadClusterData();
