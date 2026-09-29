const API = "/api";
const TOKEN_KEY = "healthcare_access";
const USER_KEY = "healthcare_user";
const SECTIONS = {
  patients: {
    title: "Patients",
    kicker: "YOUR RECORDS",
    description: "Your patient records, all in one place.",
    collection: "patients",
    addLabel: "Add patient",
    emptyLabel: "Add your first patient",
  },
  doctors: {
    title: "Doctors",
    kicker: "DOCTOR DIRECTORY",
    description: "Find and manage doctors in your shared directory.",
    collection: "doctors",
    addLabel: "Add doctor",
    emptyLabel: "Add your first doctor",
  },
  mappings: {
    title: "Care teams",
    kicker: "CONNECTED CARE",
    description: "See which doctors are caring for your patients.",
    collection: "mappings",
    addLabel: "Assign a doctor",
    emptyLabel: "Create your first assignment",
  },
};

const authScreen = document.querySelector("#auth-screen");
const workspace = document.querySelector("#workspace");
const authForm = document.querySelector("#auth-form");
const authMessage = document.querySelector("#auth-message");
const nameField = document.querySelector("#name-field");
const recordForm = document.querySelector("#record-form");
const recordList = document.querySelector("#record-list");
const emptyState = document.querySelector("#empty-state");
const notice = document.querySelector("#notice");

let authMode = "login";
let currentSection = "patients";
let records = [];
let patients = [];
let doctors = [];

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

function setSession(data) {
  sessionStorage.setItem(TOKEN_KEY, data.access);
  sessionStorage.setItem(USER_KEY, JSON.stringify(data.user));
  showWorkspace(data.user);
}

function showWorkspace(user) {
  authScreen.hidden = true;
  workspace.hidden = false;
  document.querySelector("#account-area").hidden = false;
  document.querySelector("#account-name").textContent = user.name || user.email;
  loadSection(currentSection);
}

function showAuth() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
  workspace.hidden = true;
  document.querySelector("#account-area").hidden = true;
  authScreen.hidden = false;
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (getToken()) {
    headers.set("Authorization", `Bearer ${getToken()}`);
  }
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (response.status === 401 && getToken()) {
    showAuth();
    throw new Error("Your session expired. Please sign in again.");
  }
  if (response.status === 204) return null;

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(formatError(data));
  }
  return data;
}

function formatError(data) {
  if (data.detail) return data.detail;
  return Object.entries(data)
    .map(([field, messages]) => {
      const text = Array.isArray(messages) ? messages.join(" ") : String(messages);
      return `${field}: ${text}`;
    })
    .join(" ") || "Something went wrong. Please try again.";
}

async function loadAll(path) {
  let next = `${API}/${path}/`;
  const items = [];
  while (next) {
    const url = new URL(next, window.location.origin);
    const apiPath = `${url.pathname.replace(/^\/api/, "")}${url.search}`;
    const page = await request(apiPath);
    items.push(...(page.results || []));
    next = page.next;
  }
  return items;
}

function setAuthMode(mode) {
  authMode = mode;
  const registering = mode === "register";
  nameField.hidden = !registering;
  authForm.elements.password.autocomplete = registering ? "new-password" : "current-password";
  document.querySelector("#auth-title").textContent = registering ? "Create your account" : "Welcome back";
  document.querySelector("#auth-description").textContent = registering
    ? "Set up your account to start organizing care."
    : "Sign in to continue to your workspace.";
  document.querySelector("#auth-submit").innerHTML = registering
    ? 'Create account <span aria-hidden="true">→</span>'
    : 'Sign in <span aria-hidden="true">→</span>';
  document.querySelector("#login-tab").classList.toggle("active", !registering);
  document.querySelector("#register-tab").classList.toggle("active", registering);
  document.querySelector("#login-tab").setAttribute("aria-selected", String(!registering));
  document.querySelector("#register-tab").setAttribute("aria-selected", String(registering));
  authMessage.textContent = "";
}

async function handleAuth(event) {
  event.preventDefault();
  authMessage.textContent = "";
  const values = Object.fromEntries(new FormData(authForm).entries());
  const submit = document.querySelector("#auth-submit");
  submit.disabled = true;

  try {
    if (authMode === "register") {
      await request("/auth/register/", {
        method: "POST",
        body: JSON.stringify({
          name: values.name,
          email: values.email,
          password: values.password,
        }),
      });
    }
    const data = await request("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email: values.email, password: values.password }),
    });
    setSession(data);
  } catch (error) {
    authMessage.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
}

