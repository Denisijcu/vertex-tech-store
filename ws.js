/* Vertex Tech Store — Service Worker (PWA) */
const VERSION = "v1";
const STATIC_CACHE = `vertex-static-${VERSION}`;
const PRECACHE = ["/", "/index.html", "/manifest.json"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== STATIC_CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

/* Estrategias:
   - API (/products, /chat): network-first, SIN cachear, fallback 503 JSON
   - Navegación HTML: network-first con fallback a cache
   - Assets estáticos: cache-first                                         */
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET") return;

  if (url.pathname.startsWith("/products") || url.pathname.startsWith("/chat")) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({ ok: false, error: "offline" }), {
          status: 503, headers: { "Content-Type": "application/json" },
        })
      )
    );
    return;
  }

  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(() =>
        caches.match(event.request).then((r) => r || caches.match("/index.html"))
      )
    );
    return;
  }

  if (["style", "script", "image", "font"].includes(event.request.destination)) {
    event.respondWith(
      caches.match(event.request).then(
        (cached) =>
          cached ||
          fetch(event.request).then((res) => {
            const clone = res.clone();
            caches.open(STATIC_CACHE).then((c) => c.put(event.request, clone));
            return res;
          })
      )
    );
  }
});
