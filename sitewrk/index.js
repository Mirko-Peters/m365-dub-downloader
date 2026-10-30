// Worker vor der Plattform (GitHub Pages): Cache- und Sicherheits-Header, Bild-Optimierung (Polish), Weiterleitungen fuer den Umzug von www.m365.fm.
const SEC = {
  "strict-transport-security": "max-age=31536000; includeSubDomains",
  "x-content-type-options": "nosniff",
  "referrer-policy": "strict-origin-when-cross-origin",
  "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=()",
  "x-frame-options": "SAMEORIGIN",
};
const IMG = /\.(png|jpe?g|gif|webp|avif|svg|ico)$/i, STATIC = /^\/(assets|covers|og)\//i, FONT = /\.(woff2?|ttf|otf)$/i;

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
    const p = url.pathname, isImg = IMG.test(p), isStatic = STATIC.test(p) || FONT.test(p);
    const cf = isImg ? { cacheEverything: true, cacheTtl: 604800, polish: "lossy", mirage: true }
      : isStatic ? { cacheEverything: true, cacheTtl: 86400 }
      : { cacheEverything: true, cacheTtlByStatus: { "200-299": 600, "404": 60, "500-599": 0 } };   // HTML: 10 Min am Rand, Purge nach jedem Deploy
    const res = await fetch(request, { cf });
    const h = new Headers(res.headers);
    for (const [k, v] of Object.entries(SEC)) h.set(k, v);
    h.set("cache-control", isImg || isStatic ? "public, max-age=3600, s-maxage=86400" : "public, max-age=0, s-maxage=600, stale-while-revalidate=86400");
    if (isImg) h.set("vary", "accept");
    return new Response(res.body, { status: res.status, statusText: res.statusText, headers: h });
  },
};