async function loadSection(section) {
  currentSection = section;
  const config = SECTIONS[section];
  document.querySelectorAll(".nav-tab").forEach((tab) => {
    const active = tab.dataset.section === section;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-current", active ? "page" : "false");
  });
  document.querySelector("#section-kicker").textContent = config.kicker;
  document.querySelector("#section-title").textContent = config.title;
  document.querySelector("#section-description").textContent = config.description;
  document.querySelector("#new-record").innerHTML = `<span aria-hidden="true">+</span> ${config.addLabel}`;
  document.querySelector("#empty-add").textContent = config.emptyLabel;
  recordForm.hidden = true;
  recordForm.replaceChildren();
  showNotice("");
  recordList.innerHTML = '<p class="record-meta">Loading your records…</p>';
  emptyState.hidden = true;

  try {
    if (section === "mappings") {
      [patients, doctors, records] = await Promise.all([
        loadAll("patients"),
        loadAll("doctors"),
        loadAll("mappings"),
      ]);
    } else {
      records = await loadAll(config.collection);
      if (section === "patients") patients = records;
      if (section === "doctors") doctors = records;
    }
    renderRecords();
  } catch (error) {
    recordList.replaceChildren();
    showNotice(error.message, true);
  }
}

function renderRecords() {
  recordList.replaceChildren();
  if (records.length === 0) {
    emptyState.hidden = false;
    return;
  }
  emptyState.hidden = true;
  records.forEach((record) => {
    const config = SECTIONS[currentSection];
    const patient = patients.find((item) => item.id === record.patient_id);
    const doctor = doctors.find((item) => item.id === record.doctor_id);
    const title = currentSection === "mappings"
      ? `${patient?.name || `Patient #${record.patient_id}`} · ${doctor?.name || `Doctor #${record.doctor_id}`}`
      : record.name;
    const subtitle = currentSection === "patients"
      ? `${record.age} years · ${record.gender}${record.email ? ` · ${record.email}` : ""}`
      : currentSection === "doctors"
        ? `${record.specialization}${record.email ? ` · ${record.email}` : ""}`
        : `Assigned ${new Date(record.created_at).toLocaleDateString()}`;

    const row = document.createElement("article");
    row.className = "record";
    const main = document.createElement("div");
    main.className = "record-main";
    const avatar = document.createElement("span");
    avatar.className = "record-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = currentSection === "mappings" ? "+" : record.name.slice(0, 1).toUpperCase();
    const details = document.createElement("div");
    const name = document.createElement("p");
    name.className = "record-name";
    name.textContent = title;
    const meta = document.createElement("p");
    meta.className = "record-meta";
    meta.textContent = subtitle;
    details.append(name, meta);
    main.append(avatar, details);

    const actions = document.createElement("div");
    actions.className = "record-actions";
    if (currentSection !== "mappings") {
      actions.append(makeAction("Edit", () => openRecordForm(record)));
    }
    actions.append(makeAction("Delete", () => deleteRecord(record.id), true));
    row.append(main, actions);
    recordList.append(row);
  });
}

