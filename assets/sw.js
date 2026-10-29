// Service Worker nur fuer Web-Push (kein Caching)
self.addEventListener("push", function (e) {
  var d = {}; try { d = e.data ? e.data.json() : {}; } catch (x) {}
  e.waitUntil(self.registration.showNotification(d.title || "M365.FM", { body: d.body || "", icon: "/assets/favicon-192.png", badge: "/assets/favicon-32.png", tag: d.tag || "m365", data: { url: d.url || "/" } }));
});
self.addEventListener("notificationclick", function (e) {
  e.notification.close();
  var u = (e.notification.data && e.notification.data.url) || "/";
  try { if (new URL(u, self.location.origin).origin !== self.location.origin) u = "/"; } catch (x) { u = "/"; }
  e.waitUntil(clients.matchAll({ type: "window" }).then(function (cs) { for (var i = 0; i < cs.length; i++) if (cs[i].url === u && "focus" in cs[i]) return cs[i].focus(); return clients.openWindow(u); }));
});
