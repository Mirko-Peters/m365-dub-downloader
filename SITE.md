# Website (GitHub Pages) – Einrichtung & Betrieb

Die Seite wird **automatisch** aus `episodes/*.json` + `data/published.json` gebaut (`generate_site.py`) und per GitHub Actions veröffentlicht
(bei jedem Push, sowie täglich 05:17 UTC). Nichts von Hand pflegen.

## Einmalig einschalten
1. GitHub → Repo → Settings → Pages → **Source: GitHub Actions**.
2. Actions → „Website bauen und veröffentlichen“ → **Run workflow**.
→ https://mirko-peters.github.io/m365-dub-downloader/

## Eigene Domain (z. B. international.m365.fm)
1. DNS bei m365.fm: **CNAME** `international` → `mirko-peters.github.io`
2. Repo: Datei `domain.txt` mit dem Inhalt `international.m365.fm` anlegen (eine Zeile) und committen.
3. Settings → Pages → Custom domain `international.m365.fm` eintragen, „Enforce HTTPS“ aktivieren.
Alle URLs, Sitemap, hreflang und Canonicals schalten automatisch auf die Domain um.

## Apple Podcasts / Spotify je Folge
Die Sprach-Shows müssen dort existieren (Spreaker → Show → Distribution, oder Apple Podcasts Connect / Spotify for Creators mit dem RSS-Feed
`https://www.spreaker.com/show/<ShowID>/episodes/feed`). Danach in `data/platforms.json` je Sprache `apple_id` (Zahl aus der Apple-URL `…/id123456`)
und `spotify_id` (Teil nach `/show/`) eintragen. Der tägliche Lauf ordnet die Folgen per Titel zu (`sync_platforms.py`).
Spotify-Folgenlinks brauchen zusätzlich die Repo-Secrets `SPOTIFY_CLIENT_ID` und `SPOTIFY_CLIENT_SECRET` (kostenlose App auf developer.spotify.com).
Auf der Seite zeigt ein kleines Skript Apple-Nutzern (iPhone, iPad, Mac) zuerst Apple Podcasts, allen anderen zuerst Spotify.

## Search Console
search.google.com/search-console → Property hinzufügen → Sitemap `…/sitemap.xml` einreichen. Bing/Yandex bekommen neue URLs automatisch per IndexNow.
