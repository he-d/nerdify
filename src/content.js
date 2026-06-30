// Nerdify — content script
// Reads global + per-site settings from chrome.storage.sync and applies
// the chosen Nerd Font to the page via a CSS variable + marker class.

const FONT_MAP = {
  anonymicepronerdfontmono: "AnonymicePro Nerd Font Mono",
  caskaydiacovenerdfontmono: "CaskaydiaCove Nerd Font Mono",
  firacodenerdfontmono: "FiraCode Nerd Font Mono",
  hacknerdfontmono: "Hack Nerd Font Mono",
  iosevkanerdfontmono: "Iosevka Nerd Font Mono",
  jetbrainsmononerdfontmono: "JetBrainsMono Nerd Font Mono",
  meslolgsnerdfontmono: "MesloLGS Nerd Font Mono",
  saucecodepronerdfontmono: "SauceCodePro Nerd Font Mono",
  victormononerdfontmono: "VictorMono Nerd Font Mono",
};

const DEFAULTS = {
  globalEnabled: false,
  font: "anonymicepronerdfontmono",
  scope: "all", // "all" | "code"
  siteOverrides: {}, // { "example.com": "on" | "off" | "inherit" }
};

function getHostname() {
  try {
    return location.hostname;
  } catch {
    return "";
  }
}

function resolveEffectiveState(settings) {
  const host = getHostname();
  const override = settings.siteOverrides?.[host] || "inherit";

  let enabled;
  if (override === "on") enabled = true;
  else if (override === "off") enabled = false;
  else enabled = settings.globalEnabled;

  return {
    enabled,
    font: settings.font || DEFAULTS.font,
    scope: settings.scope || DEFAULTS.scope,
  };
}

function applyState(state) {
  const root = document.documentElement;
  root.classList.remove("nf-active-all", "nf-active-code");

  if (!state.enabled) {
    root.style.removeProperty("--nf-font-family");
    return;
  }

  const fontFamily = FONT_MAP[state.font] || FONT_MAP[DEFAULTS.font];
  root.style.setProperty("--nf-font-family", `"${fontFamily}"`);
  root.classList.add(state.scope === "code" ? "nf-active-code" : "nf-active-all");
}

function loadAndApply() {
  chrome.storage.sync.get(DEFAULTS, (settings) => {
    const state = resolveEffectiveState(settings);
    applyState(state);
  });
}

// Initial application — run_at document_start, so also re-apply on DOMContentLoaded
// in case very early page scripts strip classes/styles from <html>.
loadAndApply();
document.addEventListener("DOMContentLoaded", loadAndApply);

// React live to changes made from the popup
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "sync") {
    loadAndApply();
  }
});
