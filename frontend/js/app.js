/* =====================================================================
   Task Manager — API Console
   Vanilla JS SPA wired to the real Flask/FastAPI backends from
   backend-assessment.rar. Verified against the actual route/service code:

   - Response envelope: {success, message, data, meta?}
   - Update method: PATCH everywhere (tasks also accept PUT)
   - Users & Projects lists: NOT paginated, NOT searchable (full array)
   - Tasks list: paginated + searchable (title only) + filterable
     (status, priority, project_id, assignee_id) + sortable (any Task
     column, "-" prefix = desc)
   - Comments: listable ONLY per-task via GET /tasks/{id}/comments.
     No global list, no update endpoint, no pagination.
   - Project edit cannot change owner_id (schema excludes it)
   - User edit cannot change password (schema excludes it)
   - Validation errors differ by backend:
       Flask   -> { errors: { field: [msg, ...] } }
       FastAPI -> { detail: [{ loc, msg, type }, ...] }  (422s)
               -> { detail: "message" }                  (404s/400s)
   ===================================================================== */

// ---------------------------------------------------------------------
// 1. Config
// ---------------------------------------------------------------------
const DEFAULT_BASES = {
  flask: "http://localhost:5000/api",
  fastapi: "http://localhost:8000/api",
};
let BASES = { ...DEFAULT_BASES };
let currentBackend = safeGet("backend") || "flask";

let memoryStore = {};
function safeGet(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return memoryStore[key];
  }
}
function safeSet(key, val) {
  try {
    localStorage.setItem(key, val);
  } catch {
    memoryStore[key] = val;
  }
}

function baseUrl() {
  return BASES[currentBackend];
}
function healthUrl() {
  return baseUrl().replace(/\/api$/, "") + "/health";
}

