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
// Datenexporte des Seitenbaus: fuer Programme da, nicht fuer die Suche (Allowlist - .well-known, openapi.json, agent.json, episodes.json, llms*.txt bleiben sichtbar)
const NOINDEX = /^\/(entities\.json|entities\.jsonld|og-manifest\.json|seo-report\.json|top\.json|show\/redirects\.json|show-notes\/|blog-import\/)|\.jsonld$/i;

async function redirectMap(url) {
  const r = await fetch(url.origin + "/show/redirects.json", { cf: { cacheTtl: 3600, cacheEverything: true } });
  return r.ok ? r.json() : {};
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    // Umzug (MIGRATED=1): dub.m365.fm und m365.fm -> www.m365.fm, alte Podpage-Adressen -> /show/ (301, damit der SEO-Traffic erhalten bleibt)
    if (env.MIGRATED === "1") {
      if (url.hostname === "dub.m365.fm" || url.hostname === "m365.fm") return Response.redirect("https://www.m365.fm" + url.pathname + url.search, 301);
      const p0 = url.pathname.replace(/\/+$/, "") || "/";
      if (p0 !== "/" && !p0.startsWith("/show") && !p0.startsWith("/shows")) {
        const map = await redirectMap(url);
        const to = map[p0] || map[p0.toLowerCase()] || (/^\/(blog|videos)\//.test(p0) ? "/show/" : "");
        if (to) return Response.redirect(url.origin + to + url.search, 301);
      }
    }
    { const mp = /^(\/[a-z]{2})?\/community\/u\/mirko-peters(\/.*)?$/.exec(url.pathname); if (mp) return Response.redirect(url.origin + (mp[1] || "") + "/community/u/mirko-p" + (mp[2] || "/") + url.search, 301); }   // alter Name des Blog-Profils
    if (/^\/(pa|hi|ml|ta|te)(\/|$)/.test(url.pathname)) return Response.redirect(url.origin + "/", 301);   // diese Sprachen gibt es nicht mehr (Punjabi, Hindi, Malayalam, Tamil, Telugu)
    const p = url.pathname, isImg = IMG.test(p), isStatic = STATIC.test(p) || FONT.test(p);
    const cf = isImg ? { cacheEverything: true, cacheTtl: 604800, polish: "lossy", mirage: true }
      : isStatic ? { cacheEverything: true, cacheTtl: 86400 }
      : { cacheEverything: true, cacheTtlByStatus: { "200-299": 600, "404": 60, "500-599": 0 } };   // HTML: 10 Min am Rand, Purge nach jedem Deploy
    const res = await fetch(request, { cf });
    const h = new Headers(res.headers);
    for (const [k, v] of Object.entries(SEC)) h.set(k, v);
    h.set("cache-control", HASHED.test(p) ? "public, max-age=31536000, immutable" : FONT.test(p) ? "public, max-age=86400, s-maxage=604800" : isImg || isStatic ? "public, max-age=3600, s-maxage=86400" : "public, max-age=0, s-maxage=600, stale-while-revalidate=86400");
    if (NOINDEX.test(p)) h.set("x-robots-tag", "noindex");
    if (isImg) h.set("vary", "accept");
    if (p === "/") h.set("link", '</.well-known/api-catalog>; rel="api-catalog", </openapi.json>; rel="service-desc"; type="application/vnd.oai.openapi+json", </llms.txt>; rel="service-doc"; type="text/plain", </.well-known/agent.json>; rel="describedby"; type="application/json"');   // RFC 8288 / 9727: Startseite verweist auf maschinenlesbare Ressourcen
    if (p === "/.well-known/api-catalog") { h.set("content-type", 'application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"'); h.set("access-control-allow-origin", "*"); }
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers: h });
  },
};
