self.addEventListener("install", function (event) {
  console.log("✅ Service Worker installed");
});

self.addEventListener("activate", function (event) {
  console.log("🚀 Service Worker activated");
});

self.addEventListener("push", function (event) {
  console.log("📩 Push event received:", event.data && event.data.text());
  const data = event.data ? event.data.text() : "你有一条新通知";

  event.waitUntil(
    self.registration.showNotification("🔔 通知提醒", {
      body: data,
      icon: "/icon.png",
    })
  );
});