// ---------------------------------------------------------------------
// 2. Entity configuration
// ---------------------------------------------------------------------
const ENTITIES = {
  projects: {
    label: "Projects",
    endpoint: "/projects",
    paginated: false,
    searchable: false,
    editable: true,
    columns: [
      { key: "id", label: "ID", mono: true },
      { key: "name", label: "Name" },
      { key: "description", label: "Description", truncate: 50 },
      { key: "owner_id", label: "Owner ID", mono: true },
      { key: "task_count", label: "Tasks", mono: true },
      { key: "created_at", label: "Created", date: true },
    ],
    fields: {
      create: [
        { key: "name", label: "Name", type: "text", required: true },
        { key: "description", label: "Description", type: "textarea" },
        {
          key: "owner_id",
          label: "Owner",
          type: "select-remote",
          source: "users",
          required: true,
        },
      ],
      edit: [
        { key: "name", label: "Name", type: "text", required: true },
        { key: "description", label: "Description", type: "textarea" },
      ],
    },
  },

  tasks: {
    label: "Tasks",
    endpoint: "/tasks",
    paginated: true,
    searchable: true,
    searchPlaceholder: "Search by title…",
    editable: true,
    columns: [
      { key: "id", label: "ID", mono: true },
      { key: "title", label: "Title" },
      { key: "status", label: "Status", badge: "status" },
      { key: "priority", label: "Priority", badge: "priority" },
      { key: "project_id", label: "Project", mono: true },
      { key: "assignee_id", label: "Assignee", mono: true },
      { key: "due_date", label: "Due", date: true },
    ],
    fields: {
      create: [
        { key: "title", label: "Title", type: "text", required: true },
        { key: "description", label: "Description", type: "textarea" },
        {
          key: "status",
          label: "Status",
          type: "select",
          options: ["todo", "in_progress", "done", "cancelled"],
          default: "todo",
        },
        {
          key: "priority",
          label: "Priority",
          type: "select",
          options: ["low", "medium", "high", "urgent"],
          default: "medium",
        },
        {
          key: "project_id",
          label: "Project",
          type: "select-remote",
          source: "projects",
          required: true,
        },
        {
          key: "assignee_id",
          label: "Assignee (optional)",
          type: "select-remote",
          source: "users",
        },
        { key: "due_date", label: "Due date", type: "date" },
      ],
      edit: [
        { key: "title", label: "Title", type: "text", required: true },
        { key: "description", label: "Description", type: "textarea" },
        {
          key: "status",
          label: "Status",
          type: "select",
          options: ["todo", "in_progress", "done", "cancelled"],
        },
        {
          key: "priority",
          label: "Priority",
          type: "select",
          options: ["low", "medium", "high", "urgent"],
        },
        {
          key: "assignee_id",
          label: "Assignee (optional)",
          type: "select-remote",
          source: "users",
        },
        { key: "due_date", label: "Due date", type: "date" },
      ],
    },
    filters: [
      {
        key: "status",
        label: "All statuses",
        options: ["todo", "in_progress", "done", "cancelled"],
      },
      {
        key: "priority",
        label: "All priorities",
        options: ["low", "medium", "high", "urgent"],
      },
      {
        key: "sort",
        label: "Sort",
        options: [
          { value: "-created_at", label: "Newest first" },
          { value: "created_at", label: "Oldest first" },
          { value: "due_date", label: "Due soonest" },
          { value: "title", label: "Title A–Z" },
          { value: "-priority", label: "Priority (desc)" },
        ],
      },
    ],
  },

  users: {
    label: "Users",
    endpoint: "/users",
    paginated: false,
    searchable: false,
    editable: true,
    columns: [
      { key: "id", label: "ID", mono: true },
      { key: "username", label: "Username" },
      { key: "email", label: "Email" },
      { key: "created_at", label: "Created", date: true },
    ],
    fields: {
      create: [
        { key: "username", label: "Username", type: "text", required: true },
        { key: "email", label: "Email", type: "text", required: true },
        {
          key: "password",
          label: "Password (min 8 chars)",
          type: "password",
          required: true,
        },
      ],
      edit: [
        { key: "username", label: "Username", type: "text", required: true },
        { key: "email", label: "Email", type: "text", required: true },
      ],
    },
  },

  comments: {
    label: "Comments",
    endpoint: "/comments", // create/delete only; list is task-scoped, see fetchList()
    paginated: false,
    searchable: false,
    editable: false, // no update endpoint on this API
    scopedByTask: true,
    columns: [
      { key: "id", label: "ID", mono: true },
      { key: "content", label: "Content", truncate: 90 },
      { key: "author_id", label: "Author ID", mono: true },
      { key: "created_at", label: "Created", date: true },
    ],
    fields: {
      create: [
        { key: "content", label: "Content", type: "textarea", required: true },
        {
          key: "task_id",
          label: "Task",
          type: "select-remote",
          source: "tasks",
          required: true,
        },
        {
          key: "author_id",
          label: "Author",
          type: "select-remote",
          source: "users",
          required: true,
        },
      ],
      edit: [],
    },
  },
};

// ---------------------------------------------------------------------
// 3. State
// ---------------------------------------------------------------------
const state = {
  entity: "projects",
  page: 1,
  pageSize: 20,
  search: "",
  filters: {},
  totalPages: 1,
  editingId: null,
  selectedTaskId: null,
};

let lastLoadedItems = [];
const optionsCache = {};

// ---------------------------------------------------------------------
// 4. API layer
// ---------------------------------------------------------------------
function extractErrorMessage(data, status) {
  if (data?.errors && typeof data.errors === "object") {
    return Object.entries(data.errors)
      .map(
        ([field, msgs]) =>
          `${field}: ${Array.isArray(msgs) ? msgs.join(", ") : msgs}`,
      )
      .join(" · ");
  }
  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((d) => `${(d.loc || []).slice(1).join(".")}: ${d.msg}`)
      .join(" · ");
  }
  if (typeof data?.detail === "string") return data.detail;
  if (data?.message) return data.message;
  return `HTTP ${status}`;
}

async function apiFetch(path, { method = "GET", body } = {}) {
  const res = await fetch(baseUrl() + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) throw new Error(extractErrorMessage(data, res.status));
  return data;
}

function unwrapEnvelope(raw) {
  const items = Array.isArray(raw?.data) ? raw.data : [];
  return { items, meta: raw?.meta || null };
}

