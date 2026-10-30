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

## Umzug www.m365.fm (wenn Podpage abgelöst wird)
1. DNS: `www` und Apex auf Proxied, Ziel egal (der Worker antwortet selbst).
2. In `sitewrk/wrangler.toml` die auskommentierte Routenzeile aktivieren und `MIGRATED = "1"` setzen; pushen.
3. Danach leitet der Worker `/episodes/<slug>` → `/show/episodes/<slug>/` usw. per 301 weiter, alles Unbekannte auf `/show/…`.
4. Bei Spreaker/Apple/Spotify die Show-URL auf `https://dub.m365.fm/show/` (später `www.m365.fm`) ändern.

## Bilder
Cover, Teilen-Bilder und Porträts liefert der Worker mit `polish: lossy` aus; Polish erzeugt WebP/AVIF je nach Browser (`Vary: Accept`). Originale bleiben PNG/JPG im Repo.
