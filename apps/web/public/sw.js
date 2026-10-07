self.addEventListener("push", (event) => {
  const data = event.data ? event.data.json() : {};
  event.waitUntil(
    self.registration.showNotification(data.title || "Resumen", {
      body: data.body || "",
      data: { url: data.url || "/resumen" },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const path = event.notification.data?.url || "/resumen";
  const target = new URL(path, self.registration.scope).href;
  event.waitUntil(self.clients.openWindow(target));
});