async function fetchOptions(source) {
  const cached = optionsCache[source];
  if (cached && Date.now() - cached.ts < 20000) return cached.data;

  const cfg = ENTITIES[source];
  let path = cfg.endpoint;
  if (cfg.paginated) path += "?page=1&page_size=100";
  const raw = await apiFetch(path);
  const { items } = unwrapEnvelope(raw);

  const labelFor = (item) => {
    if (source === "users") return `${item.username} (#${item.id})`;
    if (source === "projects") return `${item.name} (#${item.id})`;
    if (source === "tasks") return `${item.title} (#${item.id})`;
    return `#${item.id}`;
  };
  const data = items.map((i) => ({ value: i.id, label: labelFor(i) }));
  optionsCache[source] = { ts: Date.now(), data };
  return data;
}
function invalidateOptions(source) {
  delete optionsCache[source];
}

async function fetchList() {
  const cfg = ENTITIES[state.entity];
  let path;

  if (cfg.scopedByTask) {
    if (!state.selectedTaskId) return { items: [], meta: null };
    path = `/tasks/${state.selectedTaskId}/comments`;
  } else if (cfg.paginated) {
    const params = new URLSearchParams({
      page: state.page,
      page_size: state.pageSize,
    });
    if (state.search) params.set("search", state.search);
    Object.entries(state.filters).forEach(([k, v]) => {
      if (v) params.set(k, v);
    });
    path = `${cfg.endpoint}?${params.toString()}`;
  } else {
    path = cfg.endpoint;
  }

  document.getElementById("methodLabel").textContent = "GET";
  document.getElementById("requestPath").textContent = path;
  const raw = await apiFetch(path);
  return unwrapEnvelope(raw);
}

async function createItem(payload) {
  const cfg = ENTITIES[state.entity];
  document.getElementById("methodLabel").textContent = "POST";
  document.getElementById("requestPath").textContent = cfg.endpoint;
  return apiFetch(cfg.endpoint, { method: "POST", body: payload });
}
async function updateItem(id, payload) {
  const cfg = ENTITIES[state.entity];
  const path = `${cfg.endpoint}/${id}`;
  document.getElementById("methodLabel").textContent = "PATCH";
  document.getElementById("requestPath").textContent = path;
  return apiFetch(path, { method: "PATCH", body: payload });
}
async function deleteItem(id) {
  const cfg = ENTITIES[state.entity];
  const path = `${cfg.endpoint}/${id}`;
  document.getElementById("methodLabel").textContent = "DELETE";
  document.getElementById("requestPath").textContent = path;
  return apiFetch(path, { method: "DELETE" });
}

async function checkHealth() {
  const dot = document.getElementById("statusDot");
  const text = document.getElementById("statusText");
  try {
    const r = await fetch(healthUrl());
    if (!r.ok) throw new Error();
    dot.className = "status-dot ok";
    text.textContent = "connected";
  } catch {
    dot.className = "status-dot bad";
    text.textContent = "unreachable — check CORS & that the server is running";
  }
}

// ---------------------------------------------------------------------
// 5. Rendering
// ---------------------------------------------------------------------
function fmtDate(v) {
  if (!v) return "—";
  const d = new Date(v);
  return isNaN(d)
    ? v
    : d.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
}
function truncate(str, n) {
  if (!str) return "—";
  return str.length > n ? str.slice(0, n) + "…" : str;
}
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function renderTableHead() {
  const cfg = ENTITIES[state.entity];
  const head = document.getElementById("tableHead");
  head.innerHTML = `<tr>${cfg.columns.map((c) => `<th>${c.label}</th>`).join("")}<th></th></tr>`;
}

