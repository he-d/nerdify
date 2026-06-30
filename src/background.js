// Nerdify — background service worker
// Sets sensible defaults on first install.

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    chrome.storage.sync.set({
      globalEnabled: false,
      font: "jetbrainsmono",
      scope: "all",
      siteOverrides: {},
    });
  }
});
