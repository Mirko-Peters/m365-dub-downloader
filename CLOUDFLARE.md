# Cloudflare vor der Plattform (dub.m365.fm)

Die Seite liegt auf GitHub Pages. Mit dem Cloudflare-Proxy kommen CDN-Cache, Bildoptimierung (Polish), Header und Weiterleitungen dazu.

## Einmalig im Dashboard (Zone m365.fm)
1. **DNS**: Eintrag `dub` (CNAME → `mirko-peters.github.io`) auf **Proxied** (orange Wolke) stellen.
2. **SSL/TLS → Overview**: Modus **Full (strict)**. Edge Certificates: *Always Use HTTPS* an, *Automatic HTTPS Rewrites* an, *Minimum TLS 1.2*.
3. **Speed → Optimization**: *Brotli*, *HTTP/3*, *Early Hints* an. **Polish** auf *Lossy* mit *WebP* (und AVIF, wenn angeboten), **Mirage** an.
4. **Caching → Configuration**: *Browser Cache TTL* = *Respect Existing Headers* (der Site-Worker setzt die Header), *Tiered Cache* an.
5. **Rules → Cache Rules** (optional, der Worker erledigt das schon): URI beginnt mit `/api` nie cachen (die API läuft auf `api-dub.m365.fm`, ist nicht betroffen).
6. API-Token (Secret `CLOUDFLARE_API_TOKEN`) braucht zusätzlich **Zone → Cache Purge** und **Zone → Zone: Read**, optional Secret `CF_ZONE_ID`.

## Was im Repo schon läuft
- `sitewrk/` – Worker `m365-dub-site` auf `dub.m365.fm/*`: HTML 10 Min am Rand (stale-while-revalidate), Bilder/Fonts/Assets lange im Cache, Polish/Mirage-Hinweise, Sicherheits-Header (HSTS, nosniff, Referrer-Policy, Permissions-Policy, X-Frame-Options). Deploy: Workflow *Site-Worker*.
- `site.yml` leert nach jedem Deploy den Cloudflare-Cache, damit neue Seiten sofort sichtbar sind.
- `/show/redirects.json` – Weiterleitungsliste für den Umzug von www.m365.fm.

## Umzug dub.m365.fm → www.m365.fm (wenn die englischen Inhalte komplett sind)
Podpage-URLs heute: Folgen `/<slug>/`, Blog `/blog/<slug>/`, Videos `/videos/<slug>/`, Gäste `/guests/<slug>/`, Seiten `/<slug>/`. Die Plattform liefert sie unter `/show/…`; `/show/redirects.json` (vom Build erzeugt, aktuell ~1.160 Einträge) ordnet jede alte Adresse der neuen zu. `/show/redirect-conflicts.json` listet Adressen, die auch die Plattform selbst belegt (aktuell `/about` – die Plattform-Seite bleibt, Podpage-About liegt unter `/show/about/`).

**Reihenfolge am Umzugstag**
1. Vorher: Alle Inhalte (Folgen, Gäste, Blog, Seiten) fertig, Weiterleitungsliste prüfen (Stichprobe der 50 meistbesuchten alten URLs in der Google Search Console → Leistung → Seiten).
2. `domain.txt` und `docs/CNAME` auf `www.m365.fm` ändern, im Worker `worker/wrangler.toml` die Variablen `SITE` auf `https://www.m365.fm` setzen (Login-Rückleitungen, CORS), Google/Microsoft/LinkedIn-OAuth-Rückruf-URLs ergänzen.
3. In GitHub Pages die Custom Domain `www.m365.fm` eintragen; Cloudflare-DNS: `www` CNAME → `mirko-peters.github.io` (Proxied), Apex `m365.fm` Proxied (Dummy-A-Eintrag), Podpage-Eintrag entfernen.
4. `sitewrk/wrangler.toml`: Routen für `www.m365.fm/*` und `m365.fm/*` aktivieren und `MIGRATED = "1"` setzen, pushen. Der Worker leitet dann per 301 um: `dub.m365.fm/*` und `m365.fm/*` → `www.m365.fm/*` (gleicher Pfad), alte Podpage-Adressen → `/show/…`, unbekannte `/blog/*` und `/videos/*` → `/show/`.
5. Site neu bauen (alle Canonicals, hreflang, Sitemaps zeigen dann auf www), IndexNow wird automatisch gesendet.
6. Search Console: Property `www.m365.fm` anlegen, Sitemap `https://www.m365.fm/sitemap.xml` einreichen; für `dub.m365.fm` ist „Adressänderung“ möglich (Property-Typ Domain).
7. Spreaker, Apple Podcasts, Spotify, LinkedIn, YouTube-Beschreibungen: Show-URL auf `https://www.m365.fm/show/` ändern.
8. 301-Regeln mindestens 12 Monate lassen; 404-Berichte in der Search Console die ersten Wochen täglich prüfen.

**Videos** (`/videos/<slug>/`) waren bewusst nicht Teil der Übertragung und laufen auf `/show/`. Wenn Videoseiten Traffic haben, später auf passende Folgen oder die Videos der Plattform mappen.

## Bilder
Cover, Teilen-Bilder und Porträts liefert der Worker mit `polish: lossy` aus; Polish erzeugt WebP/AVIF je nach Browser (`Vary: Accept`). Originale bleiben PNG/JPG im Repo.