function renderTableRows(items) {
  const cfg = ENTITIES[state.entity];
  const body = document.getElementById("tableBody");
  const emptyState = document.getElementById("emptyState");

  if (!items.length) {
    body.innerHTML = "";
    emptyState.classList.remove("hidden");
    document.querySelector("#emptyState .empty-sub").textContent =
      cfg.scopedByTask && !state.selectedTaskId
        ? "Pick a task above to see its comments."
        : "Create one to get started, or check your backend connection above.";
    return;
  }
  emptyState.classList.add("hidden");

  body.innerHTML = items
    .map((item) => {
      const cells = cfg.columns
        .map((col) => {
          let val = item[col.key];
          if (col.date) val = fmtDate(val);
          else if (col.badge)
            val = `<span class="badge badge-${val}">${val ?? "—"}</span>`;
          else if (col.truncate) val = escapeHtml(truncate(val, col.truncate));
          else
            val =
              val === null || val === undefined || val === ""
                ? "—"
                : escapeHtml(String(val));
          return `<td class="${col.mono ? "mono" : ""}">${val}</td>`;
        })
        .join("");

      const actions = cfg.editable
        ? `<button class="edit-btn" data-id="${item.id}">Edit</button><button class="delete-btn" data-id="${item.id}">Delete</button>`
        : `<button class="delete-btn" data-id="${item.id}">Delete</button>`;

      return `<tr>${cells}<td><div class="row-actions">${actions}</div></td></tr>`;
    })
    .join("");

  body
    .querySelectorAll(".edit-btn")
    .forEach((btn) =>
      btn.addEventListener("click", () =>
        openModal("edit", btn.dataset.id, items),
      ),
    );
  body
    .querySelectorAll(".delete-btn")
    .forEach((btn) =>
      btn.addEventListener("click", () => confirmDelete(btn.dataset.id)),
    );
}

function renderFilters() {
  const cfg = ENTITIES[state.entity];
  const slot = document.getElementById("filterSlot");
  slot.innerHTML = "";
  state.filters = {};
  if (!cfg.filters) return;
  cfg.filters.forEach((f) => {
    const sel = document.createElement("select");
    const opts = f.options.map((o) =>
      typeof o === "string" ? { value: o, label: o } : o,
    );
    sel.innerHTML =
      `<option value="">${f.label}</option>` +
      opts
        .map((o) => `<option value="${o.value}">${o.label}</option>`)
        .join("");
    sel.addEventListener("change", () => {
      state.filters[f.key] = sel.value;
      state.page = 1;
      loadAndRender();
    });
    slot.appendChild(sel);
  });
}

async function populateTaskSelector() {
  const bar = document.getElementById("taskSelectorBar");
  const sel = document.getElementById("commentTaskSelect");
  try {
    const opts = await fetchOptions("tasks");
    sel.innerHTML = opts
      .map((o) => `<option value="${o.value}">${escapeHtml(o.label)}</option>`)
      .join("");
    if (!state.selectedTaskId && opts.length)
      state.selectedTaskId = opts[0].value;
    sel.value = state.selectedTaskId ?? "";
    bar.classList.remove("hidden");
  } catch {
    sel.innerHTML = `<option>Could not load tasks</option>`;
    bar.classList.remove("hidden");
  }
}

async function loadAndRender() {
  const cfg = ENTITIES[state.entity];
  const loading = document.getElementById("loadingState");
  const errorState = document.getElementById("errorState");
  loading.classList.remove("hidden");
  errorState.classList.add("hidden");
  document.getElementById("emptyState").classList.add("hidden");
  document.getElementById("dataTable").style.opacity = "0.4";

  const paginationBar = document.getElementById("paginationBar");
  const countBar = document.getElementById("countBar");

  try {
    const { items, meta } = await fetchList();
    lastLoadedItems = items;
    renderTableRows(items);

    if (cfg.paginated && meta) {
      paginationBar.classList.remove("hidden");
      countBar.classList.add("hidden");
      state.totalPages = meta.total_pages || 1;
      document.getElementById("pageInfo").textContent =
        `Page ${meta.page} of ${meta.total_pages} · ${meta.total_items} total`;
      document.getElementById("prevPage").disabled = meta.page <= 1;
      document.getElementById("nextPage").disabled =
        meta.page >= meta.total_pages;
    } else {
      paginationBar.classList.add("hidden");
      countBar.classList.remove("hidden");
      document.getElementById("countInfo").textContent =
        `${items.length} item${items.length === 1 ? "" : "s"}`;
    }
  } catch (err) {
    document.getElementById("tableBody").innerHTML = "";
    errorState.classList.remove("hidden");
    document.getElementById("errorText").textContent =
      `Request failed: ${err.message}`;
    paginationBar.classList.add("hidden");
    countBar.classList.add("hidden");
  } finally {
    loading.classList.add("hidden");
    document.getElementById("dataTable").style.opacity = "1";
  }
  checkHealth();
}

