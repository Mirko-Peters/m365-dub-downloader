// Worker vor der Plattform (GitHub Pages): Cache- und Sicherheits-Header, Bild-Optimierung (Polish), Weiterleitungen fuer den Umzug von www.m365.fm.
const SEC = {
  "strict-transport-security": "max-age=31536000; includeSubDomains",
  "x-content-type-options": "nosniff",
  "referrer-policy": "strict-origin-when-cross-origin",
  "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=()",
  "x-frame-options": "SAMEORIGIN",
};
const IMG = /\.(png|jpe?g|gif|webp|avif|svg|ico)$/i, STATIC = /^\/(assets|covers|og)\//i, FONT = /\.(woff2?|ttf|otf)$/i;
const HASHED = /^\/assets\/site\.[0-9a-f]{8,}\.css$/i;   // Dateiname traegt den Inhalts-Hash: darf ein Jahr im Browser bleiben
// T41 Caching: HTML 4 h am Rand statt 10 Min (nach jedem Deploy leert tools/purge_changed.py genau die geaenderten Adressen),
// Sprachseiten aus R2 ebenfalls 4 h im Kanten-Cache (Cache API, Schluessel /__r2c/<pfad>/, Purge nach dem Upload), Browser fragt bei HTML immer nach (304 per ETag/Last-Modified)
const EDGE_HTML = 14400, R2_TTL = 14400, R2_MISS_TTL = 600;
const HTML_CC = "public, max-age=0, s-maxage=600, stale-while-revalidate=86400";
const r2Path = (p) => (p.endsWith("/") ? p : p + "/");

