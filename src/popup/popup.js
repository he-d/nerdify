const DEFAULTS = {
  globalEnabled: false,
  font: "anonymicepronerdfontmono",
  scope: "all",
  siteOverrides: {},
};

let currentHost = "";

function $(sel) {
  return document.querySelector(sel);
}

function getActiveTabHostname() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      try {
        const url = new URL(tabs[0]?.url || "");
        resolve(url.hostname || "");
      } catch {
        resolve("");
      }
    });
  });
}

function render(settings) {
  // Global toggle
  $("#globalToggle").checked = !!settings.globalEnabled;
  $("#globalHint").textContent = settings.globalEnabled
    ? "On everywhere unless overridden per site"
    : "Off everywhere unless overridden per site";

  // Site name + override buttons
  $("#siteName").textContent = currentHost || "—";
  const override = settings.siteOverrides?.[currentHost] || "inherit";
  document.querySelectorAll(".site-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.value === override);
  });

  // Scope buttons
  document.querySelectorAll(".scope-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.value === settings.scope);
  });

  // Font options
  document.querySelectorAll(".font-option").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.font === settings.font);
  });
}

function loadAndRender() {
  chrome.storage.sync.get(DEFAULTS, render);
}

function updateSettings(patch) {
  chrome.storage.sync.get(DEFAULTS, (settings) => {
    const merged = { ...settings, ...patch };
    chrome.storage.sync.set(merged, () => render(merged));
  });
}

function updateSiteOverride(value) {
  chrome.storage.sync.get(DEFAULTS, (settings) => {
    const siteOverrides = { ...(settings.siteOverrides || {}) };
    if (value === "inherit") {
      delete siteOverrides[currentHost];
    } else {
      siteOverrides[currentHost] = value;
    }
    const merged = { ...settings, siteOverrides };
    chrome.storage.sync.set(merged, () => render(merged));
  });
}

async function init() {
  currentHost = await getActiveTabHostname();
  loadAndRender();

  $("#globalToggle").addEventListener("change", (e) => {
    updateSettings({ globalEnabled: e.target.checked });
  });

  document.querySelectorAll(".site-btn").forEach((btn) => {
    btn.addEventListener("click", () => updateSiteOverride(btn.dataset.value));
  });

  document.querySelectorAll(".scope-btn").forEach((btn) => {
    btn.addEventListener("click", () => updateSettings({ scope: btn.dataset.value }));
  });

  document.querySelectorAll(".font-option").forEach((btn) => {
    btn.addEventListener("click", () => updateSettings({ font: btn.dataset.font }));
  });
}

init();