// ---------------------------------------------------------------------
// 6. Modal — create / edit form
// ---------------------------------------------------------------------
async function buildFieldHtml(f, existing) {
  const val = existing?.[f.key] ?? f.default ?? "";
  const req = f.required ? "required" : "";

  if (f.type === "textarea") {
    return `<label>${f.label}${f.required ? " *" : ""}
      <textarea name="${f.key}" ${req}>${escapeHtml(val)}</textarea>
    </label>`;
  }
  if (f.type === "select") {
    return `<label>${f.label}${f.required ? " *" : ""}
      <select name="${f.key}" ${req}>
        <option value="">Select…</option>
        ${f.options.map((o) => `<option value="${o}" ${o === val ? "selected" : ""}>${o}</option>`).join("")}
      </select>
    </label>`;
  }
  if (f.type === "select-remote") {
    let opts = [];
    try {
      opts = await fetchOptions(f.source);
    } catch {
      /* fall through */
    }
    const optionsHtml = opts.length
      ? opts
          .map(
            (o) =>
              `<option value="${o.value}" ${String(o.value) === String(val) ? "selected" : ""}>${escapeHtml(o.label)}</option>`,
          )
          .join("")
      : `<option value="">Could not load ${f.source}</option>`;
    return `<label>${f.label}${f.required ? " *" : ""}
      <select name="${f.key}" ${req}>
        <option value="">Select…</option>
        ${optionsHtml}
      </select>
    </label>`;
  }
  return `<label>${f.label}${f.required ? " *" : ""}
    <input type="${f.type}" name="${f.key}" value="${escapeHtml(String(val))}" ${req}>
  </label>`;
}

async function openModal(mode, id, items) {
  const cfg = ENTITIES[state.entity];
  state.editingId = mode === "edit" ? id : null;
  const existing =
    mode === "edit"
      ? { ...items.find((i) => String(i.id) === String(id)) }
      : {};
  const fieldList = mode === "edit" ? cfg.fields.edit : cfg.fields.create;

  document.getElementById("modalTitle").textContent =
    mode === "edit"
      ? `Edit ${cfg.label.slice(0, -1)}`
      : `New ${cfg.label.slice(0, -1)}`;

  const form = document.getElementById("modalForm");
  form.innerHTML = `<div class="mono muted" style="font-size:11px;">loading form…</div>`;

  if (
    state.entity === "comments" &&
    mode === "create" &&
    state.selectedTaskId
  ) {
    existing.task_id = state.selectedTaskId;
  }

  const fieldsHtml = await Promise.all(
    fieldList.map((f) => buildFieldHtml(f, existing)),
  );
  form.innerHTML =
    fieldsHtml.join("") +
    `<div class="modal-form-error hidden" id="formError"></div>
     <div class="form-actions">
       <button type="button" class="btn btn-ghost" id="cancelForm">Cancel</button>
       <button type="submit" class="btn btn-primary">${mode === "edit" ? "Save changes" : "Create"}</button>
     </div>`;

  document.getElementById("cancelForm").addEventListener("click", closeModal);
  form.onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(form);
    const payload = {};
    fieldList.forEach((f) => {
      let v = formData.get(f.key);
      if (f.type === "select-remote") v = v === "" ? null : Number(v);
      if (f.type === "date" && v) v = `${v}T00:00:00`;
      if (v === "") v = null;
      payload[f.key] = v;
    });
    try {
      if (mode === "edit") await updateItem(id, payload);
      else await createItem(payload);
      closeModal();
      showToast(mode === "edit" ? "Saved changes" : "Created", "success");
      invalidateOptions(state.entity);
      loadAndRender();
    } catch (err) {
      const errBox = document.getElementById("formError");
      errBox.textContent = err.message;
      errBox.classList.remove("hidden");
    }
  };

  document.getElementById("modalOverlay").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("modalOverlay").classList.add("hidden");
}