function notModified(request, etag, lastMod) {
  const inm = request.headers.get("if-none-match");
  if (inm) return !!etag && inm.split(",").map((x) => x.trim().replace(/^W\//, "")).some((x) => x === "*" || x === etag.replace(/^W\//, ""));
  const ims = request.headers.get("if-modified-since");
  return !!(ims && lastMod && Date.parse(lastMod) <= Date.parse(ims));
}

// Seite aus dem R2-Bucket (pages/<pfad>/index.html) mit Kanten-Cache; null, wenn es sie dort nicht gibt (auch das wird kurz gemerkt)
async function r2Page(request, env, ctx, url, p) {
  const cache = caches.default, ck = new Request(url.origin + "/__r2c" + r2Path(p));
  let hit = await cache.match(ck).catch(() => null), state = "HIT";
  if (!hit) {
    state = "MISS";
    const obj = await env.PAGES.get("pages" + r2Path(p) + "index.html").catch(() => null);
    if (!obj) {
      ctx.waitUntil(cache.put(ck, new Response("", { headers: { "cache-control": `public, max-age=${R2_MISS_TTL}`, "x-r2-miss": "1" } })).catch(() => {}));
      return null;
    }
    hit = new Response(await obj.arrayBuffer(), { headers: { "content-type": "text/html; charset=utf-8", "etag": obj.httpEtag, "last-modified": obj.uploaded.toUTCString(), "cache-control": `public, max-age=${R2_TTL}` } });
    ctx.waitUntil(cache.put(ck, hit.clone()).catch(() => {}));
  }
  if (hit.headers.get("x-r2-miss")) return null;
  const h = new Headers({ "content-type": "text/html; charset=utf-8", "cache-control": HTML_CC, "x-m365-cache": state });
  for (const k of ["etag", "last-modified"]) { const v = hit.headers.get(k); if (v) h.set(k, v); }
  for (const [k, v] of Object.entries(SEC)) h.set(k, v);
  if (notModified(request, h.get("etag"), h.get("last-modified"))) return new Response(null, { status: 304, headers: h });
  return new Response(request.method === "HEAD" ? null : hit.body, { status: 200, headers: h });
}
// Datenexporte des Seitenbaus: fuer Programme da, nicht fuer die Suche (Allowlist - .well-known, openapi.json, agent.json, episodes.json, llms*.txt bleiben sichtbar)
const NOINDEX = /^\/(entities\.json|entities-src\.json|entities\.jsonld|og-manifest\.json|seo-report\.json|top\.json|show\/redirects\.json|show-notes\/|blog-import\/|blog-content\/)|\.jsonld$/i;

async function redirectMap() {
  const r = await fetch("https://www.m365.fm/show/redirects.json", { cf: { cacheTtl: 3600, cacheEverything: true } });
  return r.ok ? r.json() : {};
}
// T8: nur Pfade, die alte Podpage-Adressen sein koennen, fragen die Weiterleitungstabelle ab (keine Dateien, keine Assets);
// unter /show nur die frueheren Blog-Adressen /show/blog/... (dort liegen sonst nur Meta-Refresh-Seiten).
const MAPPABLE = (p) => p !== "/" && !/\.[a-z0-9]{2,5}$/i.test(p) && !/^\/(assets|og|covers|fonts|\.well-known)(\/|$)/i.test(p)
  && (!/^\/shows?(\/|$)/.test(p) || p === "/show/blog" || p.startsWith("/show/blog/"));   // nur /show und /shows selbst ausnehmen, nicht Slugs wie /showback-…
async function legacyTarget(p0) {
  if (!MAPPABLE(p0)) return "";
  const map = await redirectMap();
  if (map[p0] || map[p0.toLowerCase()]) return map[p0] || map[p0.toLowerCase()];
  const m = /^\/m365-fm-podcast\/([a-z0-9-]+)$/.exec(p0);   // T8: Podpage-Folgenadressen unter dem Shownamen
  if (m) return "/show/episodes/" + m[1] + "/";
  if (/^\/categories(\/|$)/.test(p0)) return "/show/episodes/";   // T8: Podpage-Kategorien -> Folgenliste
  return /^\/(blog|videos|p)\//.test(p0) ? "/show/" : "";
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    // Umzug (MIGRATED=1): dub.m365.fm und m365.fm -> www.m365.fm, alte Podpage-Adressen -> /show/ (301, damit der SEO-Traffic erhalten bleibt)
    if (env.MIGRATED === "1") {
      const p0 = url.pathname.replace(/\/+$/, "") || "/";
      let to = await legacyTarget(p0);
      // T8: dub.m365.fm/m365.fm und alte Adresse in einem Schritt auf das Ziel (vorher zwei 301 hintereinander)
      if (url.hostname === "dub.m365.fm" || url.hostname === "m365.fm") {
        if (!to && /^(\/[a-z]{2})?\/show\/episodes\/[a-z0-9-]+$/.test(p0)) to = (await redirectMap())[p0] || "";   // T12: umbenannte Folge auch vom alten Host in einem Schritt
        return Response.redirect("https://www.m365.fm" + (to || url.pathname) + url.search, 301);
      }
      if (to) return Response.redirect(url.origin + to + url.search, 301);
    }
    { const mp = /^(\/[a-z]{2})?\/community\/u\/mirko-peters(\/.*)?$/.exec(url.pathname); if (mp) return Response.redirect(url.origin + (mp[1] || "") + "/community/u/mirko-p" + (mp[2] || "/") + url.search, 301); }   // alter Name des Blog-Profils
    if (/^\/(pa|hi|ml|ta|te)(\/|$)/.test(url.pathname)) return Response.redirect(url.origin + "/", 301);   // diese Sprachen gibt es nicht mehr (Punjabi, Hindi, Malayalam, Tamil, Telugu)
    const p = url.pathname, isImg = IMG.test(p), isStatic = STATIC.test(p) || FONT.test(p);
    if (p.startsWith("/__r2c/")) return new Response("Not found", { status: 404 });   // interner Cache-Schluessel, keine oeffentliche Adresse
    const cf = isImg ? { cacheEverything: true, cacheTtl: 604800, polish: "lossy", mirage: true }
      : isStatic ? { cacheEverything: true, cacheTtl: 86400 }
      : { cacheEverything: true, cacheTtlByStatus: { "200-299": EDGE_HTML, "404": 60, "500-599": 0 } };   // HTML: 4 h am Rand, Purge nach jedem Deploy
    // T41: ohne Query zum Ursprung - GitHub Pages ist statisch, so landen ?utm_…/?fbclid=… im selben Cache-Eintrag (Zone steht auf Caching-Level "basic": mit Query sonst gar kein Cache)
    const res = await fetch(url.search ? new Request(url.origin + p, request) : request, { cf });
    // Seiten aus dem R2-Bucket (Paket 20): uebersetzte Seiten (Blog-Sprachfassungen, Sprachfassungen der Folgen) liegen unter pages/<pfad>/index.html im Bucket statt in GitHub Pages - gleiche Adressen, indexierbar
    if (res.status === 404 && env.MIGRATED === "1" && /^(\/[a-z]{2})?\/show\/episodes\/[a-z0-9-]+\/?$/.test(p)) {   // T12: umbenannte Folge (show/redirects.json), vor dem R2-Rueckfall mit der alten Seite
      const to = (await redirectMap())[p.replace(/\/+$/, "")];
      if (to) return Response.redirect(url.origin + to + url.search, 301);
    }
    if (res.status === 404 && env.PAGES && !IMG.test(p) && (request.method === "GET" || request.method === "HEAD")) {
      const r2 = await r2Page(request, env, ctx, url, p);
      if (r2) return r2;
      const m = /^\/(de|es|fr|it|pt|nl|pl|id|ru|uk|ar|he|ja|ko)\/show\/episodes\/([a-z0-9-]+)\/?$/.exec(p);   // noch nicht hochgeladen: englisches Original statt 404
      if (m) return Response.redirect(url.origin + "/show/episodes/" + m[2] + "/", 301);
    }
    const h = new Headers(res.headers);
    for (const [k, v] of Object.entries(SEC)) h.set(k, v);
    // T41: Schriften aendern sich unter gleichem Namen nicht (1 Jahr), Bilder 1 Tag, Skripte/Stile 1 h und danach im Hintergrund pruefen
    h.set("cache-control", HASHED.test(p) || FONT.test(p) ? "public, max-age=31536000, immutable" : isImg ? "public, max-age=86400, stale-while-revalidate=604800"
      : isStatic ? "public, max-age=3600, s-maxage=86400, stale-while-revalidate=86400" : HTML_CC);
    if (NOINDEX.test(p)) h.set("x-robots-tag", "noindex");
    if (isImg) h.set("vary", "accept");
    if (p === "/") h.set("link", '</.well-known/api-catalog>; rel="api-catalog", </openapi.json>; rel="service-desc"; type="application/vnd.oai.openapi+json", </llms.txt>; rel="service-doc"; type="text/plain", </.well-known/agent.json>; rel="describedby"; type="application/json"');   // RFC 8288 / 9727: Startseite verweist auf maschinenlesbare Ressourcen
    if (p === "/.well-known/api-catalog") { h.set("content-type", 'application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"'); h.set("access-control-allow-origin", "*"); }
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers: h });
  },
};
