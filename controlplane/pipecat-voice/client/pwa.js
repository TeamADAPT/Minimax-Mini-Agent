"use strict";

window.addEventListener("DOMContentLoaded", () => {
  if (!("serviceWorker" in navigator) || !("caches" in window)) {
    return;
  }

  (async () => {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(registrations.map((registration) => registration.unregister()));

    for (let pass = 0; pass < 3; pass += 1) {
      const keys = await caches.keys();
      await Promise.all(keys.map((key) => caches.delete(key)));
      await new Promise((resolve) => setTimeout(resolve, 150));
    }

    if (!sessionStorage.getItem("blackline-cache-reset-v7")) {
      sessionStorage.setItem("blackline-cache-reset-v7", "1");
      location.replace(location.href);
    }
  })().catch((error) => {
    console.warn("service worker cache reset failed", error);
  });
});