async function confirmDelete(id) {
  const cfg = ENTITIES[state.entity];
  if (
    !confirm(
      `Delete this ${cfg.label.slice(0, -1).toLowerCase()}? This can't be undone.`,
    )
  )
    return;
  try {
    await deleteItem(id);
    showToast("Deleted", "success");
    invalidateOptions(state.entity);
    loadAndRender();
  } catch (err) {
    showToast(`Delete failed: ${err.message}`, "error");
  }
}

function showToast(msg, kind) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.className = `toast toast-${kind}`;
  toast.classList.remove("hidden");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.add("hidden"), 2600);
}

// ---------------------------------------------------------------------
// 7. Wiring
// ---------------------------------------------------------------------
async function switchEntity(entity) {
  state.entity = entity;
  state.page = 1;
  state.search = "";
  document.getElementById("searchInput").value = "";

  document
    .querySelectorAll(".nav-item")
    .forEach((b) =>
      b.classList.toggle("is-active", b.dataset.entity === entity),
    );
  document.getElementById("entityTitle").textContent = ENTITIES[entity].label;

  const cfg = ENTITIES[entity];
  const searchInput = document.getElementById("searchInput");
  searchInput.classList.toggle("hidden", !cfg.searchable);
  if (cfg.searchPlaceholder) searchInput.placeholder = cfg.searchPlaceholder;

  const createBtn = document.getElementById("createBtn");
  createBtn.textContent = `+ New ${cfg.label.slice(0, -1)}`;

  const taskSelectorBar = document.getElementById("taskSelectorBar");
  if (cfg.scopedByTask) {
    await populateTaskSelector();
  } else {
    taskSelectorBar.classList.add("hidden");
  }

  renderTableHead();
  renderFilters();
  loadAndRender();
}

function init() {
  document.getElementById("backendSelect").value = currentBackend;

  document
    .querySelectorAll(".nav-item")
    .forEach((btn) =>
      btn.addEventListener("click", () => switchEntity(btn.dataset.entity)),
    );

  document.getElementById("backendSelect").addEventListener("change", (e) => {
    currentBackend = e.target.value;
    safeSet("backend", currentBackend);
    Object.keys(optionsCache).forEach(invalidateOptions);
    loadAndRender();
  });

  document
    .getElementById("createBtn")
    .addEventListener("click", () => openModal("create"));
  document.getElementById("modalClose").addEventListener("click", closeModal);
  document.getElementById("modalOverlay").addEventListener("click", (e) => {
    if (e.target.id === "modalOverlay") closeModal();
  });

  document
    .getElementById("commentTaskSelect")
    .addEventListener("change", (e) => {
      state.selectedTaskId = Number(e.target.value);
      loadAndRender();
    });

  let searchDebounce;
  document.getElementById("searchInput").addEventListener("input", (e) => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      state.search = e.target.value;
      state.page = 1;
      loadAndRender();
    }, 350);
  });

  document.getElementById("prevPage").addEventListener("click", () => {
    if (state.page > 1) {
      state.page--;
      loadAndRender();
    }
  });
  document.getElementById("nextPage").addEventListener("click", () => {
    if (state.page < state.totalPages) {
      state.page++;
      loadAndRender();
    }
  });
  document.getElementById("pageSizeSelect").addEventListener("change", (e) => {
    state.pageSize = Number(e.target.value);
    state.page = 1;
    loadAndRender();
  });

  document.getElementById("editBaseUrl").addEventListener("click", () => {
    document.getElementById("flaskUrlInput").value = BASES.flask;
    document.getElementById("fastapiUrlInput").value = BASES.fastapi;
    document.getElementById("urlModalOverlay").classList.remove("hidden");
  });
  document
    .getElementById("urlModalClose")
    .addEventListener("click", () =>
      document.getElementById("urlModalOverlay").classList.add("hidden"),
    );
  document.getElementById("saveUrls").addEventListener("click", () => {
    BASES.flask =
      document.getElementById("flaskUrlInput").value.trim() ||
      DEFAULT_BASES.flask;
    BASES.fastapi =
      document.getElementById("fastapiUrlInput").value.trim() ||
      DEFAULT_BASES.fastapi;
    document.getElementById("urlModalOverlay").classList.add("hidden");
    loadAndRender();
  });

  switchEntity("projects");
}

document.addEventListener("DOMContentLoaded", init);