function makeAction(label, onClick, danger = false) {
  const button = document.createElement("button");
  button.className = `text-button${danger ? " danger" : ""}`;
  button.type = "button";
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

function createField(label, name, type = "text", options = {}) {
  const wrapper = document.createElement("label");
  wrapper.className = `field${options.wide ? " form-wide" : ""}`;
  const caption = document.createElement("span");
  caption.textContent = label;
  const input = type === "select"
    ? document.createElement("select")
    : type === "textarea"
      ? document.createElement("textarea")
      : document.createElement("input");
  input.name = name;
  input.required = options.required !== false;
  if (type !== "select" && type !== "textarea") input.type = type;
  if (options.maxlength) input.maxLength = options.maxlength;
  if (options.min !== undefined) input.min = options.min;
  if (options.max !== undefined) input.max = options.max;
  if (options.placeholder) input.placeholder = options.placeholder;
  if (options.choices) {
    options.choices.forEach(([value, text]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = text;
      input.append(option);
    });
  }
  wrapper.append(caption, input);
  return wrapper;
}

function openRecordForm(record = null) {
  recordForm.replaceChildren();
  const config = SECTIONS[currentSection];
  recordForm.dataset.id = record ? record.id : "";
  let fields = [];
  if (currentSection === "patients") {
    fields = [
      createField("Patient name", "name", "text", { maxlength: 150 }),
      createField("Age", "age", "number", { min: 0, max: 150 }),
      createField("Gender", "gender", "select", {
        choices: [["female", "Female"], ["male", "Male"], ["other", "Other"]],
      }),
      createField("Email (optional)", "email", "email", { required: false }),
      createField("Phone (optional)", "phone", "tel", { required: false, maxlength: 30 }),
      createField("Address (optional)", "address", "textarea", { required: false, wide: true }),
    ];
  } else if (currentSection === "doctors") {
    fields = [
      createField("Doctor name", "name", "text", { maxlength: 150 }),
      createField("Specialization", "specialization", "text", { maxlength: 120 }),
      createField("Email (optional)", "email", "email", { required: false }),
      createField("Phone (optional)", "phone", "tel", { required: false, maxlength: 30 }),
    ];
  } else {
    fields = [
      createField("Patient", "patient_id", "select", {
        choices: [["", "Choose a patient"], ...patients.map((item) => [item.id, item.name])],
        wide: true,
      }),
      createField("Doctor", "doctor_id", "select", {
        choices: [["", "Choose a doctor"], ...doctors.map((item) => [item.id, item.name])],
        wide: true,
      }),
    ];
  }

  fields.forEach((field) => {
    const input = field.querySelector("input, select, textarea");
    if (record && Object.hasOwn(record, input.name)) {
      input.value = record[input.name] ?? "";
    }
    recordForm.append(field);
  });

  const actions = document.createElement("div");
  actions.className = "form-actions";
  const cancel = document.createElement("button");
  cancel.className = "button button-quiet";
  cancel.type = "button";
  cancel.textContent = "Cancel";
  cancel.addEventListener("click", () => { recordForm.hidden = true; });
  const save = document.createElement("button");
  save.className = "button button-primary";
  save.type = "submit";
  save.textContent = record ? "Save changes" : config.addLabel;
  actions.append(cancel, save);
  recordForm.append(actions);
  recordForm.hidden = false;
  recordForm.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function saveRecord(event) {
  event.preventDefault();
  const config = SECTIONS[currentSection];
  const id = recordForm.dataset.id;
  const payload = Object.fromEntries(new FormData(recordForm).entries());
  if (currentSection === "patients") payload.age = Number(payload.age);
  if (currentSection === "mappings") {
    payload.patient_id = Number(payload.patient_id);
    payload.doctor_id = Number(payload.doctor_id);
  }
  const button = recordForm.querySelector('[type="submit"]');
  button.disabled = true;

  try {
    await request(`/${config.collection}/${id ? `${id}/` : ""}`, {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    recordForm.hidden = true;
    showNotice(id ? "Your changes have been saved." : "Your record has been added.");
    await loadSection(currentSection);
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function deleteRecord(id) {
  if (!window.confirm("Delete this record? This cannot be undone.")) return;
  const config = SECTIONS[currentSection];
  try {
    await request(`/${config.collection}/${id}/`, { method: "DELETE" });
    showNotice("The record has been deleted.");
    await loadSection(currentSection);
  } catch (error) {
    showNotice(error.message, true);
  }
}

function showNotice(message, isError = false) {
  notice.textContent = message;
  notice.classList.toggle("error", isError);
  notice.hidden = !message;
}

document.querySelector("#login-tab").addEventListener("click", () => setAuthMode("login"));
document.querySelector("#register-tab").addEventListener("click", () => setAuthMode("register"));
authForm.addEventListener("submit", handleAuth);
recordForm.addEventListener("submit", saveRecord);
document.querySelector("#new-record").addEventListener("click", () => openRecordForm());
document.querySelector("#empty-add").addEventListener("click", () => openRecordForm());
document.querySelector("#logout-button").addEventListener("click", showAuth);
document.querySelectorAll(".nav-tab").forEach((tab) => {
  tab.addEventListener("click", () => loadSection(tab.dataset.section));
});

try {
  const savedUser = JSON.parse(sessionStorage.getItem(USER_KEY) || "null");
  if (getToken() && savedUser) {
    showWorkspace(savedUser);
  }
} catch {
  showAuth();
}
