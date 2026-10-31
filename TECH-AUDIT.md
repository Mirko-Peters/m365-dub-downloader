# Technik-Audit www.m365.fm (Ticket T0)

Stand 1. November 2026, Branch `ticket/0-tech-audit`, Grundlage main (Commit 9f5a925). Erstellt vom Dev-Chef mit acht parallelen Prüfläufen (je ein Blickwinkel) und einer Gegenprüfung je Lauf (Stichprobe der fünf wackligsten Aussagen gegen den Quellcode). Alle Pfade sind relativ zum Repository; `docs/` ist das Build-Ergebnis (GitHub Pages) und wird bei jedem Bau gelöscht, deshalb liegt dieses Audit im Wurzelverzeichnis.

Status je Befund: ✅ in Ordnung · 🟡 teilweise · ❌ fehlt · 🐞 Fehler. Die Befundtexte stammen aus den Prüfläufen (Englisch) und sind unverändert übernommen; die Einleitung je Abschnitt und die Ticket-Zuordnung sind Deutsch.

## Kurzfassung

- **Bereits in offenen PRs gelöst:** Seitengröße und R2-Auslagerung mit gezieltem Purge (PR 70), verzögerte Sprach-Skripte, gebündeltes Inline-JS, Fokus-Falle im Popup (PR 71), Folgen-Register und Übersetzungsmodell in D1 (PR 69), Expertise-Stufen (PR 73), Episodenseiten aus Shownotes (PR 74).
- **Größte offene Risiken:** Bot-Commits aus Workflows lösen keinen Seitenbau aus (Artikel, Übersetzungen, Updates erreichen die Seite bis zu 24 h später); Commit-Schritte in site.yml scheitern mit exit 128; Qualitätsprüfungen (check_links, check_schema, IndexNow) laufen rot, aber folgenlos; Startseite ohne Kartenobergrenze; Dub-Folgen ohne hreflang auf das Original; Person-Schema von Mirko Peters vierfach unterschiedlich definiert.
- **Reihenfolge-Vorschlag für T1–T20:** erst T2/T3 (Englisch unter /en/, hreflang-Cluster zusammenführen), dann T1 (Sitemaps je Typ mit lastmod), T4 (Person/Organization konsolidieren, Fehler in Dub-Folgen und Profilen), T6/T9 (Startseite begrenzen, Lenis und YouTube-Fassade), T8/T7 (Redirect-Lücken, Titel-Vorlagen), T5 (Mojibake-Reparatur und Build-Check), T10, danach T11–T20.

## Architektur und Build-Pipeline

Ein sequenzieller Python-Generator (generate_site.py, ca. 8 Minuten, 35.000 Seiten, docs/ 1,67 GB) baut 14 Dub-Sprachseiten, die englische Show unter /show/, Community-Seiten aus den D1-Exporten und ca. 2.300 frühere Blog-Beiträge; davor ein schlanker Site-Worker (Header, Edge-Cache, 301-Karte) und der Community-Worker (43 Module, 22 Cron-Aufgaben alle 30 Minuten, versionierte D1-Migrationen). Die Pipeline funktioniert, ist aber an vier Stellen fragil: Ausgabegröße über dem Pages-Richtwert (PR 70 lagert übersetzte Seiten nach R2 aus), Bot-Commits lösen keinen Seitenbau aus, Commit-Schritte scheitern an unstaged Änderungen, Qualitätsprüfungen laufen als continue-on-error.

### ✅ in Ordnung · Build pipeline map: generate_site.py phases and site_* responsibilities

generate_site.py build() (line 795) runs strictly sequentially: SF.prefetch/check of API exports -> load episodes/published -> rmtree docs/ (line 815) -> dub-episode pages, taxonomy, language homes, root hub (phase 'Folgenseiten', 290 s in CI run 41246343089) -> blog merge (62 s) -> ENT.build entity pages (38 s) -> MEM/EVT/BLG/LIB/GST/PODS/VIDS/FEED/SHW community pages (31 s) -> PP.build English /show/ replica (34 s) -> MCPS/LIVE/SEOR/PRS, learn/updates/top (5 s) -> sitemaps -> robots, llms*.txt, agent.json, openapi, admin, 404, topics.json (5 s). Total ~8 min of a 10-22 min push run; 35,306 pages, 9,006 sitemap URLs. Each site_*.py owns one page family (podpage=/show/, blog, legacy_blog=Podpage posts as mirko-p, entities, events, members, learn=glossary+entity registry, live, feed, shows, library, podcast, video, press, legal, seo, sidebar, design/cover=CSS+SVG, r2=URL rewrite, fetch=API loader, i18n=UI strings). No incremental build and no parallelism inside generate_site.py (only the 8-thread export prefetch in site_fetch.py:76).

*Dateien:* `generate_site.py`, `site_fetch.py`, `site_podpage.py`, `site_blog.py`, `site_legacy_blog.py`, `site_entities.py`, `site_learn.py`  
*Tickets:* –

### ✅ in Ordnung · Data sources: repo JSON + 14 API exports, with cache fallback and hard-fail on essentials

Inputs are episodes/*.json (117 videos x 14 languages), data/published.json + top.json (sync_spreaker.py), platforms/episode_links/videos/en_titles/en_episodes, data/articles + covers (Claude-generated), data/podpage/*.json(.gz) (Podpage backup: 16.5 MB blog, 8.5 MB episodes), data/blog_i18n (186 MB, 246 files), podpage_i18n (27 MB), show_notes (11 MB), live.json, speakers.json, entities.json (269) + guest/speaker_entities. site_fetch.py prefetches 14 worker exports (+ wiki per language), stores each in data/cache (gitignored, restored via actions/cache in site.yml) and aborts the build when blog/profiles/entity/qa exports are missing fresh AND cached (check(), exit 1); profiles additionally fall back to the committed data/members_export.json (site_members.py:25). This is sound; the remaining risk is a stale actions/cache silently feeding an old export (warning only, no age limit).

*Dateien:* `site_fetch.py`, `site_members.py`, `site_learn.py`, `data/blog_import.json`, `.github/workflows/site.yml`  
*Tickets:* T14, T15

### 🐞 Fehler · docs/ output is 1.67 GB (701 MB Pages artifact) and grows ~100 MB per feature; no r2out/ exists

CI logs show docs/ gesamt 1449 MB (19:00) -> 1581 MB -> 1666 MB (22:11) within three hours; the deployed artifact is 701,509,669 bytes. GitHub Pages documents a 1 GB soft limit for published sites, so the current size is already past it and every new indexable language block (de: 90 -> 168 MB after 'deutsche Sprachfassungen indexierbar') pushes further. Main contributors: each dub language ~80 MB (incl. ~14,000 noindex translated /<lang>/show/episodes/ pages, site_podpage.py:312-331), community 151 MB, blog-import 104 MB, 5,961 OG PNGs (generate_og.py). There is no r2out/ directory or code path anywhere in the repo (grep r2out = 0 hits); R2 is only reached by tools/r2_upload.py (manual workflow) and site_r2.rewrite() swapping 878 mapped URLs at write time (generate_site.py:855).

*Dateien:* `generate_site.py`, `site_podpage.py`, `site_r2.py`, `tools/r2_upload.py`, `data/r2_map.json`, `generate_og.py`  
*Tickets:* T9, T14

### 🟡 teilweise · blog-import/ (104 MB) is republished on every build only to feed the worker's D1 import cron

site_legacy_blog.publish() (lines 118-130) writes all ~2,300 Podpage posts as blog-import/part-N.json (100 per part) into docs/ whenever data/blog_import.json has enabled=true (it does). worker/src/legacyblog.js:17-22 pulls 60 posts per 30-minute cron from SITE/blog-import and tracks offset/ver in D1 table blog_import. Once offset == total the flag must be set to false by hand or the 104 MB stays in every deploy; the worker also still runs CREATE TABLE IF NOT EXISTS blog_import at runtime (line 11) although 0001_baseline.sql already defines it.

*Dateien:* `site_legacy_blog.py`, `worker/src/legacyblog.js`, `data/blog_import.json`, `worker/migrations/0001_baseline.sql`  
*Tickets:* T14

### ✅ in Ordnung · GitHub workflows: triggers, writes and commit targets

site.yml: push to main on data/episodes/site_* paths + cron 05:17 + manual; commits data/top.json, published.json, spreaker_auth.enc, en_titles, en_episodes, en_transcripts, reviews_ext, spotify_links, show_notes, live.json, episode_links*, platforms.json, money_keywords, members_export, entity_mod (each as a separate commit step), then builds, checks, OG images, deploys Pages, purges Cloudflare, IndexNow. worker.yml: push on worker/** + daily 05:50 (renews Spreaker token, commits spreaker_auth.enc, runs node --check/--test/MCP coverage/SQLite migration dry-run, setup.mjs = D1 create/export backup/migrations apply/secrets/deploy). sitewrk.yml: push on sitewrk/** -> wrangler deploy. articles.yml hourly (data/articles, covers, spend.json), translate-blog.yml every 3 h (data/blog_i18n), ms-updates.yml 04:20 (product_updates.json), apply-shownotes.yml every 2 h (shownotes/*), mcp-check.yml 06:30, manual: r2-images, wikidata, translate-show/-notes/-all, fetch-blog, admin-setzen, spreaker/youtube_connect, adfree-*. dubs.yml schedule is paused (runs on the PC).

*Dateien:* `.github/workflows/site.yml`, `.github/workflows/worker.yml`, `.github/workflows/sitewrk.yml`, `.github/workflows/articles.yml`, `.github/workflows/translate-blog.yml`, `.github/workflows/ms-updates.yml`, `.github/workflows/dubs.yml`, `worker/setup.mjs`  
*Tickets:* –

### 🐞 Fehler · Bot data commits from workflows do not trigger the site build (GITHUB_TOKEN), contrary to the comment in articles.yml

All workflows use actions/checkout@v4 with the default GITHUB_TOKEN (no token:/PAT anywhere), and pushes made with that token never fire on:push workflows. articles.yml:30 claims 'der Push auf data/ loest den Seitenbau aus', but the last 40 site.yml runs are exclusively human pushes or the 05:17 schedule; none followed the hourly article, 3-hourly translate-blog, 04:20 ms-updates or wikidata/r2-images commits. Consequence: new articles, blog translations, product updates and R2 mappings only reach the site with the next manual push or the nightly build (up to 24 h). Either use a PAT/App token for those commits, or have them dispatch site.yml explicitly (workflow_dispatch via gh), keeping the cancel-in-progress group.

*Dateien:* `.github/workflows/articles.yml`, `.github/workflows/translate-blog.yml`, `.github/workflows/ms-updates.yml`, `.github/workflows/r2-images.yml`, `.github/workflows/site.yml`  
*Tickets:* T15, T17, T20

### 🐞 Fehler · Commit steps in site.yml fail with exit 128 because build_speakers.py leaves unstaged changes

Runs 41240030626 and 41235457661 show 'error: cannot pull with rebase: You have unstaged changes' followed by 'fatal: no rebase in progress' and exit 128 in the live.json commit step. Cause: tools/build_speakers.py:161-164 rewrites the committed files data/speaker_entities.json, speakers.json and speaker_report.json before the later commit steps, and the '(git pull --rebase || git rebase --abort) && git push' pattern (site.yml:52,120,136,150) has no handling for a dirty tree, so the local commit is never pushed. Fix: stash or add those three files, or collect all data changes into one commit at the end of the job.

*Dateien:* `.github/workflows/site.yml`, `tools/build_speakers.py`  
*Tickets:* –

### 🐞 Fehler · 208 bot commits in 7 days: top.json timestamp and Fernet re-encryption create a diff on every run

git log shows 71 'Spreaker-Daten aktualisiert' and 59 'Spreaker-Token erneuert' commits in the last week (plus 32 live.json). sync_spreaker.py:87 writes an 'updated' ISO timestamp into data/top.json, so every site run produces a commit even when the top list is unchanged; spreaker_auth.py:33 re-encrypts with a fresh Fernet nonce, so every worker.yml run (daily + every worker/** push) commits a changed data/spreaker_auth.enc. Together with 186 MB of blog_i18n and 44 MB en_transcripts this inflates the repo (pack 230 MiB + 127 MiB loose) and the checkout of every one of the ~15 daily runs. Compare content without the timestamp / only re-encrypt when the token actually changed.

*Dateien:* `sync_spreaker.py`, `spreaker_auth.py`, `.github/workflows/worker.yml`, `.github/workflows/site.yml`  
*Tickets:* –

### 🐞 Fehler · Quality gates (check_links, check_schema, IndexNow) fail on every run but are continue-on-error

In the last four successful site runs check_links.py reports 10,936-11,813 broken internal links (e.g. https://www.m365.fm/blog/<slug>/ linked from /pt/show/episodes/... - legacy blog URLs that only the Cloudflare worker's 301 map resolves, so the checker cannot see them), check_schema.py reports 3,210 Event objects without 'location' (/<lang>/community/events/m365con-2026/) and dozens of non-ISO datePublished values on entity pages, and the IndexNow step dies with HTTP 403 fetching https://www.m365.fm/sitemap.xml (urllib default user agent blocked at Cloudflare), so Bing/Yandex never get notified. All three steps are continue-on-error (site.yml:152-157,205), so nobody sees it. Rewrite legacy links to /community/u/mirko-p/blog/<slug>/ at build time, fix the Event location, and send a browser-like User-Agent (or read docs/sitemap*.xml locally) for IndexNow.

*Dateien:* `.github/workflows/site.yml`, `check_links.py`, `check_schema.py`, `site_events.py`, `site_podpage.py`  
*Tickets:* T1, T4, T8

### 🟡 teilweise · Site worker (sitewrk/index.js): headers, caching, redirects; no R2 binding or origin fallback

The 48-line worker sets HSTS/nosniff/referrer/permissions/X-Frame headers, caches HTML at the edge for 600 s (stale-while-revalidate 86400, purge_everything after every deploy in site.yml), images 7 days with Polish/Mirage + Vary: Accept, hashed /assets/site.<hash>.css immutable for a year, fonts only 1 day (could be immutable since file names are stable), x-robots-tag noindex for data exports, and RFC 8288 Link headers on /. Redirects: dub.m365.fm and m365.fm -> www (301), old Podpage paths via /show/redirects.json fetched from origin per request (cacheTtl 3600), /community/u/mirko-peters -> mirko-p, removed languages pa/hi/ml/ta/te -> / (301 to home rather than 410 or to the matching page). There is no R2 bucket binding and no fallback to R2 or to the GitHub Pages origin if the map fetch fails (returns {} silently); images at img.m365.fm are served by the bucket's own custom domain, not through this worker. wrangler.toml already has MIGRATED="1" and all three routes active.

*Dateien:* `sitewrk/index.js`, `sitewrk/wrangler.toml`, `CLOUDFLARE.md`, `CLAUDE.md`  
*Tickets:* T8, T9

### 🟡 teilweise · Legacy Podpage 301 map covers episodes/pages/guests/blog but misses several documented paths and uses meta-refresh under /show/blog/

site_podpage.py:425-438 builds show/redirects.json for /<episode-slug>, /<page-slug>, /guests/<slug>, /blog/<slug>, /show/blog/<slug>, list pages (/episodes, /guests, /hosts, /people, /sponsors, /reviews, /podroll, /videos, /blog) and merged guest entities, plus show/redirect-conflicts.json for clashes (currently /about). Missing from the map: /sponsor (singular), /legal/, /follow/, /newsletter/, /p/..., and the /mirko-peters/ episode rename. Because the worker skips every path starting with /show (index.js:27), the /show/blog/<slug>/ entries are only served as noindex meta-refresh stub pages (site_podpage.py:376-382), not 301s, and these ~2,300 stubs are also built into docs/ on every run.

*Dateien:* `site_podpage.py`, `sitewrk/index.js`  
*Tickets:* T8, T12

### ✅ in Ordnung · Community worker: module map, 22 cron tasks every 30 minutes, versioned D1 migrations

worker/src/index.js routes /auth/*, /mcp, /a2a and /api/* to 43 modules (profiles, events, blog, qa, votes, library, guests, podcast, youtube, shows, reviews, notes, points, messages, mail, translate/autotr, wiki, seo_api, topics, entities, legacyblog, liveevents, pastevents, adminpanel, feeds, digest, badges, push, credits, demo, orgoffers, wish, updates, mcp, a2a). scheduled() (index.js:388-414) runs runDigest only at 06:00 and 21 other tasks on every */30 cron inside one invocation via ctx.waitUntil, each logged to cron_runs (0002_ops.sql) with 7-day cleanup; on the Workers Paid plan (30 s CPU, 1000 subrequests per invocation, worker/README.md) this single-invocation fan-out is the fragile spot if several import/translate tasks run long at the same tick. Migrations are consistent: every table referenced in src/ exists in 0001_baseline (~100 tables), 0002_ops (cron_runs, audit, tr_queue) or 0003_content_topic; worker.yml dry-runs them in SQLite, runs node --test and MCP coverage before setup.mjs exports a D1 backup (artifact, 14 days) and applies migrations remotely.

*Dateien:* `worker/src/index.js`, `worker/migrations/0001_baseline.sql`, `worker/migrations/0002_ops.sql`, `worker/migrations/0003_content_topic.sql`, `worker/setup.mjs`, `worker/wrangler.toml`, `worker/README.md`  
*Tickets:* T13, T14

### 🟡 teilweise · Two-way coupling: build reads D1 exports, worker crons read build artefacts (up to 24 h + 30 min latency)

The site pulls 14 exports from api-dub.m365.fm (site_fetch.py PREFETCH), while worker crons pull files the build wrote to GitHub Pages: /blog-import/*.json (legacyblog.js:17), /entities.json (entities.js:22, importEntitiesFromSite), /topics.json (topics.js:19, 'site' overrides older DB mappings), /live.json (liveevents.js:20), /speakers.json and program files (pastevents.js:25,81), /ui_js_en.json (translate.js:81). Entity data therefore has two sources of truth (data/entities.json + guest/speaker_entities.json merged with /api/entity/export in site_learn.py:393-414, then re-exported for the worker). Because bot data commits do not trigger builds (see above), a change made in /admin/ or by a cron may take a nightly build plus a 30-minute cron to round-trip, and a failed or partial build (e.g. empty topics.json) is imported into D1 unchecked.

*Dateien:* `site_fetch.py`, `site_learn.py`, `worker/src/entities.js`, `worker/src/topics.js`, `worker/src/liveevents.js`, `worker/src/pastevents.js`, `worker/src/translate.js`  
*Tickets:* T11, T12, T13, T14

### 🟡 teilweise · Sitemaps are split per language plus one core file; not per type, and robots.txt lacks Disallow for admin/callback/exports

generate_site.py:1388-1413 writes sitemap-core.xml (everything not under /<lang>/), one sitemap-<lang>.xml per dub language with xhtml:link alternates (dub episodes only) and a sitemapindex sitemap.xml; English /show/, community, entities and blog all land in sitemap-core.xml, so there is no per-type split (episodes/blog/entities/events). robots.txt (line 1415) allows everything incl. AI bots and lists the sitemap, but /admin/, /callback/, /blog-import/, /show-notes/ rely only on meta noindex or the worker's x-robots-tag header. The build also writes data/urls.json (gitignored) for the IndexNow step, which currently never succeeds.

*Dateien:* `generate_site.py`, `sitewrk/index.js`  
*Tickets:* T1

### 🟡 teilweise · hreflang/x-default: default x-default points to the home page and most page families pass no alternates

page() (generate_site.py:386-397) only emits hreflang links when a caller passes alternates, and sets x-default to BASE+'/' whenever xdefault is not given (line 396), so dub episode pages (line 1066, no xdefault) declare the English home as x-default instead of the original episode. Translated /<lang>/show/episodes/ pages pass alternates=None (site_podpage.py:330) and only 150 per language with translated show notes are indexable; community/blog pages compute tr_langs for hreflang (site_blog.py:70-73) but no English dub entry exists, so clusters never include an /en/ URL. The sitemap mirrors this (alternates only for dub episodes and homes).

*Dateien:* `generate_site.py`, `site_podpage.py`, `site_blog.py`  
*Tickets:* T3, T2

### ❌ fehlt · English is not a first-class language: no /en/, English lives at / (hub) and /show/ (Podpage replica)

LANGS (generate_site.py:46-57) contains only the 14 dub languages; English pages are built by site_podpage.py under /show/ and the root hub by site_home.py, with COMM_LANGS (site_i18n.py:6) treating 'en' as prefix ''. ROADMAP.md:100-105 records the /en/ plan as backlog ('betrifft den gesamten Seitenbau'). Any T2 implementation touches url_of/pfx helpers, sitemap-core partitioning, the worker's /show redirect exclusion (sitewrk/index.js:27) and the OG image sharing (og_of) that currently keys on the English /show/ URL.

*Dateien:* `generate_site.py`, `site_i18n.py`, `site_podpage.py`, `ROADMAP.md`  
*Tickets:* T2

### 🟡 teilweise · Home hub renders every card of every language server-side and paginates only in JS

site_home.hub() (lines 47-120) appends one HTML card per blog post, podcast episode, upcoming event, library item, creator-feed item (incl. GitHub), 40 product updates, creator videos and 24 dub videos; at the root (root=True, line 50) the language filter is disabled so posts of all 15 languages are included, and the JS only hides cards beyond 18 (%N%). The full card list is therefore in the HTML of / and /<lang>/, which is the structural cause of a home page far above 300 kB (not measurable here: www.m365.fm is blocked from this sandbox). Cap to 24 cards per language at build time and move the GitHub feed kind out of the public list.

*Dateien:* `site_home.py`, `site_feed.py`  
*Tickets:* T6, T9

### 🟡 teilweise · Legacy and D1 blog posts are merged by slug; translated legacy posts live in repo JSON (186 MB)

generate_site.py:1263-1264 fetches D1 posts (/api/blog/export) and adds Podpage posts from data/podpage/blog_posts.json.gz only when the slug is not already in D1 for mirko-p, so duplicates are avoided by slug only (a changed slug in D1 would create a duplicate). Translations come from data/blog_i18n/<lang>/*.json (translate_blog.py, 19-22 MB per language, committed every 3 h) and are merged by site_legacy_blog.py, not from D1, so the T15 review status and the T14 'everything in D1' target are not yet implemented for translations; the import path imports/blog/<lang>/*.md does not exist in the repo.

*Dateien:* `generate_site.py`, `site_legacy_blog.py`, `translate_blog.py`, `data/blog_i18n`  
*Tickets:* T6, T14, T15, T17

### 🟡 teilweise · Core Web Vitals plumbing: hashed external CSS, local preloaded fonts, deferred scripts, OG cache; no critical-CSS inline, no image dimensions pipeline

page() links one content-hashed stylesheet (css_link, generate_site.py:446-456, immutable via the worker) and inlines only assets/fx.css; Barlow woff2 files are local (assets/fonts) and preloaded; attend/smooth/fx scripts are defer, Clarity loads behind consent (consent_html). Missing: critical CSS inline (full CSS is external, render-blocking), width/height + loading=lazy for most images (only site_legacy_blog.py:99 and site_learn.py:161 set them), AVIF/WebP for repo images (Polish does it at the edge only for www), and AdSense is prepared but off (site_ads.py). OG images: 5,961 PNGs rendered with Playwright, 292 MB .ogcache restored per run (generate_og.py:64-66), only 2 new per run.

*Dateien:* `generate_site.py`, `generate_og.py`, `site_ads.py`, `assets/fonts`, `sitewrk/index.js`  
*Tickets:* T9

### 🟡 teilweise · Build duration and concurrency: 10-22 min per push, 34 min nightly, cancel-in-progress drops 12 of the last 40 runs

site.yml uses concurrency group site-build with cancel-in-progress: true (line 16-18); of the last 40 runs 12 were cancelled by a following push, and bursts of 5 pushes within a minute (20:39-20:40) mean the first commits' data steps ran partially. generate_site.py itself takes ~7.8 min (dub-episode phase 290 s), check_links 0.7 min, artifact upload 0.8 min, deploy 0.9 min; the scheduled run adds fetch_en_episodes, reviews, Spotify scraping (12 min cap), show notes and sync_platforms (15 min cap, TODO.md notes ~21 min) and reaches 34 min. The 'Spreaker-Daten holen' step runs on every push too (0.5 min, commit noise). Splitting the data-sync steps into their own scheduled workflow and only building on push would shorten push builds and remove the dirty-tree commit failures.

*Dateien:* `.github/workflows/site.yml`, `generate_site.py`, `TODO.md`  
*Tickets:* –

### 🟡 teilweise · Deprecated and unsupported language paths handled inconsistently

The worker 301s /pa, /hi, /ml, /ta, /te to the home page (sitewrk/index.js:28) while data/retired.json and site_i18n.py drive noindex notice pages for retired content; episodes/*.json still carry entries for those languages but build() skips any lang not in LANGS (generate_site.py:822). config.json show_map still lists hi/ml/pa/ta/te Spreaker shows, so the PC-side uploader may keep producing episodes the site never shows.

*Dateien:* `sitewrk/index.js`, `generate_site.py`, `config.json`, `data/retired.json`  
*Tickets:* T8

**Gegenprüfung (alle Stichproben bestätigt):** All checked claims verified. (1) GITHUB_TOKEN/no PAT: no `token:` on any actions/checkout and articles.yml:30 carries the quoted comment — correct. (2) build_speakers.py:161-164 rewrites speaker_entities.json/speakers.json/speaker_report.json unstaged, and site.yml:52,120,136,150 use the `(git pull --rebase -q -X theirs || git rebase --abort) && git push -q` pattern with no dirty-tree handling — correct. (3) sync_spreaker.py:87 writes `updated` ISO timestamp into top.json; spreaker_auth.py:33 `FILE.write_bytes(Fernet(...).encrypt(...))` is called unconditionally from refresh() on every `spreaker_auth.py env` run (worker.yml:28) — correct. (4) sitewrk/index.js is 48 lines; fonts get max-age=86400 (line 41), HTML 600 s + stale-while-revalidate 86400, redirects.json fetched with cacheTtl 3600 and `{}` on failure (lines 14-17), pa/hi/ml/ta/te -> / 301 (line 33), MIGRATED="1" and three routes in wrangler.toml — correct. (5) site_legacy_blog.publish() gated on data/blog_import.json enabled=true (currently true), PER=100; legacyblog.js BATCH=60, CREATE TABLE IF NOT EXISTS at line 11, offset/ver in D1, cron */30 in worker/wrangler.toml:15; 0001_baseline.sql:566 already defines blog_import — correct. Only cosmetic line offsets: generate_site.py rmtree is at line 810 (finding says 815) and R2.rewrite write at line 857 (finding says 855); site_legacy_blog.publish starts at line 117.

## Sprachen, URLs, hreflang (T2, T3, T12, T19)

hreflang wird zentral in page() ausgegeben, aber nur, wenn der Aufrufer Alternates übergibt; x-default fällt sonst auf die Startseite zurück. Dub-Folgenseiten (/<lang>/<slug>/) verweisen nicht per hreflang auf das englische Original; dasselbe Video existiert je Sprache in zwei getrennten Clustern. Englisch hat keinen /en/-Baum. Mirko Peters ist auf vier URL-Familien verteilt.

### 🟡 teilweise · hreflang/x-default is emitted centrally in page() but only when a caller passes alternates; x-default defaults to the home page

generate_site.py:386-396 `page()` writes `<link rel=alternate hreflang=...>` for every entry of the `alternates` dict and then one x-default; when `xdefault` is not given it falls back to `BASE + '/'` (the English home). Any caller that passes `alternates=None` (the majority: entity index, community, members, events, library, video, podcast, learn, press, live, updates, show hub/guests/hosts, `/show/episodes/`) gets no hreflang at all. Only the accessibility statement (generate_site.py:1158-1164: alternates for all languages + `hreflang="en"` via extra_head + `xdefault=ast_url('en')`) implements the full reciprocal pattern.

*Dateien:* `generate_site.py`  
*Tickets:* T3

### 🐞 Fehler · Dubbed episode pages have no hreflang="en" to the English original and x-default points to the home page

generate_site.py:962 builds `alts = {x: url_of(by_vid[vid][x]) for x in by_vid[vid]}` (dub languages only, `LANGS` has no `en`), and line 1067 calls `page(..., alts, ...)` without `xdefault`, so every `/<lang>/<slug>/` page ends with `hreflang="x-default" href="https://www.m365.fm/"`. The English original is known (`ORIG` line 941-948) but only rendered as a visible link `<a href=.../show/episodes/<slug>/ hreflang=en>Original (English)</a>` (line 1048), never as a `<link rel=alternate>`; the sitemap entry (line 1068) carries the same incomplete set.

*Dateien:* `generate_site.py`  
*Tickets:* T3, T2

### 🟡 teilweise · Root '/' and all language-level hubs omit themselves/English from the hreflang cluster

`alts_home = {x: f'{BASE}/{x}/' for x in active}` (generate_site.py:1073, 1106) lists the 14 dub homes; `/` is only referenced as x-default and never as `hreflang="en"`, and `/<lang>/` pages therefore have no `en` alternate either. The same pattern repeats for `/<lang>/podcast/` (line 1337 `_palts`), category pages (1343) and `/<lang>/top/` (1372): clusters among dubs only, no English member, x-default = home. The English show hub `/show/` is published via `pub()` with `alts=None` (site_podpage.py:200-204) and is not part of any cluster.

*Dateien:* `generate_site.py`, `site_podpage.py`  
*Tickets:* T3, T2, T1

### 🟡 teilweise · Sitemaps carry xhtml:link alternates but never x-default, and are split by path prefix rather than by language/type

`sm_file()` (generate_site.py:1388-1396) writes one `<xhtml:link hreflang=...>` per entry of the alts dict and nothing else, so no sitemap URL has x-default and `en` only appears where a caller added it (show episodes, blog, entities). `sitemap-core.xml` = every URL not under `/<lang>/` (1400-1402, i.e. all English and the unprefixed community/entity pages) and `sitemap-<lang>.xml` = everything under `/<lang>/` (1403-1407); there is no per-type split and no English-language sitemap distinct from 'core'. robots.txt (1415) points to the index only.

*Dateien:* `generate_site.py`  
*Tickets:* T1, T3

### ❌ fehlt · English has no /en/ tree: it is served at '/', '/show/...' and unprefixed '/community/', '/entity/', '/glossary/'

`LANGS` (generate_site.py:45-55) contains only the 14 dub languages; `header()` (606-628), `page()` (389-391), `footer()` (652-663) and `site_i18n.pfx()` (site_i18n.py:13-15 returns '' for en) all special-case English as 'not in LANGS' = unprefixed. The root page is built at `docs/index.html` (1128-1141) and the Podpage main show under `/show/` (site_podpage.py:193, `root = f'{BASE}/show/'`). Nothing writes `/en/` (grep finds only the comment at generate_site.py:656 about a former 404 at `/en/top/`), and `sitewrk/index.js` has no `/show/ -> /en/` 301 (only dub.m365.fm→www, the Podpage map, `/community/u/mirko-peters`→`mirko-p` and retired languages, lines 20-34). ROADMAP.md:101 records the `/en/` goal as open.

*Dateien:* `generate_site.py`, `site_i18n.py`, `site_podpage.py`, `sitewrk/index.js`, `ROADMAP.md`  
*Tickets:* T2

### 🐞 Fehler · Same video exists twice per language in two disjoint hreflang clusters (dub page vs. localized show page)

Dub pages live at `/<lang>/<slug>/` (generate_site.py:849 `url_of`), while site_podpage.py:274 `loc_url` builds `/<lang>/show/episodes/<podpage-slug>/` for the same episode with translated title/teaser/notes (data/podpage_i18n/*.json, notes_*.json for all 14 languages). The English original `/show/episodes/<slug>/` declares alternates `{'en': self, <lang>: /<lang>/show/episodes/...}` only for versions with translated notes (site_podpage.py:320-322), and the localized version links back with `xdefault=ep_url(e)` (line 330); the dub page for the same language is in a separate cluster without `en` (finding 2). Canonicals are always self (generate_site.py:422), so Google sees two German pages per episode with conflicting alternate sets.

*Dateien:* `site_podpage.py`, `generate_site.py`  
*Tickets:* T3, T2

### 🐞 Fehler · Localized show episode lists compute hreflang targets but never emit them (dead variable)

site_podpage.py:350 builds `lal = {'en': f'{root}episodes/' ...}` for `/<lang>/show/episodes/` pages, but line 353-354 calls `g['page'](l, ..., None, None, xdefault=...)`, so `lal` is unused; the English list `/show/episodes/` is published with `alts=None` (line 335-336). Result: x-default is written (because `page()` only emits it inside `if alternates:` it is actually not written either) and no list-level cluster exists.

*Dateien:* `site_podpage.py`  
*Tickets:* T3

### 🟡 teilweise · Language switch is page-level only on dub episode/home/list/top pages; everywhere else it jumps to language home pages and 'English' always goes to /show/

`lang_dropdown()` (site_design.py:206-213) renders a `<details class=lsw>` with flag, `hreflang`/`lang` attributes and `aria-current=page`; `lang_switch()` (generate_site.py:192-194) feeds it page alternates only for dub episodes (line 1046), language homes (1096), list pages (1324) and top pages (1373). Every other page calls `header(lang, '')`, which falls back (generate_site.py:625-627) to all 14 `/<lang>/` home URLs, and `lang_dropdown` prepends `('en','English', EN_URL)` where `EN_URL = f'{BASE}/show/'` (site_design.py:203-209, generate_site.py:583). So on entity, blog, community, learn, localized-show and English show pages the switch does not lead to the same page in another language, and 'English' never points at the English counterpart (not even on '/', where it leads to /show/). The root 'Languages' grid additionally hard-codes the EN tile to `https://www.m365.fm` (generate_site.py:1115) instead of a BASE-relative URL.

*Dateien:* `site_design.py`, `generate_site.py`  
*Tickets:* T3, T10

### 🟡 teilweise · lang/dir are set per page (ar/he get dir=rtl) but CSS still has physical left/right rules and og:locale for Arabic is invalid

`page()` writes `<html lang="{hl}" dir="{d}">` from `LANGS[lang][1..2]` (generate_site.py:389-390, 421), giving `ar`/`he` `dir="rtl"` and all non-LANGS pages `lang="en" dir="ltr"`. There is no `[dir=rtl]` rule anywhere (grep over assets/*.css, generate_site.py, site_design.py); site_design.py mostly uses logical properties (inset-inline x9, inline-start x4) but generate_site.py CSS keeps `.portrait{float:right;margin:0 0 12px 22px}` (line 119), 4x margin-right, 2x padding-left, and assets/community.css uses margin-left and text-align:right, so RTL layouts partly mirror and partly do not. `og:locale` for Arabic is `ar_AR` (generate_site.py:52), which is not a valid locale (e.g. ar_SA/ar_AE). Glossary definitions in non-de languages are correctly marked `<dd lang="en" dir="ltr">` (site_learn.py:318).

*Dateien:* `generate_site.py`, `site_design.py`, `assets/community.css`, `site_learn.py`  
*Tickets:* T3, T10

### 🟡 teilweise · Show sidebar exists in all 15 languages (L10N) but is only attached to dub episode/home/list/top pages and English /show/ pages

site_sidebar.py has an English `render()` (lines 50-63, incl. the 'M365.FM Show' nav card built at site_podpage.py:194-195) used by `pub()` for `/show/...` (site_podpage.py:200-203), and `render_lang()` with `L10N` strings for en + 14 languages (lines 67-103) used through `side_for()` (generate_site.py:851-852) on dub episode pages (1067), language homes (1103), podcast/category/tag lists (1331) and top pages (1377). No sidebar is passed for: localized show pages `/<lang>/show/...` (site_podpage.py:330, 353 use a plain `<main class=wrap>`), entity pages in every language (site_entities.py:265 `shell`), blog (site_blog.py:63), members/events/library/video/podcast/guests community pages, learn/glossary (site_learn.py), press, live, updates, MCP. The 'M365.FM Show' nav card therefore never appears on a non-English page, and TODO.md:32 already flags its links (Blog -> /show/blog/ which only redirects).

*Dateien:* `site_sidebar.py`, `site_podpage.py`, `generate_site.py`, `site_entities.py`, `site_blog.py`, `TODO.md`  
*Tickets:* T19

### 🟡 teilweise · M365Con elements are only partly localized: top bar in 15 languages, popup and band English-only outside en/de

`con_bar()`/`BAR_T` (generate_site.py:566-579) have strings for en + 14 languages and the bar is injected into every header via `site_header(..., con_bar(lang))` (line 628). The popup/countdown script assets/attend.js only has `T = {en, de}` and falls back to English for the other 13 languages (lines 6-10, `L = T[lang] || T.en`). `m365con_band()` (generate_site.py:560-563) is hard-coded English and placed on every `/<lang>/` home (line 1100) and the root. The sidebar M365Con card has English alt text/aria-label in `render_lang()` for all languages (site_sidebar.py:96-97); only the button label uses `t['seat']`.

*Dateien:* `generate_site.py`, `assets/attend.js`, `site_sidebar.py`  
*Tickets:* T19, T7

### 🟡 teilweise · Mirko Peters is spread over four URL families; canonical entity exists but guest/host/profile pages and a duplicate 'mirko' entity are not consolidated

Canonical: `/entity/mirko-peters/` (person_ld generate_site.py:457-470 with `@id .../entity/mirko-peters/#entity`, sameAs MVP/LinkedIn/m365.fm/m365con/YouTube; `AUTHOR_EID` site_entities.py:26; `about_url()` 602-603 returns `/de/entity/mirko-peters/` for de). Parallel pages: community profile `/community/u/mirko-p/` (`AUTHOR_HANDLE` generate_site.py:667, mapped to the entity by `AUTHOR_ENT` site_members.py:98, old handle 301'd in sitewrk/index.js:33; non-en profile copies are noindex, site_members.py:248), Podpage guest page `/show/guests/mirko-peters/` (data/podpage/guests.json slug `mirko-peters`, site_podpage.py:359-371, ProfilePage mainEntity resolves to the entity via data/guest_merge.json `"mirko-peters":"mirko-peters"`), a second guest `mirko` producing `/show/guests/mirko/` and a separate guest entity `{"id":"mirko","name":"Mirko","guest":true}` in data/guest_entities.json (not merged), and `/show/hosts/` (site_podpage.py:384-385) listing the host without a link to the entity. Retired `/about/mirko-peters/` and `/<lang>/about/mirko-peters/` (data/retired.json) are only noindex stub pages, not 301s (generate_site.py:1208-1219), and the old about-page code (`about_alts`, `hl_en`, `about_body`, lines 1176-1206) is dead.

*Dateien:* `generate_site.py`, `site_entities.py`, `site_members.py`, `site_podpage.py`, `sitewrk/index.js`, `data/guest_merge.json`, `data/guest_entities.json`, `data/retired.json`  
*Tickets:* T12, T13

### ❌ fehlt · /mirko-peters is an episode slug: /show/episodes/mirko-peters/ is built in 15 languages and the legacy map 301s /mirko-peters to it

data/podpage/episodes.json.gz contains an episode with slug `mirko-peters` ("Why Power Platform Is Your Real Automation Layer — Not Custom Code", 2026-08-12). site_podpage.py:218 `ep_url` and 323 publish it at `/show/episodes/mirko-peters/`, line 330 at `/<lang>/show/episodes/mirko-peters/` for every language with a translated title, and line 429 adds `"/mirko-peters" -> "/show/episodes/mirko-peters/"` to `show/redirects.json` (438), which sitewrk/index.js:24-29 serves as a 301 when `MIGRATED=1`. No slug rename, no 301 from that episode URL to a new slug, and no redirect of `/mirko-peters/` to `/entity/mirko-peters/` is implemented.

*Dateien:* `site_podpage.py`, `sitewrk/index.js`, `data/podpage/episodes.json.gz`  
*Tickets:* T12, T8

### ✅ in Ordnung · Entity and blog pages implement a conservative en/de hreflang cluster correctly; other languages are noindex without alternates

site_entities.py:473-503: `_alts = {'en','de'}` only when the entity has real German text and is not thin, passed only for `lang in ('en','de')`, `xdefault = eurl(BASE,'en',id)`, and all other 12 language copies (`/<lang>/entity/...`) are noindex (`_noidx = lang not in ('en','de') ...`) and excluded from the sitemap. site_blog.py:69-72 and 123-127 build `_alt = {'en': original, <lang>: translation}` only between the English legacy post and languages approved in data/blog_tr.json `index` (currently build=[de]); `xdefault=(_alt or {}).get('en')`. Both are self-consistent and reciprocal; they are the pattern the dub/show pages should follow.

*Dateien:* `site_entities.py`, `site_blog.py`, `data/blog_tr.json`  
*Tickets:* T3

### 🟡 teilweise · Page types with and without alternates (inventory)

With alternates: dub episodes (dubs only), `/<lang>/` homes and `/` (dubs only), `/<lang>/podcast/`, `/<lang>/c/<cat>/`, `/<lang>/top/` (dubs only); `/show/episodes/<slug>/` + `/<lang>/show/episodes/<slug>/` (en + languages with translated notes, site_podpage.py:320-331); entity pages (en/de); legacy blog posts (en + approved); accessibility statement (all + en + x-default). Without any alternates: `/show/` hub, `/show/episodes/` lists, `/show/guests|hosts|sponsors|reviews|listen|<page>/`, `/<lang>/show/episodes/` lists, entity index, glossary (`/glossary/` vs `/de/glossary/` site_learn.py:300-306), learn/path/trainer pages, all community pages (`/community/`, members, events, library, video, podcast, guests), `/shows/...`, press, live, updates, MCP. Tag pages are noindex. `/<lang>/community/*` copies are noindex for lang != en (site_members.py:248) so their lack of hreflang is harmless.

*Dateien:* `generate_site.py`, `site_podpage.py`, `site_learn.py`, `site_members.py`, `site_events.py`, `site_library.py`, `site_video.py`, `site_podcast.py`, `site_press.py`, `site_live.py`  
*Tickets:* T3, T1

**Gegenprüfung (mit Korrekturen):** Spot-checked findings 2 (dub episode hreflang), 4 (sitemaps), 7 (dead `lal`), 8 (language switch), 9 (RTL/og:locale) and 12 (Mirko Peters consolidation). All substantive claims hold: generate_site.py:962 builds `alts` from dub languages only and :1067 calls page() without xdefault; :1048 renders the English original only as a visible link; sm_file() :1388-1396 writes xhtml:link per alt and no x-default, split core/per-lang :1400-1407; site_podpage.py:350 defines `lal` and :353-354 passes `None, None`; lang_dropdown site_design.py:206-213 prepends EN_URL (= BASE+'/show/', generate_site.py:583) and header() :625-627 falls back to language homes; LANGS 'ar' -> 'ar_AR' at :52, `.portrait{float:right...}` at :119, no `[dir=rtl]` rule anywhere; guest `mirko` exists in data/podpage/guests.json:1474 and data/guest_entities.json:2448 (guest:true, not in guest_merge.json); retired about pages are noindex stubs :1208-1219 and about_alts/hl_en/about_body :1180-1206 are defined but never used. Two citation errors only: (1) finding 12 attributes `about_url()` to site_entities.py:602-603 — it is in generate_site.py:602-603 (site_entities.py has no about_url; its line 602 is unrelated). (2) finding 8 cites the hard-coded EN tile `https://www.m365.fm` at generate_site.py:1115 — it is at generate_site.py:1118 (`tiles += lang_tile("EN", "English", "Original", "https://www.m365.fm", ...)`).

## Strukturierte Daten (T4)

Jede wichtige Seitenart gibt JSON-LD aus (PodcastSeries/PodcastEpisode mit Transkript, BlogPosting, typisierte Entitäten inkl. DefinedTerm, ProfilePage/Person, Event mit subEvents, FAQPage, WebSite, Person Mirko mit sameAs, Organization). Hauptmängel: die Person-@id /entity/mirko-peters/#entity ist mit vier verschiedenen Eigenschaftssätzen definiert, Dub-Folgen tragen im transcript eine URL statt Text, Mitgliederprofile führen ein ungültiges review-Feld an Person, Updates-Seite ohne JSON-LD, BreadcrumbList nur teilweise.

### 🟡 teilweise · Root home (/) JSON-LD: Person, Organization, Event, FAQPage, WebSite present; no series node

generate_site.py:1137-1139 emits person_ld(), org_ld(), event_ld() (M365Con), faq_ld('en') and a WebSite (@id /#website, publisher/author refs). There is no PodcastSeries on the English entry page (the English show lives at /show/) and no BreadcrumbList. WebSite has no potentialAction and Organization carries no description/contactPoint.

*Dateien:* `generate_site.py:1137-1139`, `generate_site.py:529-541`, `generate_site.py:551-552`  
*Tickets:* T4, T2

### ✅ in Ordnung · Language home (/<lang>/): PodcastSeries + CollectionPage/ItemList + FAQ + Person + Org

generate_site.py:1080-1088 emits PodcastSeries with @id /<l>/#series, webFeed, sameAs (platform URLs), numberOfEpisodes, author/publisher refs, plus CollectionPage>ItemList (first 50), faq_ld(l), person_ld(), org_ld(). Only gaps: CollectionPage has no @id and there is no BreadcrumbList; series image is the generic og-default.png.

*Dateien:* `generate_site.py:1080-1088`  
*Tickets:* T4

### 🟡 teilweise · English show home (/show/): PodcastSeries has no @id, no author/publisher/image

site_podpage.py:418 emits a PodcastSeries (name, url, description, inLanguage, webFeed, sameAs from platforms.json) but without @id, author, publisher or image. Episode pages inline their own partOfSeries {name,url} (site_podpage.py:299) instead of referencing a shared series @id, so the English show is not one node in the graph. No BreadcrumbList on the show home.

*Dateien:* `site_podpage.py:418-419`, `site_podpage.py:299`  
*Tickets:* T4, T2

### 🟡 teilweise · English episode page (/show/episodes/<slug>/): PodcastEpisode with transcript, breadcrumb, FAQ; Person/Org nodes absent, no VideoObject

site_podpage.py:298-315 emits PodcastEpisode (@id #episode, datePublished, description, image, partOfSeries inline, author {@id mirko-peters#entity}, episodeNumber, duration/timeRequired, about/contributor entity refs, partOfSeason, associatedMedia, sameAs platform links, transcript truncated to 5000 chars) plus a BreadcrumbList (line 307) and a FAQPage from SNT.sections/SECTIONS. Missing: the Person and Organization nodes are not emitted on these pages (pub() at line 200-203 passes only ld+nld), so the author @id is a dangling reference on-page; no VideoObject although video_link exists; no publisher; transcript is cut at 5000 chars rather than full text or a URL.

*Dateien:* `site_podpage.py:298-315`, `site_podpage.py:200-203`, `site_notes.py:66`  
*Tickets:* T4, T18

### 🐞 Fehler · Dub-language episode page (/<lang>/<slug>/): transcript property holds a URL, series link points to Spreaker

generate_site.py:970-989 emits PodcastEpisode (no @id), BreadcrumbList, VideoObject (@id #video, thumbnails, uploadDate, embedUrl), person_ld(), org_ld(), optional Article (line 1014) and FAQPage (line 1030). Two problems: `transcript` is set to e['tr'] which is a raw.githubusercontent.com URL to a .txt (generate_site.py:965, 976; episodes/*.json 'tr'), while schema.org transcript expects Text; and partOfSeries.url is the Spreaker show URL (line 978) instead of the on-site series @id /<l>/#series defined on the language home, so episode and series are not linked. Article has no @id and reuses the OG PNG as image.

*Dateien:* `generate_site.py:965-989`, `generate_site.py:1014-1031`  
*Tickets:* T4, T13

### 🟡 teilweise · Localized Podpage episode copies (/<lang>/show/episodes/<slug>/): minimal PodcastEpisode

site_podpage.py:326-328 emits PodcastEpisode (name, url, datePublished, description, inLanguage, partOfSeries inline, author ref, associatedMedia) without @id, sameAs, transcript, BreadcrumbList or Person/Org nodes. Versions without translated notes are noindex (_thin), so this mainly affects the ~150 per language that are indexable.

*Dateien:* `site_podpage.py:320-331`  
*Tickets:* T4, T17

### 🟡 teilweise · Blog posts (site_blog.py, incl. legacy Podpage posts): BlogPosting without publisher or breadcrumb

site_blog.py:115-118 emits BlogPosting (@id #post, mainEntityOfPage, headline, description, image list, datePublished/dateModified, author array via _author_node (entity @id or profile #person), about entity refs, citation) plus FAQPage from SNT.sections; legacy Podpage posts flow through the same path with their FAQ restored from the Podpage export (site_legacy_blog.py:25-33). Missing: publisher (Organization) which Google recommends for Article, BreadcrumbList, and an on-page Person node for the author beyond name/url. Blog index emits Blog with blogPost @id refs (line 149).

*Dateien:* `site_blog.py:33-36`, `site_blog.py:115-118`, `site_blog.py:149-150`, `site_legacy_blog.py:25-33`  
*Tickets:* T4, T14

### 🟡 teilweise · Entity pages: rich typed node (SoftwareApplication/DefinedTerm/Organization/Person/Event/Credential) but Product/Event nodes likely incomplete for Google

site_entities.py:458-471 emits WebPage (@id #page, mainEntity = ent_ld node, nested BreadcrumbList, speakable, isPartOf #website, author Mirko ref, hasPart), ItemList #articles, FAQPage #faq and ItemList #episodes; ent_ld (lines 55-170) maps types to SoftwareApplication+Product, DefinedTerm (inDefinedTermSet, termCode), Organization, Person, EducationalOccupationalCredential, Event, PodcastSeries with sameAs (web, wikipedia, docs, wikidata, same_as, claimed profile). Likely invalid: products get @type ['SoftwareApplication','Product'] (line 84) but offers only when license is free/included (line 82-83) and never an image, so Google will flag missing offers/image; event entities get location but startDate only if e['start'] exists (line 142-146); Person.performerIn Events (lines 165-168) have no startDate when no session is dated.

*Dateien:* `site_entities.py:55-170`, `site_entities.py:458-471`  
*Tickets:* T4, T13

### 🐞 Fehler · Person 'Mirko Peters' @id /entity/mirko-peters/#entity is defined with four different property sets

The same @id is defined by generate_site.py:457-489 person_ld() (url switches to /community/u/mirko-p/ when the profile loads, mainEntityOfPage stays the entity, sameAs includes itself), by site_entities.py ent_ld() on the entity page (line 62, person branch 152-168), by site_blog.py:35 _author_node (name/url/sameAs only) and by site_podpage.py:369 for merged guests (jobTitle/sameAs from Podpage). site_members.py:107 additionally defines a second identity node /community/u/mirko-p/#person linked only via sameAs. check_schema.py:93 only warns about conflicting #person/#org definitions, so #entity conflicts go unnoticed; about_body() in generate_site.py:1184 is dead code (no about page is written any more).

*Dateien:* `generate_site.py:457-489`, `site_entities.py:62`, `site_blog.py:33-36`, `site_podpage.py:369-370`, `site_members.py:107`, `check_schema.py:92-94`, `generate_site.py:1184`  
*Tickets:* T4, T12

### 🟡 teilweise · Organization node: emitted only on some page types, logo is the OG image

org_ld() (generate_site.py:529-532) defines @id /#org with name, url, logo = assets/og-default.png (a 1200x630 share image, not a logo), founder and sameAs; it is emitted on /, /<lang>/, dub episode pages and /press/ only. English show/episode pages, blog posts, entity pages, events and member pages reference {@id: /#org} or omit it, so within those pages the publisher reference is dangling. No description, contactPoint or address (the press page prints the postal address as text only).

*Dateien:* `generate_site.py:529-532`, `site_press.py:110`  
*Tickets:* T4

### 🟡 teilweise · Event pages: Event with sessions as subEvent; subEvents lack location, no image, paid offers lack price; M365Con exists as three unlinked nodes

site_events.py:42-97 emits Event (@id #event, startDate/endDate, eventAttendanceMode, eventStatus, isAccessibleForFree, VirtualLocation/Place, organizer, offers, sponsor, about, subEvent with performer/about/recordedIn). Each nested subEvent (line 74-93) has no location, which Google requires on every Event; offers (line 65) carries price only for free events; no image; non-English event pages are noindex (line 248 pattern in build). M365Con is modelled separately as a hard-coded home Event @id /#m365con2027 (generate_site.py:535-541, dates 2027-01-11..22), as entity 'm365con' (#entity, data/entities.json) and as a community event, with no sameAs/@id link between them.

*Dateien:* `site_events.py:42-97`, `site_events.py:208-209`, `generate_site.py:535-541`  
*Tickets:* T4

### 🐞 Fehler · Member profiles: Person carries a 'review' property that schema.org Person does not have

site_members.py:107-161 builds ProfilePage (@id #profile) > Person (@id #person) with image, description, jobTitle, address, worksFor, knowsAbout, hasCredential, award, memberOf, sameAs (incl. entity link), agentInteractionStatistic. Line 111 adds `review` (Review objects from recommendations) to the Person node; `review` is not a property of Person in schema.org and Google does not allow review snippets on Person, so validators flag it. Org profiles (165-186) are fine; profile pages have no BreadcrumbList and non-English copies are noindex.

*Dateien:* `site_members.py:107-161`, `site_members.py:288`, `site_members.py:308`  
*Tickets:* T4

### 🟡 teilweise · Guest pages (/show/guests/): ProfilePage without @id/url, Person reuses entity @id

site_podpage.py:369-370 emits ProfilePage > Person with name, jobTitle and sameAs from Podpage social links; the Person @id is the entity #entity when a guest entity exists, otherwise /show/guests/<slug>/#p. ProfilePage lacks @id, url and dateModified, and there is no breadcrumb or link to the episodes list in JSON-LD.

*Dateien:* `site_podpage.py:369-371`  
*Tickets:* T4, T13

### 🟡 teilweise · Glossary / learn: DefinedTermSet on /glossary/, DefinedTerm only on entity pages; learn hub has no JSON-LD

site_learn.py:288-306 emits DefinedTermSet (@id /glossary/#set, hasDefinedTerm refs to entity #entity) on /glossary/ and /de/glossary/; single term pages are retired stubs with empty LD (line 311), and the DefinedTerm branch of gloss_ld (line 294) is never called. DefinedTerm nodes are produced on entity pages via site_entities.py:113 (inDefinedTermSet glossary set or entity set, termCode). Other-language glossaries are noindex without LD, /<lang>/learn/ (line 370) has no JSON-LD, and learning paths (line 337) emit an ItemList without url/@id.

*Dateien:* `site_learn.py:288-311`, `site_learn.py:337-338`, `site_learn.py:370`, `site_entities.py:113`  
*Tickets:* T4

### ❌ fehlt · Updates page has no JSON-LD

generate_site.py:1140-1147 writes /updates/ and /de/updates/ via page() without a jsonld argument, so no CollectionPage/ItemList or dateModified is emitted even though the page is in the sitemap. site_updates.py only renders HTML blocks.

*Dateien:* `generate_site.py:1140-1147`, `site_updates.py:69-89`  
*Tickets:* T4, T20

### 🟡 teilweise · BreadcrumbList coverage is partial

BreadcrumbList is emitted on dub episode pages (generate_site.py:980-983), English episode pages (site_podpage.py:307), category/tag archives (generate_site.py:1320, 1368) and nested inside WebPage on entity pages (site_entities.py:463). It is missing on blog posts and blog index, member/company profiles, event pages, guest pages, glossary, learn, updates, show home, language homes, press and live pages.

*Dateien:* `generate_site.py:980-983`, `site_podpage.py:307`, `site_entities.py:463`, `site_blog.py:115`, `site_events.py:208`  
*Tickets:* T4

### ✅ in Ordnung · FAQPage emitted on home, language homes, episodes, blog posts and entities

faq_ld() (generate_site.py:551-552) is on / and /<lang>/; dub episode pages add FAQPage from article FAQ (line 1030); English episodes and blog posts get FAQPage via site_notes.sections (site_notes.py:66); entity pages emit FAQPage @id #faq (site_entities.py:468). Nodes other than the entity one have no @id/url, and since Google limits FAQ rich results to government/health sites the SEO value is informational only.

*Dateien:* `generate_site.py:551-552`, `site_notes.py:66`, `site_entities.py:468`  
*Tickets:* T4

### 🟡 teilweise · Community shows/podcast/video pages: inconsistent author identity (inline Person vs #person @id)

site_shows.py:36-44 emits PodcastEpisode/PodcastSeries without @id and with an inline author Person (name/url), whereas site_podcast.py:52 and site_video.py:53 use the profile @id /community/u/<handle>/#person. The result is two different nodes for the same host across page types; show episodes also truncate transcript to 5000 chars.

*Dateien:* `site_shows.py:36-44`, `site_podcast.py:51-54`, `site_video.py:51-53`  
*Tickets:* T4, T12

### 🟡 teilweise · check_schema.py validates built pages in CI but misses #entity conflicts and type-specific Google requirements

check_schema.py checks required fields per type (REQ table lines 9-19), absolute URLs, ISO dates, dangling @id refs and conflicting definitions, and runs in .github/workflows/site.yml:157. It does not check SoftwareApplication/Product offers+image, nested subEvent location, Person.review validity, or conflicting definitions of #entity ids (line 93 only matches #person/#org), so the issues above pass CI.

*Dateien:* `check_schema.py:9-19`, `check_schema.py:92-94`, `.github/workflows/site.yml:157`  
*Tickets:* T4

**Gegenprüfung (mit Korrekturen):** Spot-checked 5 findings (dub episode transcript/series, English episode Person/Org absence, Person @id consolidation incl. check_schema + about_body, member Person.review, events subEvent/offers; plus the entity Product image claim). Substantive claims hold, but three details are wrong: (1) Dub-language episode page: e['tr'] is a raw.githubusercontent.com URL to a .vtt file (transcripts/<lang>/<vid>.vtt, see episodes/0CI-mzhWEWE.json and /tmp/wt-t0/generate_site.py:965,976), not a .txt; the rest (transcript holds a URL, partOfSeries.url = Spreaker show at generate_site.py:978) is correct. (2) check_schema.py: the conflicting-definition warning that only covers '#person'/'#org' is at /tmp/wt-t0/check_schema.py:85-86, not line 93 (lines 92-94 are the summary print/sys.exit). The claim itself (no warning for #entity conflicts) is correct. (3) Entity pages: the claim that products 'never' get an image is inaccurate at code level — /tmp/wt-t0/site_entities.py:66-67 sets n['image'] = e['logo'] for every non-org type including products; it is only true in effect because none of the 141 product entities in data/entities.json has a 'logo' value. Verified as correct: person_ld() at generate_site.py:457-489 (url switched to /community/u/<handle>/, mainEntityOfPage stays entity, sameAs includes own #entity); about_body() at generate_site.py:1184 has no call site (also about_alts/about_en_url/hl_en at 1180-1182 are unused); site_members.py:110-111 adds 'review' to the Person node; site_podpage.py:200-203 pub() passes only the given ld to page() so Person/Org nodes are absent on English episode pages, transcript cut at 5000 chars (line 316); site_events.py:66 offers carry price only when free, subEvents (74-93) have no location; updates pages written without jsonld at generate_site.py:1140-1147; BlogPosting at site_blog.py:115-118 has no publisher; guest ProfilePage at site_podpage.py:369-370 has no @id/url.

## Sitemaps, robots, llms.txt, Feeds, Indexierung (T1, T16, T13)

Sitemap-Index je Sprache plus Kerndatei, konsistente noindex-Regeln (jede noindex-Seite bleibt aus der Sitemap), robots.txt mit Sitemap-Zeile und KI-Bot-Freigaben, llms.txt-Familie vorhanden. Lücken: keine Sitemaps je Typ, lastmod = Baudatum für Hubs, kein x-default in der Sitemap, IndexNow schickt bei jedem Deploy die gesamte Sitemap (PR 70 löst das durch gezielten Purge), keine Sitemap-Validierung im Build.

### 🟡 teilweise · Sitemap index exists, but split by URL prefix only (no per-type sitemaps, no /en/)

generate_site.py:1387-1412 writes sitemap.xml as a <sitemapindex> over sitemap-core.xml plus one sitemap-<lang>.xml per active dub language; the split is purely `url.startswith(BASE/<lang>/)` (line 1400/1404). sitemap-core.xml therefore lumps every English page (/show/episodes/* ~1,119, /entity/* ~576, /community/u/*/blog/* ~2,300 legacy posts, events, members, glossary, learn) into one file; there are no type sitemaps (episodes/entities/blog/events) and no English-language sitemap as T1/T2 ask. PR 70 reports 38,718 sitemap URLs in total, still well under the 50,000 URL / 50 MB per-file limit, so correctness is fine; the gap is granularity for Search Console diagnostics.

*Dateien:* `generate_site.py`  
*Tickets:* T1, T2

### 🐞 Fehler · lastmod is TODAY for most hub pages, so the sitemap index lastmod is always the build date

Language homepages (generate_site.py:1104), root (1140), updates (1148), accessibility (1164), category pages (1338/1345), learn hubs and paths (site_learn.py:307/340/371), member/company/event pages and directories (site_members.py:291/311/327, site_events.py:215/226), press (site_press.py:112), localized show lists (site_podpage.py:355) all append `TODAY`. Because each sitemap-<lang>.xml lastmod is `max(e[1])` (line 1405) and the homepage is always TODAY, every entry in sitemap.xml shows the build date on every daily run (site.yml cron 17 5 * * *), which Google treats as untrustworthy and ignores. Real dates exist only for dub episodes (1068, episode date), blog posts (site_blog.py:129 updated/published), entities (site_entities.py:437-439 via content hash in data/entity_mod.json), show episodes (site_podpage.py:204/331 update_time), feed/podcast/video items. Fix: derive hub lastmod from max(child lastmod) and reuse the entity_mod.json hash approach for lists.

*Dateien:* `generate_site.py`, `site_learn.py`, `site_members.py`, `site_events.py`, `site_entities.py`, `site_podpage.py`  
*Tickets:* T1

### 🟡 teilweise · Sitemap hreflang incomplete: no x-default, show episodes lose their alternates

sm_file (generate_site.py:1388-1396) emits <xhtml:link hreflang> only for entries carrying alts (dub episodes 1068, language homepages 1104, approved blog translations site_blog.py:129, en/de entities site_entities.py:498, accessibility 1164) and never writes an x-default link, although page() writes x-default in HTML (line 395). The English show episode page gets hreflang alternates in HTML (site_podpage.py:313-314 `alts`), but pub() appends the sitemap entry with `None` (site_podpage.py:204) and the localized entries at line 331 also append `None`, so sitemap and HTML hreflang disagree for the main show. Top pages (1379) carry alts; category pages (1345) do too.

*Dateien:* `generate_site.py`, `site_podpage.py`, `site_blog.py`, `site_entities.py`  
*Tickets:* T1, T3

### ✅ in Ordnung · robots.txt: permissive, correct for noindex strategy, single Sitemap line

generate_site.py:1415 writes `User-agent: *`, `Content-Signal: search=yes, ai-input=yes, ai-train=yes`, `Allow: /`, an explicit Allow block for GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-User, Claude-SearchBot, PerplexityBot, Google-Extended, Applebot-Extended, Bingbot, and `Sitemap: <BASE>/sitemap.xml`. There is no Disallow, which is right because every excluded page relies on meta `noindex,follow` (line 421) and must stay crawlable; the per-bot Allow lines are redundant with `*` but harmless. Not covered: the 657 noindex tag pages (line 1351) and ~15,700 thin localized show pages (site_podpage.py:312) still consume crawl budget; a `Disallow: /*/tag/` would be a cheap win. The site worker does not alter robots.txt.

*Dateien:* `generate_site.py`, `sitewrk/index.js`  
*Tickets:* T1

### ✅ in Ordnung · noindex rules are consistent and every noindex page is kept out of the sitemap

page() emits `noindex,follow` and drops ads/OG generation for noindex pages (generate_site.py:398-421, site_ads.py:48/79). Rules today: legal pages (1150-1154), /community/ profile app per language (1166-1169), retired pages (1208-1220), tag pages (1343), top pages of provisional languages (1377), 404/callback (1592-1597), entities outside en/de or thin persons (site_entities.py:483), localized glossary/trainer (site_learn.py:324/359), blog posts <10 upvotes and unapproved translations (site_blog.py:120-123, INDEX_VOTES at :85, data/blog_tr.json), library <10 votes (site_library.py:69), members/companies/events outside en (site_members.py:248, site_events.py:174), guests outside en/de (site_guests.py:31), [Test] podcast/video (site_podcast.py:55, site_video.py:55), pulled feed items without >=300 chars own text (site_feed.py:59), paginated lists and thin localized show episodes (site_podpage.py:331/338/354), seo report page (site_seo.py:62). Every one of these guards the matching `sitemap.append` (e.g. site_blog.py:128, site_entities.py:498, site_podpage.py:204/331, site_members.py:290-327, site_events.py:214-226, site_feed.py:60). The sitewrk NOINDEX regex (sitewrk/index.js:12) adds X-Robots-Tag for entities.json/.jsonld, og-manifest.json, seo-report.json, top.json, show/redirects.json, show-notes/, blog-import/ and *.jsonld.

*Dateien:* `generate_site.py`, `sitewrk/index.js`, `site_blog.py`, `site_entities.py`, `site_podpage.py`, `site_feed.py`  
*Tickets:* T1, T6

### 🟡 teilweise · Worker NOINDEX allowlist misses newer JSON exports

sitewrk/index.js:12 lists the exports that get `x-robots-tag: noindex`, but the build now also writes articles.json (generate_site.py:1452), topics.json (1613), speakers.json (953), translation-status.json (site_trstatus.py:63) and show/redirect-conflicts.json (site_podpage.py:439); none match the regex, so they are indexable JSON. agent.json, episodes.json, openapi.json, llms*.txt and .well-known/* are deliberately left indexable (comment at line 11), which is fine. Add the five files (or switch to a `\.json$` rule with an allowlist for agent/episodes/openapi).

*Dateien:* `sitewrk/index.js`, `generate_site.py`, `site_trstatus.py`, `site_podpage.py`  
*Tickets:* T1

### 🐞 Fehler · IndexNow resubmits the entire sitemap on every deploy

.github/workflows/site.yml:193-215 fetches sitemap.xml, expands every child sitemap and POSTs all ~38k URLs to api.indexnow.org in 9,000-URL batches after each deploy (daily cron plus every push to main). IndexNow is meant for changed URLs only; bulk resubmission of identical sets is documented as a reason for engines to deprioritise a key. The key is also duplicated as a literal (generate_site.py:38 INDEXNOW_KEY and site.yml:198). PR 70 (branch claude/ap20a-thin-pages) replaces this with tools/page_hashes.py + tools/purge_changed.py so only changed pages are purged and submitted; that part should land regardless of the R2 decision.

*Dateien:* `.github/workflows/site.yml`, `generate_site.py`  
*Tickets:* T1

### 🟡 teilweise · llms.txt family is in place; several content areas and per-language files are missing

generate_site.py:1416-1461 writes llms.txt (Core, Main show/knowledge graph/blog, Languages with topics, Topics), llms-full.txt (all dub episodes per language, 200-char summaries), llms-show.txt (English show with summary + 3 key points), llms-entities.txt, llms-blog.txt, plus articles.json, episodes.json, agent.json, .well-known/agent.json, agent-card.json, mcp/server-card.json, agent-skills/index.json, openapi.json and api-catalog (1486-1568), and the worker adds a Link header on `/` (sitewrk/index.js:44). Missing for T16: no list for events/M365Con/speakers, community podcast/video/library, members/companies, /updates/ or glossary terms; no per-language `/<lang>/llms.txt`; no `generated` date in the text files; the M365Con dates are hardcoded twice (1420 and event_ld at 537) instead of coming from site_events data; llms-blog.txt is titled 'articles by Mirko Peters' but `_bp` (1448) lists every English post of any author; llms-full.txt covers only dubs while the English show lives in llms-show.txt (naming is confusing for agents). llms.txt is not referenced from HTML (<link rel="alternate"> or footer), only via the root Link header.

*Dateien:* `generate_site.py`, `sitewrk/index.js`  
*Tickets:* T16

### 🟡 teilweise · episodes.json mixes two record shapes; show entries lack alternates, dub entries lack entities

generate_site.py:1462-1469 builds dub records (id=YouTube vid, language, categories, tags, youtube, spreaker, alternates across dub languages) and appends show records (kind 'show': keypoints, entities from _ep_about, guests, duration) with `alternates: {}` although 150 localized show-note versions per language are index + hreflang (site_podpage.py:312-313, data/podpage_i18n/notes_*.json). Dub records carry no `entities` and show records carry no categories/tags/youtube/spreaker, so an agent following agent.json's find-episode skill (1480) cannot filter uniformly. No transcript URL is exposed even though PodcastEpisode JSON-LD embeds up to 5,000 chars (site_podpage.py:311). Suggest one schema with kind, language, entities, alternates, transcript for both kinds.

*Dateien:* `generate_site.py`, `site_podpage.py`  
*Tickets:* T13, T16

### 🟡 teilweise · Episode <-> entity mapping is string matching only, one-directional for dubs, exported to topics.json

English show: PP.find_episodes (site_podpage.py:139-160) scores entity name/alias regex hits in title (3) and key points/FAQ (1), max 12 per entity; dub languages: regex over title + tags, max 12 (generate_site.py:1236-1241). The reverse map `_ep_about` (1243-1248) feeds PodcastEpisode.about (site_podpage.py:303), episodes.json entities and topics.json weights for the worker's content_topic table (1606-1613). Entity sameAs is assembled from web/wikipedia/docs/wikidata/same_as plus a claimed community profile (site_entities.py:58-71); guest entities get sameAs from Podpage social links (site_podpage.py:172-175). Missing for T13: no manual override/exclusion file for false positives, no mapping for dub episodes in episodes.json or topics.json, no weights beyond list position, and entity feeds/ItemLists only cover English episodes.

*Dateien:* `site_podpage.py`, `generate_site.py`, `site_entities.py`  
*Tickets:* T13

### 🟡 teilweise · Feeds: Spreaker RSS for shows, first-party RSS for blog and entities, but poorly advertised and English-only for entities

Podcast feeds are Spreaker's (agent.json 'rss' at generate_site.py:1478, PodcastSeries.webFeed at 1081 and site_podpage.py:425); there is no first-party RSS per language. Blog feeds exist at /<lang>/community/blog/feed.xml and /<lang>/community/u/<handle>/blog/feed.xml for all 15 COMM_LANGS (site_blog.py:146/151, 50 items, rss() at 157-162), entity feeds at /entity/<id>/feed.xml only for lang == 'en' (site_entities.py:484-495, 40 items of articles + episodes). Only entity pages advertise their feed with <link rel="alternate" type="application/rss+xml"> (site_entities.py:496); blog pages, the German entity page (which links the English feed) and llms.txt/agent.json do not mention the blog feeds. All feeds are bare RSS 2.0 without atom:link rel=self, lastBuildDate or category on blog items; blog feeds are written even for languages whose pages are noindex (site_blog.py:146).

*Dateien:* `site_blog.py`, `site_entities.py`, `generate_site.py`, `site_podpage.py`  
*Tickets:* T16, T13, T6

### 🟡 teilweise · GitHub Pages size and the PR 70 R2 fallback: what it means for indexing

sizes() (generate_site.py:786-792) only prints per-directory sizes against a '1 GB Richtwert'; PR 70 measured docs/ at 1,724 MB on main (blog-import/ alone 537 MB because translations leaked into the D1 import files), which is past the GitHub Pages soft limit. Today the ~13,500 localized show pages are noindex and outside the sitemap (site_podpage.py:312/331) and only `de` blog translations are built/indexed (data/blog_tr.json), so the sitemap is small but the translated content is invisible to search. PR 70 moves ~40k translated pages (2.17 GB) to R2 and has sitewrk serve them when Pages returns 404 (patch to sitewrk/index.js:36-44), making them index + sitemap + hreflang. Indexing caveats: those URLs then depend on a Pages 404 (edge-cached 60 s via cacheTtlByStatus) plus an R2 GET per miss; R2 responses skip the `vary`/`link` logic of the normal path; and while an object is not yet uploaded the worker 301s /<lang>/show/episodes/<slug>/ to the English page, so sitemap/hreflang URLs can briefly resolve as redirects. The noindex regex is not applied to R2 responses, which is correct for HTML.

*Dateien:* `generate_site.py`, `sitewrk/index.js`, `site_podpage.py`, `data/blog_tr.json`, `site_legacy_blog.py`  
*Tickets:* T1, T3, T14, T17

### ❌ fehlt · No automated sitemap validation in the build

check_links.py and check_schema.py never read the sitemaps (no 'sitemap' reference in either), and data/urls.json (generate_site.py:1598) is written but consumed by nothing. Nothing verifies that each sitemap URL exists in docs/ (or r2out/ after PR 70), that no URL appears twice across sitemap-core/sitemap-<lang>, that noindex pages stay out, that lastmod is ISO and <= today, or that per-file limits (50k URLs / 50 MB) hold as the blog translations grow. A 30-line check reading sitemap.xml -> children -> docs/ paths would close this and could run in the existing 'Interne Links prüfen' step of site.yml.

*Dateien:* `check_links.py`, `check_schema.py`, `generate_site.py`, `.github/workflows/site.yml`  
*Tickets:* T1

### 🟡 teilweise · Blog directory page lists every post on one unpaginated page

site_blog.py:147-153 renders /community/blog/ (and per-author lists at 136-145) with `lst(it)` over all posts of the language, i.e. ~2,300 legacy posts in one HTML document, and adds it to the sitemap. That page is the only crawl path besides the per-author list and llms-blog.txt; Google's size cap for HTML (first ~2 MB) and the T6 pagination goal both apply. The Blog JSON-LD at 150 already truncates to 50 posts, so the page and its schema disagree.

*Dateien:* `site_blog.py`  
*Tickets:* T6, T1

**Gegenprüfung (alle Stichproben bestätigt):** 

## Encoding, Feed-Quellen, Zähler (T5, T6, T11)

Der Generator selbst ist UTF-8-sauber (encoding bei jedem Schreiben, meta charset, ensure_ascii=False). Gefunden: 5 CP850-Mojibake-Treffer in en_titles.json und live.json (aus YouTube-Titeln, nie repariert) und ca. 25 U+FFFD/doppelt kodierte Stellen in KI-Übersetzungen. GitHub-Aktivität landet im öffentlichen Feed; Startseite und Blog-Index haben keine Kartenobergrenze im HTML.

### 🐞 Fehler · Mojibake (CP850-rendered UTF-8) in en_titles.json and live.json, no repair step

grep for ÔÇ/â€/Ã¼/Ã¶ over data/*.json, data/blog_i18n (decompressed), episodes/, data/en_transcripts, data/articles, data/podpage finds exactly 5 hits: data/en_titles.json lines 28/30/32/77 ('eDiscovery ÔÇö', 'ModelÔÇæDriven', 'NextÔÇæGen', 'WonÔÇÖt') and one title in data/live.json ('Copilot Settings Microsoft WonÔÇÖt Explain'). The same video in data/en_episodes.json has the correct 'Won’t', so the damage sits in the YouTube titles fetched by fetch_en_titles.py (oEmbed) and sync_live.py (channel RSS/yt-dlp), and nothing in the generator repairs it (no ftfy/cp850/ÔÇ handling anywhere). Consequence: generate_site.py:944-946 matches videos to Podpage originals via site_podpage.norm(title), so these 4 videos never get their English-original link, and site_live.py:78-89 prints the broken title into HTML, alt text and BroadcastEvent JSON-LD.

*Dateien:* `data/en_titles.json`, `data/live.json`, `fetch_en_titles.py`, `sync_live.py`, `generate_site.py`, `site_live.py`, `site_podpage.py`  
*Tickets:* T5

### 🐞 Fehler · U+FFFD and double-encoded characters inside AI translations are published unchecked

Decompressed data/blog_i18n contains replacement characters mid-word: ru/0b,0e,0f (8), uk/05,0a (6) e.g. 'застаю��те', 'групп��', plus nl/0f with double-encoded 'Ã©Ã©n' (4). data/podpage_i18n/he.json (2), ja.json (1) and notes_uk.json (2, 'Ш��чний AI') carry the same defect. translate_blog.py:412, translate_show.py:94 and translate_notes.py:79 read batch results with a bare .decode() and store them without validating for � or mojibake; site_legacy_blog.translations() and site_podpage then render the text verbatim. A pre-write check (reject chunks containing � or Ã./â€ sequences and re-queue them) is missing.

*Dateien:* `data/blog_i18n/ru/0b.json.gz`, `data/blog_i18n/uk/05.json.gz`, `data/blog_i18n/nl/0f.json.gz`, `data/podpage_i18n/he.json`, `data/podpage_i18n/ja.json`, `data/podpage_i18n/notes_uk.json`, `translate_blog.py`, `translate_show.py`, `translate_notes.py`  
*Tickets:* T5, T17

### 🟡 teilweise · UTF-8 is explicit in the site build but several helper scripts use platform-default encoding

The generator is clean: generate_site.py:857 writes every file with encoding='utf-8', the page shell has <meta charset="utf-8"> (line 418), all JSON is dumped with ensure_ascii=False, episodes are read as utf-8-sig (yt_dub_to_spreaker.py:67) and the Windows console is reconfigured (yt_dub_to_spreaker.py:120); 89 open() calls pass encoding='utf-8'. But fetch_reviews.py:3,9,25 (run in site.yml:78), generate_site.py:1598 (data/urls.json), adfree_cue.py:35, adfree_test.py:22,26, tools/r2_upload.py:27,36, tools/seed_entities*.py and tools/translate_missing.py:34,57 open text/JSON without encoding, and install_task.bat/.ps1 set neither chcp 65001 nor PYTHONUTF8, so on the Windows dub machine these would read/write cp1252. CI runs on ubuntu (site.yml:15, Python 3.12) so the live site is currently unaffected.

*Dateien:* `generate_site.py`, `fetch_reviews.py`, `adfree_cue.py`, `adfree_test.py`, `tools/r2_upload.py`, `tools/translate_missing.py`, `install_task.ps1`, `.github/workflows/site.yml`  
*Tickets:* T5

### 🐞 Fehler · GitHub activity feeds are pulled into the public feed and onto the home page

worker/src/feeds.js:39 auto-discovers a GitHub channel as https://github.com/<user>.atom (the user's commit/issue/star activity), refreshFeeds stores up to 12 items per channel in feed_items, and /api/feed/export (worker/src/profiles.js:461-465) applies no kind filter (only hidden=0, url NOT LIKE site, 120 days, LIMIT 300). site_home.py:77-83 then renders every exported item as a 'From the creators · GitHub' card on every home page (KL explicitly labels github), without any language filter, and site_feed.py:31-61 builds a /community/feed/<id>-slug/ page per item (noindex unless body >=300). To get GitHub out of the public feed either the export query must exclude c.kind='github' or site_home/site_feed must skip that kind.

*Dateien:* `worker/src/feeds.js`, `worker/src/profiles.js`, `site_home.py`, `site_feed.py`  
*Tickets:* T6

### 🐞 Fehler · Legacy-blog dedup drops the static /de/ translations once a post is imported into D1

generate_site.py:1263-1264 dedups static Podpage posts against DB posts by slug only (_have = slugs of mirko-p from /api/blog/export; static items kept only if slug not in _have). site_legacy_blog.items() (lines 74-112) returns the English originals AND their German translations from data/blog_i18n (translations(), lines 52-71; data/blog_tr.json build=['de']) under the same slug, so as worker/src/legacyblog.js imports the English HTML posts (60 per cron run, 2307 total, VER=2) the German versions silently disappear; autotr.js only translates posts with html='' (KINDS.blog where clause), so no DB replacement exists. Side effect for T11: the home hub (site_home.py:13,56-60) only sees API posts while /community/blog/ (site_blog.py:146-152) lists API + static posts, so the 'Blog · N' chip and the blog index disagree during the migration.

*Dateien:* `generate_site.py`, `site_legacy_blog.py`, `worker/src/legacyblog.js`, `worker/src/autotr.js`, `data/blog_tr.json`, `site_home.py`  
*Tickets:* T6, T14, T17, T11

### ❌ fehlt · Home and blog index have no card cap: every item is in the HTML, JS hides all but 18

site_home.hub() (site_home.py:47-120) appends a card for every API blog post (export LIMIT 6000, worker/src/blog.js:62), every podcast episode, library item and creator video, up to 300 feed items, 40 Microsoft updates and 24 own videos; only videos (line 98) and updates (line 87) are capped, and the root home (root=True, line 50) ignores language. The JS (lines 21-30, N=18) merely sets hidden on the rest, so the DOM carries all of them. Measured on data/podpage/blog_posts.json.gz: 2307 legacy posts x 601 B average card = about 1.4 MB of blog cards alone on / once legacyblog.js has imported them, far over the 300 kB target; /community/blog/index.html and /community/u/mirko-p/blog/ list all posts in a single <ul> (site_blog.py:131-152, about 1 MB), with no pagination (Podpage episodes are paginated at PER=100, site_podpage.py:18,334-346). site.yml has no size assertion. Live verification was not possible (outbound to www.m365.fm/api-dub.m365.fm blocked by the proxy with 403).

*Dateien:* `site_home.py`, `site_blog.py`, `worker/src/blog.js`, `site_podpage.py`, `.github/workflows/site.yml`  
*Tickets:* T6, T9

### ✅ in Ordnung · Episode/language counters share the data source of the lists

generate_site.py:819-845 builds items/by_vid/by_lang/active once from episodes/*.json + data/published.json, and every counter reuses them: language page stats len(newest)=by_lang[l] (1077,1099), tiles len(by_lang[l]) (1108,1117), root stats len(items)/len(by_vid)/len(active) (1130), press n_eps/n_langs (1304), llms.txt (1424-1432) and the console summary (1616). The Podpage show count 'All {len(eps)} episodes' and episode_index() use the identical published/hidden filter (site_podpage.py:115,181), and the hub filter chips count the rendered cards themselves (site_home.py:103-106).

*Dateien:* `generate_site.py`, `site_podpage.py`, `site_home.py`  
*Tickets:* T11

### 🟡 teilweise · M365Con '120 sessions' is hard-coded in three places, not derived from program data

generate_site.py:536 (Event JSON-LD description), 562 (popup H2) and 578 (banner) carry the literal '120 sessions' for M365Con 2027, while the repo's program data holds 66 sessions/69 speakers (data/m365con_program_2026.json), 88 (m365con_program.json) and 60 (m365con_program_dach.json), and community events render their session lists from /api/events/export (site_events.py:73-205). The figure is a marketing promise rather than a count and will drift from the program and from the Event/subEvent markup T4 asks for.

*Dateien:* `generate_site.py`, `data/m365con_program_2026.json`, `site_events.py`  
*Tickets:* T11, T4, T19

### 🟡 teilweise · Community counters silently fall to 0 when the API is unreachable

All community lists and counters go through site_fetch.fetch (site_learn.py:394-397, site_fetch.py:43-62): on failure it returns the data/cache copy with a stderr warning, or None when no cache exists, and callers default to [] ('or {}').get('items', []). The build therefore succeeds with an empty hub, 'Blog · 0' chips and empty /community/blog/ pages while the episode counters stay correct, so lists and counters can disagree without the workflow failing; site.yml has no guard that compares fetched item counts against the previous build.

*Dateien:* `site_fetch.py`, `site_learn.py`, `site_home.py`, `.github/workflows/site.yml`  
*Tickets:* T11, T6

**Gegenprüfung (alle Stichproben bestätigt):** 

## Performance, Core Web Vitals (T9)

Gut: ein gehashtes externes Stylesheet (ein Jahr immutable), lokale woff2-Subsets mit font-display swap und metrisch angepassten Fallbacks (kein Font-CLS), AdSense/Clarity erst spät. Schwachstellen: Startseite rendert alle Karten ins HTML, Lenis-Scroll mit dauerhafter rAF-Schleife, ui-<lang>.js blockierend im Head (PR 71 lädt es verzögert und bündelt ca. 8 KB Inline-JS je Folgenseite), YouTube-iframe statt Klick-Fassade, Community-Skripte auf jeder Folgenseite, keine AVIF/WebP-Pipeline im Build.

### 🐞 Fehler · Home hub renders every content item into the HTML and hides all but 18 with JS

site_home.py:52-112 emits a .hub-card for every blog post, community episode, upcoming event, library item, every creator-feed item, 40 Microsoft updates, every creator video and 24 stick-man videos (on the root page across all languages, root=True makes ok() always true, generate_site.py:1133), each with data-q/data-a/data-t attributes and a summary; the inline JS (site_home.py:21-30) then hides everything beyond N=18 (line 113). The page also carries a <select> with every author and every topic. There is no server-side cap or pagination, so the home HTML scales linearly with the community DB and will blow past the 300 kB target once the ~2300 Podpage posts (T14) land in D1. Live measurement was not possible (proxy blocks www.m365.fm), but the structure alone makes this the biggest page-weight issue. Quick win: cap cards server-side at 24, emit the rest as a JSON file fetched only when a filter is used.

*Dateien:* `site_home.py:52-113`, `generate_site.py:1100`, `generate_site.py:1133`  
*Tickets:* T6, T9

### 🟡 teilweise · CSS: one hashed external stylesheet with 1-year immutable cache, but no critical CSS and 3-4 extra CSS requests per page

css_link() (generate_site.py:446-453) writes site.<sha1>.css (~36 KB raw: FONT_CSS 5.0 KB + base 9.1 KB + INDUSTRY 21.8 KB, ~7.3 KB gzip) and sitewrk/index.js:10,41 serves it immutable for a year - good. Only fx.css (697 B) is inlined (generate_site.py:383,429); no critical CSS is inlined, so first paint waits on the stylesheet. In addition a11y.css (2.9 KB) is a separate <link> at the end of <body> (generate_site.py:319,434), sbar.css (7.9 KB) on every sidebar page (line 410) and community.css (10 KB) on every episode/community page (line 595), all unhashed with max-age=3600. Quick win: concatenate a11y/sbar/community CSS into the hashed site.css and inline a small critical block (tokens, body font stack, header/hero).

*Dateien:* `generate_site.py:383`, `generate_site.py:410`, `generate_site.py:429`, `generate_site.py:446-453`, `generate_site.py:319`, `generate_site.py:595`, `assets/a11y.css`, `assets/sbar.css`, `assets/community.css`, `sitewrk/index.js:10`, `sitewrk/index.js:41`  
*Tickets:* T9, T19

### 🟡 teilweise · Per-module inline <style> blocks are emitted before the main stylesheet

Fourteen modules carry their own <style> block passed via extra_head (site_home.py:18 714 B, site_learn.py LCSS 2.4 KB / WCSS 2.5 KB, site_press.py 2.0 KB, site_entities.py:289 1.5 KB, site_members.py:196 1.1 KB, site_updates.py:14 1.0 KB, site_live.py:25, site_blog.py:55, site_library.py:34, site_notes.py:83, site_events.py:172, site_mcp.py:42, site_seo.py:11). page() prints {extra_head} before {css_link()} (generate_site.py:429), so these uncached blocks are repeated on every page and the hashed site.css overrides them at equal specificity. Quick win: move them into site.css (hashed, cached) and keep extra_head for meta tags only.

*Dateien:* `generate_site.py:429`, `site_home.py:18`, `site_learn.py:55`, `site_learn.py:115`, `site_press.py:45`, `site_entities.py:289`, `site_members.py:196`, `site_updates.py:14`, `site_live.py:25`  
*Tickets:* T9, T19

### 🐞 Fehler · Lenis smooth-scroll (smooth.js, 17.6 KB) runs a permanent rAF loop on every page

generate_site.py:436 loads assets/smooth.js (minified Lenis) deferred on every page; its init (tail of assets/smooth.js) starts an endless requestAnimationFrame loop, takes over wheel scrolling, injects a <style> and sets iframe{pointer-events:none} while scrolling. It is disabled only for reduced-motion and coarse pointers, so every desktop visit pays main-thread time (INP) and battery for a cosmetic effect that has no SEO or UX necessity. Quick win: remove smooth.js (or load it on idle only when matchMedia('(pointer:fine)') and after first interaction).

*Dateien:* `generate_site.py:436`, `assets/smooth.js`  
*Tickets:* T9, T10

### 🐞 Fehler · ui-<lang>.js is a render-blocking script in <head>

generate_site.py:387-388 inserts <script src=.../assets/ui-{lang}.js> without defer/async into <head> for community, entity and glossary pages in the non-EN/DE languages; the file (site_i18n.py:50-60) is just window.M365T = {...} translations. A synchronous external script in the head blocks parsing and first paint. Quick win: add defer (all consumers community.js/entity.js are deferred and run after it) or inline the JSON as <script type=application/json>.

*Dateien:* `generate_site.py:387-388`, `site_i18n.py:50-60`  
*Tickets:* T9

### 🐞 Fehler · YouTube embed on every episode page is a full iframe; the click-to-play facade exists but is dead code

Episode pages (generate_site.py:1052-1054) embed the Spreaker player iframe (loading=lazy, height=131, no width) and a complete youtube-nocookie.com/embed iframe (loading=lazy) directly under the cover, i.e. usually within the first viewport, so the YouTube player (~0.5-1 MB JS/CSS, several third-party origins) loads on nearly every episode view. The facade YT_JS (generate_site.py:728, '.yt' + data-id, creates the iframe on click) is defined but never referenced anywhere (single grep hit), while yt_thumb() (line 492-495) already provides a lazy srcset thumbnail. Quick win: render <div class=yt data-id> with yt_thumb and append YT_JS on episode pages; keep Spreaker lazy and add width/height or aspect-ratio.

*Dateien:* `generate_site.py:728`, `generate_site.py:1052-1054`, `generate_site.py:492-495`  
*Tickets:* T9, T18

### 🟡 teilweise · Community widget (community.css + community.js + API calls) loads on every episode page

community_tags() (generate_site.py:589-596) is appended to all episode pages (lines 1065) and adds a <link rel=stylesheet> for community.css (10 KB) inside <body>, the 26 KB community.js and a config blob. community.js:250 runs init() on DOMContentLoaded and immediately calls api-dub.m365.fm (/api/providers, comments; comments respond with cache-control: no-store, worker/src/index.js:201) - a new origin connection and two requests per page view, with no <link rel=preconnect>. Quick win: initialise the widget only when #c-comments scrolls into view (IntersectionObserver), merge community.css into site.css, and give public comment GETs a short edge cache (public, max-age=60).

*Dateien:* `generate_site.py:589-596`, `generate_site.py:1065`, `assets/community.js:16`, `assets/community.js:28`, `assets/community.js:250`, `worker/src/index.js:161`, `worker/src/index.js:201`  
*Tickets:* T9

### ✅ in Ordnung · Fonts: self-hosted woff2 subsets with font-display:swap and metric-matched fallbacks (CLS-safe); preloads unconditional and font cache only 1 day

site_design.py:7-27 declares 12 subsetted woff2 files (assets/fonts, 14-23 KB each; all present) with font-display:swap and size-adjust/ascent-override local fallbacks, so the swap causes no layout shift; generate_site.py:428 preloads barlow-latin-400 and barlow-condensed-latin-600, which match body and h1/h2 weights. Caveats: the two preloads are emitted on ar/he/ja/ko/ru/uk pages too, where Barlow's latin unicode-range renders almost nothing (~45 KB downloaded unused); fonts get only max-age=86400 (sitewrk/index.js:41) although they never change. Quick win: skip font preload for non-Latin languages and cache /assets/fonts/ immutable for a year.

*Dateien:* `site_design.py:7-27`, `generate_site.py:428`, `assets/fonts`, `sitewrk/index.js:9`, `sitewrk/index.js:41`  
*Tickets:* T9

### 🟡 teilweise · Images: no AVIF/WebP pipeline in the build; relies on Cloudflare Polish; third-party thumbnails bypass it

Own assets are mixed: attending-m365con.webp (69 KB, 675x563 for a ~300 px sidebar slot, no srcset), gsource.webp 11 KB, mirko-peters.jpg / mirko-peters-800.jpg (JPEG only, 8/63 KB, no WebP or srcset), og-default.png 548 KB. Format conversion is delegated to the worker (sitewrk/index.js:35 polish:lossy + mirage, CLOUDFLARE.md:34), which only touches same-zone images; YouTube thumbnails on home/lists (yt_thumb generate_site.py:492-495, site_home.py:106) and feed thumbs still come from i.ytimg.com / creator hosts, contrary to the CLAUDE.md R2 rule (data/r2_map.json has 878 entries, rewrite at write time generate_site.py:857, none for own assets). OG images are 1200x630 PNG screenshots (generate_og.py:86-92) - acceptable for social cards. Quick win: ship resized WebP/AVIF for the sidebar card and portrait with srcset, and route YouTube thumbnails through img.m365.fm.

*Dateien:* `assets/attending-m365con.webp`, `assets/mirko-peters-800.jpg`, `assets/og-default.png`, `generate_site.py:492-495`, `generate_site.py:857`, `site_home.py:106`, `site_r2.py`, `sitewrk/index.js:35`, `generate_og.py:86-92`, `CLOUDFLARE.md:34`  
*Tickets:* T9, T14

### 🟡 teilweise · Images: width/height + lazy present on generated cards, missing on blog bodies, feed thumbs and learn images

Good: yt_thumb has width/height/loading=lazy/srcset/sizes (generate_site.py:494-495), sidebar images (site_sidebar.py:45-47,82-84), flags (site_design.py:200), podpage episode cards (site_podpage.py:221, with decoding=async) and the legacy blog hero (site_legacy_blog.py:99, fetchpriority=high) all have dimensions. Missing: the Podpage HTML sanitizer (site_podpage.py:35) rewrites body <img> to src/alt/loading=lazy only - no width/height, so the ~2300 migrated articles will shift layout (CLS); feed thumbnails (site_feed.py:47) and learn images (site_learn.py:161) also lack dimensions; the home portrait (generate_site.py:1188) has dimensions but no fetchpriority. Quick win: record image dimensions in data/r2_map.json during tools/r2_upload.py and inject width/height + decoding=async in the sanitizer.

*Dateien:* `site_podpage.py:35`, `site_feed.py:47`, `site_learn.py:161`, `generate_site.py:494-495`, `generate_site.py:1188`, `site_sidebar.py:45-47`, `site_legacy_blog.py:99`  
*Tickets:* T9, T14

### ✅ in Ordnung · AdSense and Clarity are loaded late and only where needed

AdSense is enabled (data/adsense.json, fixed slots mid/end, auto_ads false); site_ads.py:58-68 emits the meta tag always but adsbygoogle.js (async) only when a block was actually injected, and inject() (lines 77-98) places at most two blocks only on indexable pages with >=2500 chars, never on home/community/legal (skip_paths); blocks reserve min-height 280/250 px (CSS line 13-15) so no CLS. Clarity (generate_site.py:270-278) is injected only after localStorage consent '1', the banner script is a tiny inline IIFE. Minor: {ADS.head} is printed before {css_link()} (generate_site.py:429); put the async ad script after the stylesheet link so the CSS keeps top priority.

*Dateien:* `site_ads.py:46-98`, `data/adsense.json`, `generate_site.py:270-278`, `generate_site.py:429`  
*Tickets:* T9

### 🟡 teilweise · Caching headers in the site worker: good baseline, but unhashed JS/CSS get 1 h, fonts 1 day, and every deploy purges the whole zone

sitewrk/index.js:35-41 sets HTML to public, max-age=0, s-maxage=600, stale-while-revalidate=86400 (edge TTL 600 s), hashed site.*.css immutable 1 y, images/static max-age=3600 + s-maxage=86400 with polish/mirage and vary: accept, fonts max-age=86400, plus HSTS/nosniff/referrer headers. Gaps: all assets/*.js (~330 KB total), community.css, sbar.css, a11y.css and images are unhashed so browsers revalidate hourly; site.yml:191 runs purge_everything after every (daily) deploy, which evicts images/fonts/CSS from the edge as well; the worker emits no Link: rel=preload for site.css/fonts (only the api-catalog link on '/', line 44) so Early Hints cannot kick in. Quick win: content-hash JS like CSS (HASHED regex line 10), cache /assets/fonts/ and hashed JS for a year, purge by prefix (HTML + sitemaps) instead of everything, and add a Link preload header for the stylesheet.

*Dateien:* `sitewrk/index.js:9-10`, `sitewrk/index.js:35-44`, `.github/workflows/site.yml:191`, `CLOUDFLARE.md:8`  
*Tickets:* T9

### 🟡 teilweise · Episode pages carry ~8 KB of repeated inline JS that could be one hashed file

Every episode page (generate_site.py:1065) ends with PLAT_JS (0.5 KB), INFO_JS (2.6 KB), GLOSS_JS (2.2 KB), optional QUIZ_JS (2.6 KB), the share script (line 253) and the consent script (line 272), all inline and therefore re-downloaded with every one of the ~1,600 language pages. A11Y_EARLY (378 B, generate_site.py:311) is deliberately synchronous to avoid a theme flash - fine. Quick win: bundle PLAT/INFO/GLOSS/QUIZ/share/consent into one hashed page.js loaded with defer.

*Dateien:* `generate_site.py:253`, `generate_site.py:272`, `generate_site.py:311`, `generate_site.py:728-780`, `generate_site.py:1065`, `site_learn.py`  
*Tickets:* T9

### 🟡 teilweise · Community pages load 16 separate deferred scripts (~220 KB JS)

generate_site.py:1169 renders the client-side community hub with profile.js (48 KB), events.js (31 KB), editor.js (25 KB), community.js (26 KB), entity/notes/blog/podcast/shows/video/library/guests/feeditems/wish/mailprefs/messages.js etc., all unhashed and unbundled; admin.js (33 KB) is separate. These pages are noindex, so Core Web Vitals impact on SEO is nil, but the 16 requests and ~220 KB are a bundling/minification candidate. Low priority.

*Dateien:* `generate_site.py:1169`, `assets/profile.js`, `assets/events.js`, `assets/editor.js`, `assets/community.js`  
*Tickets:* T9

### 🟡 teilweise · Estimated page weights (from code; live fetch blocked by the sandbox proxy)

Episode page: header + sidebar + inline SVG cover (site_cover.py, 1200x420 vector, no image request - good for LCP) + article + JSON-LD (transcript is only a URL, episodes/*.json 'tr', so no bloat) + ~8 KB inline JS + 2-5 KB module CSS, roughly 60-120 KB HTML uncompressed; first view then needs site.css (36 KB/7 KB gz), 2-6 font subsets (~45-130 KB), a11y.css, sbar.css, community.css, smooth/attend/fx/a11y/community.js (~52 KB) and the Spreaker (~300 KB) and YouTube (~600 KB+) iframes, which dominate the transfer. Home: all hub cards in HTML (see finding 1) - very likely already above the 300 kB target and growing with the DB. Language home pages (/de/ etc.) use the same hub per language plus 24 lazy yt thumbnails with srcset up to maxresdefault (1280w) capped by sizes to 380 px, which is fine.

*Dateien:* `site_home.py`, `generate_site.py:1052-1065`, `generate_site.py:1100`, `site_cover.py:74-117`, `episodes/0CI-mzhWEWE.json`  
*Tickets:* T6, T9

**Gegenprüfung (alle Stichproben bestätigt):** 

## Barrierefreiheit (T10)

Besser als der Durchschnitt: Skip-Link in 15 Sprachen, korrektes lang/dir (ar/he rtl), Landmarks auf Desktop, iframes mit Titel, Einstellungspanel und Erklärung in 15 Sprachen, reduced-motion, Farbtoken mit WCAG AA. Lücken: keine globale :focus-visible-Regel, hover-only-Zustände, Dialoge ohne Fokus-Falle (attend.js bekommt sie in PR 71), doppelte Navigation auf Show-Seiten, Filter ohne Ergebnis-Ansage, M365Con-Leiste als sticky div vor dem H1.

### ✅ in Ordnung · Skip link present on every generated page, in all 15 languages

page() prepends <a class="skip" href="#main"> whenever the body contains id="main" (generate_site.py:413-414); single_main() guarantees the first <main> gets id="main" and demotes extra <main>s to labelled <section>s (generate_site.py:360-380). Labels exist for all 15 languages in SKIP_T (generate_site.py:300-302) and the CSS hides it off-canvas until focus (.skip / .skip:focus, site_design.py:94). Lenis smooth scroll (assets/smooth.js, anchors:true) intercepts '#' clicks but does not preventDefault, so focus still lands on #main.

*Dateien:* `generate_site.py`, `site_design.py`, `assets/smooth.js`  
*Tickets:* T10

### 🟡 teilweise · Landmarks: header/nav/main/footer/aside exist, but no <nav> on mobile and header uses display:contents

site_header() emits <header class="sh">, <nav class="menu" aria-label="Menu">, and footer()/sidebar/ads emit <footer>, <aside class="sbar" aria-label="Sidebar"> and <aside class="ad" aria-label> (site_design.py:224-225, generate_site.py:659, site_sidebar.py:66/86, site_ads.py:72). However the mobile menu <details class="mm"> sits outside the <nav> and the desktop nav is display:none at <=860px (site_design.py:112), so phones get no navigation landmark; .sh{display:contents} (site_design.py:94) has historically stripped the header landmark from the accessibility tree in some browsers. The aside label 'Sidebar' is generic and the sidebar hides its scrollbar (scrollbar-width:none, assets/sbar.css:4), which hides that it scrolls.

*Dateien:* `site_design.py`, `site_sidebar.py`, `assets/sbar.css`, `site_ads.py`  
*Tickets:* T10, T19

### 🟡 teilweise · Heading order is sound in templates but sidebar/JS widgets break it; breadcrumbs inconsistent

The episode template is h1 -> h2 -> h3 (generate_site.py:1046-1068) and the home hub uses h2 sections with h3 cards (site_home.py:43,59-96). But every sidebar card is an <h2> inside <aside> (site_sidebar.py:52-60, 83-86) and the show-page sb-nav card adds another <h2> 'M365.FM Show' (site_podpage.py:195), so the screen-reader heading list interleaves sidebar with article sections; profile.js creates six <h4> under only two <h3> (assets/profile.js:44,192,207). Episode breadcrumbs are a plain <div class="crumbs"> (generate_site.py:1047) while entity/event/member/learn pages use <nav aria-label="breadcrumb"> (site_entities.py:449, site_events.py:203, site_members.py:282, site_learn.py:334).

*Dateien:* `generate_site.py`, `site_sidebar.py`, `site_podpage.py`, `assets/profile.js`, `site_entities.py`  
*Tickets:* T10, T19

### 🟡 teilweise · No global :focus-visible style; hover-only states and one outline:none

Neither the base CSS block (generate_site.py:88ff) nor INDUSTRY in site_design.py defines a site-wide :focus-visible rule; only components do (.qo, .isteps li, .ichecks button.ck at site_design.py:138/153/166; a11y.css:2; community.css:20,31,46,63). Menu links, .mg/.lsw/.mm summaries (with ::-webkit-details-marker hidden), .btn, .chip, .lt, .tile and all sidebar controls (assets/sbar.css has zero focus rules) fall back to the browser default ring, while their :hover styles (site_design.py:49,73,103,105,107) have no focus twin. community.css:52 sets .ed-b:focus-visible{outline:none}, leaving only a border-colour change on editor toolbar buttons.

*Dateien:* `site_design.py`, `generate_site.py`, `assets/sbar.css`, `assets/community.css`, `assets/a11y.css`  
*Tickets:* T10

### 🟡 teilweise · Colour tokens pass WCAG AA; tile hover and 14%-alpha borders are the weak spots

Computed from site_design.py:30-32: light --mut #5d6470 on --bg #f3f3f2 = 5.37:1, --ac #3b6391 = 5.6:1, white on --ac (.btn.main) = 6.21:1; dark --mut #98a0ab on #101214 = 7.11:1, --ac #82a7d4 = 7.53:1; .mbar b #9fc0ea on --ink = 9.0:1 (site_design.py:95); high-contrast mode #ffe600 on #000 = 16.6:1 (a11y.css:8). Bug: .tile:hover{background:var(--ink);color:var(--onink)} (site_design.py:49) inverts the tile but nested .mut text keeps --mut, giving 2.84:1 on hover. Filter chips .en-f/.hub-f/.mb-f and inputs rely on border:1px solid var(--bd) where --bd is #17191c24 (14% alpha), well under the 3:1 non-text minimum (site_entities.py:289, site_home.py:18-20, site_members.py:197). Quiz ok/no states add a text prefix (site_design.py:144) so colour is not the only cue.

*Dateien:* `site_design.py`, `assets/a11y.css`, `site_home.py`, `site_entities.py`, `site_members.py`  
*Tickets:* T10

### 🟡 teilweise · html lang/dir correct for ar/he, but several physical-direction CSS rules and English-only popup

page() writes <html lang="{hl}" dir="{d}"> from LANGS, where ar and he are declared rtl (generate_site.py:52, 384-386, 418); language links carry hreflang+lang (site_design.py:191-193, 212) and the sidebar L10N has ar/he strings with mirrored arrows (site_sidebar.py:81-82). Most layout uses logical properties, but hardcoded physical values remain: .tile/.xbox/.lt '+' marks left/right (site_design.py:49,66,73), the fixed share bar .fshare{left:0} (site_design.py:149,155), generate_site.py:120 float:right and :128 left/right, site_shows.py:42 float:right, assets/sbar.css:43,57 and community.css:55 text-align:right, so these do not mirror under dir=rtl. attend.js only has en/de strings (assets/attend.js:6-9) and injects English text and an English alt into rtl pages without a lang override.

*Dateien:* `generate_site.py`, `site_design.py`, `assets/sbar.css`, `assets/community.css`, `site_shows.py`, `assets/attend.js`  
*Tickets:* T10, T19, T3

### 🟡 teilweise · Language menu is keyboard-operable via <details> but lacks a name, Escape handling and page-level targets on many pages

lang_dropdown() renders <details class="lsw"><summary>flag + code</summary> with links that carry hreflang/lang and aria-current=page for the active language (site_design.py:206-213), so Enter/Space toggles and links are tabbable. The summary has no aria-label; its accessible name is the flag alt (native name) plus the code, e.g. 'English EN', and nothing says 'Language' (site_design.py:202-203). No script closes .lsw/.mg/.mm on Escape, outside click or focus-out (no references in assets/*.js or generate_site.py), and the same applies to the menu groups and the mobile burger (site_design.py:218-225). Episode/home/top pages pass page-level alternates via lang_switch() (generate_site.py:192-194, 1045, 1096, 1324, 1372), but header(lang, "") on community, entity, show (site_podpage.py:196), press and updates pages falls back to language home pages (generate_site.py:620-621).

*Dateien:* `site_design.py`, `generate_site.py`, `site_podpage.py`  
*Tickets:* T3, T10

### 🟡 teilweise · Filters use real buttons with aria-pressed, but results are not announced and hub chips lack grouping

.en-f, .hub-f and .mb-f are <button type=button aria-pressed> whose state the scripts update on click (site_entities.py:287-288, site_home.py:21-29/106, site_members.py:316-319, assets/pfpub.js:83); en-f and mb-f sit in role="group" aria-label (site_entities.py:291, site_members.py:321) and the hub search/selects have aria-label (site_home.py:117-119). Missing: no live region reports the number of visible items after a filter (items are just set hidden), the hub-f chip row has no group/label, the selected-topic chips in #hub-sel read 'Name ✕' with the remove action only in a title attribute (site_home.py:27), and the hub-f pressed state is conveyed by border colour + bold only (site_home.py:19).

*Dateien:* `site_entities.py`, `site_home.py`, `site_members.py`, `assets/pfpub.js`  
*Tickets:* T10, T11

### 🟡 teilweise · Dialogs (a11y panel, M365Con popup) have roles, Escape and focus restore, but no focus trap and the popup interrupts

assets/a11y.js builds a role="dialog" panel with aria-label, trigger aria-expanded/aria-controls, moves focus in, closes on Escape and returns focus (a11y.js:19-33); assets/attend.js builds role="dialog" aria-modal="true" aria-labelledby, focuses the close button, handles Escape and restores focus (attend.js:27-37), with animations off under prefers-reduced-motion (sbar.css:48). Neither traps Tab or sets inert on the page, so aria-modal=true is not honoured for keyboard users. The popup fires after 120 s of inactivity and steals focus (attend.js:40-41) with no way to opt out beyond 7/30-day localStorage, and its strings/alt are en/de only. The cookie banner is a hidden role="region" that is revealed without focus or announcement (generate_site.py:271-277).

*Dateien:* `assets/a11y.js`, `assets/attend.js`, `assets/sbar.css`, `generate_site.py`  
*Tickets:* T10, T19

### 🟡 teilweise · Alt texts mostly present; cover SVG has contradictory role=img + aria-hidden, imported blog HTML unchecked

Flags get alt=native name (site_design.py:202-203), yt_thumb() takes an alt (generate_site.py:492-496), sidebar images have descriptive alt plus width/height (site_sidebar.py:52-53,83-84), site_members.img_tag() requires alt (site_members.py:92), brand icons are aria-hidden/focusable=false and share links have aria-label (generate_site.py:238,249-251), and all player/video iframes carry title (generate_site.py:1052,1054; site_podcast.py:42; site_video.py:42; site_live.py:104). Decorative images correctly use alt="" (site_shows.py:42, site_home.py:96, profile.js:25). Bugs: the generated episode cover SVG is emitted with role="img" aria-hidden="true" (generate_site.py:520), which is contradictory; Podpage/legacy blog HTML is imported verbatim with no alt check (site_legacy_blog.py:67-107, site_blog.py:98), so ~2300 migrated posts carry whatever Podpage had.

*Dateien:* `generate_site.py`, `site_design.py`, `site_sidebar.py`, `site_legacy_blog.py`, `site_blog.py`  
*Tickets:* T10, T14

### 🐞 Fehler · Duplicate navigation on show pages: header Show menu plus sidebar sb-nav card

English show pages render the header 'Show' dropdown (About the show, All episodes, Live, Guests, Hosts; generate_site.py:617) and, in the sidebar, a second menu <section class="sb-card sb-nav"><h2>M365.FM Show</h2><ul class="sb-navl"> with Home, Episodes, Blog, Guests, Hosts, Sponsors, Reviews, Work with me, About (site_podpage.py:194-195, comment: 'frueher zweite Menueleiste'). The two overlap in targets, the second is not a <nav> landmark, and its items (Sponsors, Reviews, Work with me) are reachable only there. The mobile .mm menu also duplicates .menu in the DOM (site_design.py:222-225), though CSS hides one at a time.

*Dateien:* `site_podpage.py`, `generate_site.py`, `site_design.py`  
*Tickets:* T10, T19

### 🟡 teilweise · Form labels in profile.js/community.js: mostly labelled, with a few unassociated labels, an aria-label override and non-ARIA tabs

profile.js has a lab() helper that creates <label for=id> and uses it for most fields (assets/profile.js:91, 45-49, 193, 207-208); checkboxes are wrapped in <label> (93), selects/file inputs get aria-label (19,26,160,187) and all forms have role=status aria-live messages (43,175,186,201,217). Issues: community.js:198 and :205 create <label> without for (inputs rely on aria-label); profile.js:188 gives the description textarea aria-label="desc", which overrides the visible label 'Short description…' because aria-label wins over <label for>; the 'kind' select has German aria-label 'Typ' in English UI (profile.js:187); the website field is placeholder-only ('https://'). The profile tab bar sets role=tablist/tab and aria-selected (profile.js:7-11) but has no aria-controls, no role=tabpanel and no arrow-key navigation.

*Dateien:* `assets/profile.js`, `assets/community.js`  
*Tickets:* T10

### 🟡 teilweise · ARIA: interactive list items in infographics have no role or state; progress bar invisible to AT

Good usage exists: aria-pressed toggles, role=status/aria-live, role=group, role="note" on the old-entity banner (site_entities.py:404), th scope=row in fact tables (site_entities.py:328, site_members.py:275,303) and quiz feedback role=status (generate_site.py:342). But .isteps and .iflow render <li tabindex="0"> with click plus Enter/Space handlers (generate_site.py:753,758,771-772) and no role="button", aria-pressed or aria-current, so the on/cur state exists only as CSS classes; the checklist .iprog bar shows 'n / total' through CSS content:attr(data-t) (site_design.py:167) with no role=progressbar or text node; #hub-sel is an aria-live region that contains buttons (site_home.py:119).

*Dateien:* `generate_site.py`, `site_design.py`, `site_home.py`, `site_entities.py`  
*Tickets:* T10

### ✅ in Ordnung · Accessibility settings panel, reduced-motion handling and statement page are implemented in all languages

A11Y_EARLY applies stored preferences (size, high contrast, dark, font, spacing, underline, no-motion) before first paint (generate_site.py:311-313) and a11y_tags() injects a11y.css + a11y.js on every page (generate_site.py:316-319, 434) with strings for all 15 languages (data/a11y_en.json, data/a11y_i18n.json). Lenis smooth scrolling is skipped under prefers-reduced-motion, coarse pointers and the a11y-nomo class (assets/smooth.js tail), and CSS animations are guarded by prefers-reduced-motion (site_design.py:142,151,162; sbar.css:48,68). An accessibility statement exists per language (data/a11y_statement_*.json, generate_site.py:625-650) and is linked from every footer (generate_site.py:663). Its claim d3 'keyboard operation for menus and language switch' is only partly true given the missing Escape/focus handling noted above.

*Dateien:* `generate_site.py`, `assets/a11y.js`, `assets/a11y.css`, `assets/smooth.js`, `data/a11y_statement_en.json`  
*Tickets:* T10

### 🟡 teilweise · M365Con bar is a sticky <div> inside <header> before the H1, not an aside after it

con_bar() returns <div class="mbar"><a …> (generate_site.py:575-578) which site_header() places as the first child of <header> (site_design.py:224), sticky at top:0 (site_design.py:95), so screen-reader and keyboard users hit the promo before the brand, menu and H1 on every page. The in-page banner m365con_band() is a labelled <section class="band" aria-label="M365Con 2027"> (generate_site.py:560-561) used on the home/language pages (1101,1135,1205). T7 asks for the banner as an <aside> after the H1; today it is neither an aside nor after the H1.

*Dateien:* `generate_site.py`, `site_design.py`  
*Tickets:* T7, T10, T19

**Gegenprüfung (alle Stichproben bestätigt):** All checked claims hold. Verified: skip link injection (generate_site.py:413-414) and single_main() (generate_site.py:360-380), SKIP_T for 15 languages (generate_site.py:300-302), Lenis onClick calls scrollTo without preventDefault (assets/smooth.js); .mm <details> outside <nav class="menu"> and .lsw summary without aria-label (site_design.py:206-213, 218-225); no Escape/outside-click handling for .lsw/.mg/.mm anywhere in assets/*.js or generate_site.py; assets/sbar.css has zero focus rules; community.css:52 .ed-b:focus-visible{outline:none}; cover SVG role="img" aria-hidden="true" (generate_site.py:520); cookie banner hidden role="region" (generate_site.py:271); episode crumbs are a plain div (generate_site.py:1047); sb-nav card with <h2> (site_podpage.py:195) and shell uses header("en","") (site_podpage.py:196); contrast ratios recomputed and match (5.37, 5.60, 6.21, 7.11, 7.53, 9.02, 16.57, tile hover 2.84). Minor nits only: in site_design.py the .skip/.sh{display:contents} rule is at line 91 (not 94) and .tile:hover at line 50 (not 49); the high-contrast token is at assets/a11y.css:10 (not 8); the tile hover issue is `.tile span{color:var(--mut)}` (generate_site.py CSS block), not a nested `.mut` class, and the only .tile markup is the language grid at generate_site.py:1108.

## Alte Podpage-URLs, Weiterleitungen, Titel-Vorlagen (T8, T7)

Build-Zeit-Karte /show/redirects.json (ca. 1.160 Einträge) wird vom Site-Worker als 301 ausgeliefert, dub.m365.fm und Apex gehen auf www. Lücken: /sponsor, /newsletter, /follow, /contact, /join, /legal, /p/... ohne Eintrag; /videos/<slug> (219 eingehende Links) fehlt; meta-refresh-Stubs statt 301 bei /show/blog. Titel: Marke doppelt angehängt, 774 von 1.119 englischen Folgentiteln mit Auslassung gekürzt, OG-Titel ungekürzt.

### 🟡 teilweise · Redirect engine: build-time map + Cloudflare site worker (301), active with MIGRATED=1

site_podpage.py:415-439 builds /show/redirects.json (old path -> new path) from Podpage episodes (flat /<slug>), pages (/<slug>), guests (/guests/<slug>), blog posts (/blog/<slug>), fixed list items and merged guest entities; sitewrk/index.js:14-30 fetches that JSON (cached 1 h) and answers 301 for any path not under /show or /shows, with a lowercase fallback and a /blog/* and /videos/* catch-all to /show/. sitewrk/wrangler.toml sets MIGRATED="1" and routes dub/www/apex, so this is live. GitHub Pages itself can only serve HTML, so every 301 depends on the worker; there is no data/redirects* file in the repo and data/podpage/redirects.json (Podpage's own redirect export) is an empty list, so Podpage-side custom redirects are not mirrored.

*Dateien:* `site_podpage.py`, `sitewrk/index.js`, `sitewrk/wrangler.toml`, `data/podpage/redirects.json`, `CLOUDFLARE.md`  
*Tickets:* T8

### 🟡 teilweise · dub.m365.fm / apex m365.fm -> www.m365.fm handled, but legacy paths produce a 2-hop chain

sitewrk/index.js:23 redirects any request on dub.m365.fm or m365.fm to https://www.m365.fm + same path with 301, then the map lookup only runs on the next request, so dub.m365.fm/<old-slug> hops twice (dub -> www/<old-slug> -> www/show/episodes/<slug>/). Resolving the map before the host redirect (or combining both into one Location) would give a single 301.

*Dateien:* `sitewrk/index.js`  
*Tickets:* T8

### ✅ in Ordnung · /guests/, /guests/<slug>, /reviews, /sponsors, /episodes, /hosts, /people, /podroll, /blog/<slug> are mapped

site_podpage.py:429-433 adds /episodes, /guests, /hosts, /people, /sponsors, /reviews, /podroll, /videos, /blog plus /guests/<slug> for all 174 Podpage guests, /<slug> for 1119 episodes, /<slug> for Podpage pages with content and /blog/<slug> for 2307 blog posts -> /community/u/mirko-p/blog/<slug>/ (targets built by site_legacy_blog.py). Targets exist under /show/... (pub() in site_podpage.py:200-204).

*Dateien:* `site_podpage.py`, `site_legacy_blog.py`  
*Tickets:* T8

### ❌ fehlt · /sponsor (singular), /newsletter, /follow, /contact, /join, /legal, /p/... have no redirect

The Podpage pages episodes/blog/reviews/.../newsletter/follow/legal/contact/join/voicemail are in SKIPP (site_podpage.py:402) and therefore neither rendered nor added to the map; only pages with page_content get a /<slug> entry. /sponsor (singular) and /p/... never appear anywhere in the code or map (grep for '/p/' finds nothing); /legal only works by accident because the platform builds its own /legal/ page (generate_site.py:1152). Podpage blog data links to /contact (6x), /follow (2x), /legal (2x) and /videos/<slug> (219x); /videos/* currently falls through to /show/ (sitewrk/index.js:27), losing the target. Suggested targets: /sponsor and /sponsors -> /show/sponsors/, /newsletter + /follow -> /show/listen/ (or the community), /contact + /join -> /show/work-with-me/ or /community/, /p/<slug> -> same as /<slug>, /blog/category/<x> and /blog/page/N -> /community/u/mirko-p/blog/.

*Dateien:* `site_podpage.py`, `sitewrk/index.js`, `data/podpage/pages.json`, `data/podpage/blog_posts.json.gz`  
*Tickets:* T8

### 🟡 teilweise · Flat episode slugs: mapped, but slugs colliding with platform top-level folders are silently dropped

site_podpage.py:417-423 computes a 'taken' set from whatever is in docs/ at build time plus a hard-coded list, and any flat /<slug> that matches is written to /show/redirect-conflicts.json instead of redirects.json (CLOUDFLARE.md documents /about as the known case). Because docs/ is built incrementally before site_podpage runs (generate_site.py:1230), the conflict list depends on build order and the dropped URLs get no 301 at all; a conflict should still redirect when the platform page is a different thing (e.g. /about -> /show/about/ is intentionally not done, but other collisions are not reviewed). Redirect keys are stored without trailing slash and the worker strips trailing slashes and preserves the query string (sitewrk/index.js:25-28), which matches Podpage's /<slug>/ form.

*Dateien:* `site_podpage.py`, `sitewrk/index.js`, `CLOUDFLARE.md`  
*Tickets:* T8

### 🐞 Fehler · /show/blog/... and retired pages use meta-refresh/noindex stubs instead of 301; /show/blog map entries are dead

site_podpage.py:376-381 writes <meta http-equiv=refresh> stubs for /show/blog/<slug>/ and /show/blog/, and site_podpage.py:434 also adds /show/blog/<slug> keys to redirects.json, but the worker never consults the map for paths starting with /show (sitewrk/index.js:26), so those entries are unused and the stubs answer 200 + meta refresh (no link equity, extra hop). Same pattern for /de/live/ (site_live.py:108) and the retired page about/mirko-peters/ (data/retired.json, generate_site.py:1210-1222: 'kein Auto-Redirect', noindex notice page). These should become worker 301s (lift the /show exclusion for an explicit key list) rather than meta refresh.

*Dateien:* `site_podpage.py`, `sitewrk/index.js`, `site_live.py`, `data/retired.json`, `generate_site.py`  
*Tickets:* T8, T12

### 🟡 teilweise · Merged-guest entity redirects exist; mirko-peters guest maps to itself, guest page still separate from Person entity

site_podpage.py:435-437 adds /entity/<old>(-guest) -> /entity/<new>/ for every language prefix from data/guest_merge.json, but the merge table maps 'mirko-peters' -> 'mirko-peters' (self), so /show/guests/mirko-peters/ is still published as its own ProfilePage (site_podpage.py:355-363) alongside /entity/mirko-peters/, and the legacy /guests/mirko-peters only 301s to that guest page, not to the canonical Person URL. The worker additionally rewrites /community/u/mirko-peters -> /community/u/mirko-p (sitewrk/index.js:31).

*Dateien:* `site_podpage.py`, `data/guest_merge.json`, `sitewrk/index.js`  
*Tickets:* T8, T12

### 🟡 teilweise · Worker fetches the redirect map on every non-/show request and has no noindex/robots guard for redirect sources

sitewrk/index.js:14-17 performs a subrequest to /show/redirects.json (cacheTtl 3600) for every path that is not /, /show* or /shows*, including /assets/*, /de/*, /community/* and /entity/*; the ~1,160-entry JSON is parsed per request. A cheaper design would check the map only for first-segment paths that are not known platform roots, or bake the map into the worker bundle at deploy time (sitewrk.yml). No ticket-blocking bug, but a hot-path cost on every page view.

*Dateien:* `sitewrk/index.js`  
*Tickets:* T8, T9

### 🐞 Fehler · Episode <title>: brand appended twice, 774 of 1,119 English episode titles truncated with an ellipsis

site_podpage.py:203 pub() always passes title as f"{title} – {NAME}" (NAME = 'M365 FM Podcast' from data/podpage/podcast.json), and page() (generate_site.py:419) then runs seo_title() (generate_site.py:214-220) for og_type='article', which cuts the string to 52 chars and appends ' | M365.FM'. Simulated on the real data: 774 titles end in '…', 494 contain the brand twice or a cut brand (e.g. 'Single Sign-On (SSO) Simply Explained – M365 FM… | M365.FM', 'Group Policy - Simply Explained – M365 FM Podcast | M365.FM'). Fix: pass the bare episode title into page() for article pages and let seo_title add exactly one suffix. The same double-suffix pattern applies to community posts: site_blog.py:127 (f'{title} – {author} | M365.FM'), site_feed.py:59, site_library.py:70, site_podcast.py:55 where seo_title then cuts '... – Mirko Pe… | M365.FM'.

*Dateien:* `site_podpage.py`, `generate_site.py`, `site_blog.py`, `site_feed.py`, `site_library.py`, `site_podcast.py`  
*Tickets:* T7

### ❌ fehlt · No title template/length control for non-article pages (website/profile/video.other)

page() applies seo_title only when og_type == 'article' (generate_site.py:419); every website/profile page uses the raw title, so e.g. the root home title 'M365.FM – Microsoft community: blog, podcast, events & explainers | Mirko Peters' is 80 chars (generate_site.py:1137), member/company pages use f'{name} – {headline} | M365.FM' with unbounded headlines (site_members.py:289,309), events f'{title} – {events} | M365.FM' (site_events.py:209), Podpage guest pages render as 'Name – guest – M365 FM Podcast' (site_podpage.py:364 + pub). Three different brand spellings coexist: ' | M365.FM', ' – M365.FM', ' – M365 FM Podcast', and ' – M365.FM Deutsch' style (generate_site.py:1377, site_learn.py:324). A single title_for(kind, parts) helper with 50-60 char budget and one suffix is missing; the editor rule in worker/src/seo.js:119-121 (ideal 30-65) is not applied at build time.

*Dateien:* `generate_site.py`, `site_members.py`, `site_events.py`, `site_podpage.py`, `site_learn.py`, `worker/src/seo.js`  
*Tickets:* T7

### 🟡 teilweise · Meta descriptions: partly bounded to 155, but Podpage pages allow 300 chars and 486 episode meta_descriptions exceed 155

Many builders cut descriptions with [:155] or short(…,155) (site_blog.py:127, site_members.py:289, generate_site.py:175-177 short()), and episode pages use e['meta_description'] or short_desc(e, nrec, 155) (site_podpage.py:314). But pub() stores desc[:300] (site_podpage.py:203) and site_shows.py:22 likewise, so hub/guest/page descriptions run up to 300 chars (hub uses the full plain(pod description), guests use the full bio); the Podpage meta_description field itself is >155 chars for 486 of 1,119 episodes (27 empty) and is used unchanged, and the root home description is 186 chars (generate_site.py:1138). Podpage pages fall back to plain(c)[:200] (site_podpage.py:409). A central 140-155 clamp with word boundary (reuse short()) in page() would fix all of them.

*Dateien:* `site_podpage.py`, `site_shows.py`, `generate_site.py`, `data/podpage/episodes.json.gz`  
*Tickets:* T7

### 🟡 teilweise · M365Con promo: sticky top bar on every page plus a hard-coded English <section class="band"> below the fold; not an <aside> after the H1

Two placements exist: con_bar() (generate_site.py:575-578) renders the sticky .mbar above the header on every page via header() (generate_site.py:622, CSS in site_design.py:91-92, translated per language, auto-expires after 2027-01-22), and m365con_band() (generate_site.py:560-563) renders an English-only <section class="band" aria-label="M365Con 2027"> between the first <main> and the FAQ/author block on the language homes (generate_site.py:1101), the root home (1135) and the about page (1205); single_main() (generate_site.py:360) then turns the trailing <main> into a <section>. Episode and show pages get no band. Ticket T7 wants the banner as an <aside> directly after the H1: today it is a <section> far below the hero, untranslated, with its own H2 that competes with the page's content headings, and it has no end-date guard like con_bar.

*Dateien:* `generate_site.py`, `site_design.py`  
*Tickets:* T7, T19

### 🟡 teilweise · OG/Twitter titles use the raw (double-branded) title while <title> is rewritten

page() writes og:title, og:image:alt and twitter:title from the unmodified title argument (generate_site.py:423-426) while <title> goes through seo_title(); for episodes that means og:title = 'FinOps for Manufacturing IT: Controlling Cloud Costs – M365 FM Podcast' and <title> = 'FinOps for Manufacturing IT | M365.FM'. The OG image generator also receives strip_tags(title) incl. the ' – M365 FM Podcast' suffix (generate_site.py:406). A shared title template would keep both in sync (og:title without brand, <title> with one brand).

*Dateien:* `generate_site.py`  
*Tickets:* T7

**Gegenprüfung (alle Stichproben bestätigt):** Spot-checked 5 findings; all claims verified against the source. (1) Worker redirect engine: sitewrk/index.js:14-17 fetches /show/redirects.json (cacheTtl 3600), :23-24 host redirect dub/apex -> www (2-hop chain confirmed), :25-29 map lookup skipped for /show*/ /shows*, /blog|/videos catch-all to /show/; wrangler.toml sets MIGRATED="1"; data/podpage/redirects.json is []. (2) Episode double brand: site_podpage.py:203 pub() passes f"{title} – {NAME}" (NAME from pod name, :193) and generate_site.py:419 applies seo_title (:214-220, cut at 52 chars, appends " | M365.FM") only for og_type=="article"; og:title/twitter:title use raw title (:423-426). (3) Descriptions: desc[:300] at site_podpage.py:203 and site_shows.py:22; episode meta_description used unchanged at :314; pages fallback plain(c)[:200] at :409; root home title is 80 chars and description 186 chars (generate_site.py:1137-1138). (4) M365Con: m365con_band() generate_site.py:560-563 is an untranslated <section class="band"> placed at :1101, :1135, :1205 between two <main>s (single_main :360 converts trailing main to section), no end-date guard; con_bar :575-578 with M365CON_END, injected via header() :622, CSS site_design.py:91-92. (5) Guest merge / stubs: data/guest_merge.json maps "mirko-peters" -> "mirko-peters"; site_podpage.py:435-437 adds /entity/<old> redirects per language; guest pages still published :355-364; /show/blog meta-refresh stubs :377-382 and dead /show/blog keys :434; site_live.py:108 de/live stub; retired pages generate_site.py:1209-1222 noindex notice. Only trivial line offsets: worker mirko-peters rewrite is index.js:32 (not 31), SKIPP is site_podpage.py:401 (not 402).

## Tickets T0–T20: Stand, Befunde und Dateipfade

| Ticket | Inhalt | Stand (1.11.) | Dateien laut Befunden |
|---|---|---|---|
| T0 | Technik-Audit (dieses Dokument) | erledigt (1.11., PR dieses Audits) | – |
| T1 | Sitemap-Index je Sprache und Typ mit lastmod, robots, GSC | offen – Sitemap-Index je Sprache vorhanden, nicht je Typ; lastmod für Hubs = Baudatum; Validierung fehlt | `.github/workflows/site.yml`, `check_links.py`, `check_schema.py`, `data/blog_tr.json`, `generate_site.py`, `site_blog.py`, `site_entities.py`, `site_events.py`, `site_feed.py`, `site_learn.py`, `site_legacy_blog.py`, `site_library.py`, `site_live.py`, `site_members.py` … |
| T2 | Englisch-Einstieg: / englische Startseite, /en/…, /show/ per 301 | offen – kein /en/-Baum; Entscheidung von Mirko liegt vor | `ROADMAP.md`, `generate_site.py`, `generate_site.py:1137-1139`, `generate_site.py:529-541`, `generate_site.py:551-552`, `site_blog.py`, `site_i18n.py`, `site_podpage.py`, `site_podpage.py:299`, `site_podpage.py:418-419`, `sitewrk/index.js` |
| T3 | hreflang + x-default überall, Sprachwechsel auf Seitenebene | teilweise – page() gibt hreflang aus, Dub-Folgen ohne en-Alternate, zwei Cluster je Video, Sitemap ohne x-default | `assets/attend.js`, `assets/community.css`, `assets/sbar.css`, `data/blog_tr.json`, `generate_site.py`, `site_blog.py`, `site_design.py`, `site_entities.py`, `site_events.py`, `site_learn.py`, `site_legacy_blog.py`, `site_library.py`, `site_live.py`, `site_members.py` … |
| T4 | JSON-LD je Seitentyp | teilweise – alle Seitentypen mit JSON-LD; Person-@id vierfach, Dub-transcript als URL, Person.review ungültig, Updates ohne Schema | `.github/workflows/site.yml`, `.github/workflows/site.yml:157`, `check_links.py`, `check_schema.py`, `check_schema.py:9-19`, `check_schema.py:92-94`, `data/m365con_program_2026.json`, `generate_site.py`, `generate_site.py:1014-1031`, `generate_site.py:1080-1088`, `generate_site.py:1137-1139`, `generate_site.py:1140-1147`, `generate_site.py:1184`, `generate_site.py:457-489` … |
| T5 | Encoding-Fix UTF-8, Mojibake-Check im Build | offen – 5 Mojibake-Stellen (en_titles.json, live.json), ~25 U+FFFD in Übersetzungen, kein Build-Check | `.github/workflows/site.yml`, `adfree_cue.py`, `adfree_test.py`, `data/blog_i18n/nl/0f.json.gz`, `data/blog_i18n/ru/0b.json.gz`, `data/blog_i18n/uk/05.json.gz`, `data/en_titles.json`, `data/live.json`, `data/podpage_i18n/he.json`, `data/podpage_i18n/ja.json`, `data/podpage_i18n/notes_uk.json`, `fetch_en_titles.py`, `fetch_reviews.py`, `generate_site.py` … |
| T6 | Feed bereinigen, Paginierung, Startseite < 300 kB | teilweise – GitHub-Aktivität im Feed, keine Kartenobergrenze auf Startseite/Blog, Dedup verliert /de/-Fassungen | `.github/workflows/site.yml`, `data/blog_i18n`, `data/blog_tr.json`, `episodes/0CI-mzhWEWE.json`, `generate_site.py`, `generate_site.py:1052-1065`, `generate_site.py:1100`, `generate_site.py:1133`, `site_blog.py`, `site_cover.py:74-117`, `site_entities.py`, `site_feed.py`, `site_fetch.py`, `site_home.py` … |
| T7 | Title/Description-Vorlagen, M365Con-Banner als aside | offen – Marke doppelt, 774 gekürzte Folgentitel, OG-Titel ungekürzt, Band hart kodiert | `assets/attend.js`, `data/podpage/episodes.json.gz`, `generate_site.py`, `site_blog.py`, `site_design.py`, `site_events.py`, `site_feed.py`, `site_learn.py`, `site_library.py`, `site_members.py`, `site_podcast.py`, `site_podpage.py`, `site_shows.py`, `site_sidebar.py` … |
| T8 | Legacy-Podpage-URLs 301-Karte, dub → www | teilweise – 301-Karte über Site-Worker aktiv; /sponsor, /newsletter, /follow, /contact, /join, /legal, /p/, /videos/<slug> fehlen; 2-Hop-Kette ab dub.m365.fm | `.github/workflows/site.yml`, `CLAUDE.md`, `CLOUDFLARE.md`, `check_links.py`, `check_schema.py`, `config.json`, `data/guest_merge.json`, `data/podpage/blog_posts.json.gz`, `data/podpage/episodes.json.gz`, `data/podpage/pages.json`, `data/podpage/redirects.json`, `data/retired.json`, `generate_site.py`, `site_events.py` … |
| T9 | Core Web Vitals | teilweise – Fonts/CSS/Caching gut (CLS 0,02 nach Paket CLS); Startseite, Lenis, YouTube-iframe, Bilder-Pipeline offen; PR 71 bündelt Inline-JS und verzögert ui-<lang>.js | `.github/workflows/site.yml`, `.github/workflows/site.yml:191`, `CLAUDE.md`, `CLOUDFLARE.md`, `CLOUDFLARE.md:34`, `CLOUDFLARE.md:8`, `assets/a11y.css`, `assets/attending-m365con.webp`, `assets/community.css`, `assets/community.js`, `assets/community.js:16`, `assets/community.js:250`, `assets/community.js:28`, `assets/editor.js` … |
| T10 | Accessibility | teilweise – Skip-Link, lang/dir, Panel in 15 Sprachen; :focus-visible, Fokus-Fallen, Doppel-Navigation, Filter-Ansagen offen | `assets/a11y.css`, `assets/a11y.js`, `assets/attend.js`, `assets/community.css`, `assets/community.js`, `assets/pfpub.js`, `assets/profile.js`, `assets/sbar.css`, `assets/smooth.js`, `data/a11y_statement_en.json`, `generate_site.py`, `generate_site.py:436`, `site_ads.py`, `site_blog.py` … |
| T11 | Zähler aus derselben Datenquelle | teilweise – Folgen-/Sprachzähler aus denselben Quellen; „120 Sessions“ dreifach hart kodiert; Community-Zähler fallen ohne API auf 0 | `.github/workflows/site.yml`, `assets/pfpub.js`, `data/blog_tr.json`, `data/m365con_program_2026.json`, `generate_site.py`, `site_entities.py`, `site_events.py`, `site_fetch.py`, `site_home.py`, `site_learn.py`, `site_legacy_blog.py`, `site_members.py`, `site_podpage.py`, `worker/src/autotr.js` … |
| T12 | Personen-Entity Mirko Peters konsolidieren | teilweise – Host verlinkt auf /entity/mirko-peters/ (Paket 7); Gastseite, Profil mirko-p und Folgen-Slug /mirko-peters/ noch getrennt | `check_schema.py:92-94`, `data/guest_entities.json`, `data/guest_merge.json`, `data/podpage/episodes.json.gz`, `data/retired.json`, `generate_site.py`, `generate_site.py:1184`, `generate_site.py:457-489`, `site_blog.py:33-36`, `site_entities.py`, `site_entities.py:62`, `site_fetch.py`, `site_learn.py`, `site_live.py` … |
| T13 | Episoden ↔ Entitäten, sameAs | teilweise – content_topic in D1 (Paket 13), Entitätsseiten zeigen Folgen und Artikel (Pakete 1/2/8), 45 Wikidata-IDs; Dub-Folgen nur einseitig zugeordnet, 100 % sameAs offen | `data/guest_entities.json`, `data/guest_merge.json`, `data/retired.json`, `generate_site.py`, `generate_site.py:1014-1031`, `generate_site.py:965-989`, `site_blog.py`, `site_entities.py`, `site_entities.py:458-471`, `site_entities.py:55-170`, `site_fetch.py`, `site_learn.py`, `site_members.py`, `site_podpage.py` … |
| T14 | Podpage-Migration abschließen | teilweise – Blog-Import nach D1 läuft (legacyblog.js), R2-Bilder-Workflow und Autorenbox vorhanden; blog-import/ (104 MB) bleibt im Deploy, Artikel-zu-Artikel-Links offen, Prüfbericht offen | `.github/workflows/site.yml`, `CLOUDFLARE.md:34`, `assets/attending-m365con.webp`, `assets/mirko-peters-800.jpg`, `assets/og-default.png`, `data/blog_i18n`, `data/blog_import.json`, `data/blog_tr.json`, `data/r2_map.json`, `generate_og.py`, `generate_og.py:86-92`, `generate_site.py`, `generate_site.py:1188`, `generate_site.py:492-495` … |
| T15 | Import-Pfad imports/blog/<lang>/*.md → D1 | offen – kein Import-Pfad für imports/blog/; Entitäten-Import aus imports/entities/ kommt mit PR 74 | `.github/workflows/articles.yml`, `.github/workflows/ms-updates.yml`, `.github/workflows/r2-images.yml`, `.github/workflows/site.yml`, `.github/workflows/translate-blog.yml`, `data/blog_i18n`, `data/blog_import.json`, `generate_site.py`, `site_fetch.py`, `site_learn.py`, `site_legacy_blog.py`, `site_members.py`, `translate_blog.py` |
| T16 | llms.txt erweitern | erledigt (Paket 9: llms-show/entities/blog.txt, agent.json) – per-Sprache-Dateien fehlen noch | `generate_site.py`, `site_blog.py`, `site_entities.py`, `site_podpage.py`, `sitewrk/index.js` |
| T17 | Übersetzungs-Pipeline Blog | teilweise – translate-blog.yml mit Haiku-Vormerkliste (Paket 11), Budget ab Dezember; Namen/Produkte-Schutz prüfen | `.github/workflows/articles.yml`, `.github/workflows/ms-updates.yml`, `.github/workflows/r2-images.yml`, `.github/workflows/site.yml`, `.github/workflows/translate-blog.yml`, `data/blog_i18n`, `data/blog_i18n/nl/0f.json.gz`, `data/blog_i18n/ru/0b.json.gz`, `data/blog_i18n/uk/05.json.gz`, `data/blog_tr.json`, `data/podpage_i18n/he.json`, `data/podpage_i18n/ja.json`, `data/podpage_i18n/notes_uk.json`, `generate_site.py` … |
| T18 | Episoden-Enrichment-Vorlage | teilweise – Kernpunkte/FAQ je Folge (data/episode_sections), Vollfassungen aus Shownotes mit PR 74 | `generate_site.py:1052-1054`, `generate_site.py:492-495`, `generate_site.py:728`, `site_notes.py:66`, `site_podpage.py:200-203`, `site_podpage.py:298-315` |
| T19 | Show-Sidebar je Sprache, Popup, Design | teilweise – M365Con-Popup nach 2 Minuten (attend.js) in 15 Sprachen, Sidebar nur auf Dub-Seiten, Band/Popup teils Englisch, Logo-Konsolidierung offen | `TODO.md`, `assets/a11y.css`, `assets/a11y.js`, `assets/attend.js`, `assets/community.css`, `assets/profile.js`, `assets/sbar.css`, `data/m365con_program_2026.json`, `generate_site.py`, `generate_site.py:319`, `generate_site.py:383`, `generate_site.py:410`, `generate_site.py:429`, `generate_site.py:446-453` … |
| T20 | Updates-Seite mit Wichtigkeit und Clustern | teilweise – ms-updates.yml liefert Produkt-Updates (product_updates.json); Wichtigkeit und Cluster offen, Seite ohne JSON-LD | `.github/workflows/articles.yml`, `.github/workflows/ms-updates.yml`, `.github/workflows/r2-images.yml`, `.github/workflows/site.yml`, `.github/workflows/translate-blog.yml`, `generate_site.py:1140-1147`, `site_updates.py:69-89` |

## Offene Entscheidungen für Mirko aus dem Audit

1. Bot-Commits sollen den Seitenbau auslösen: dafür braucht es ein GitHub-App-Token oder einen PAT als Secret (Vorschlag: feingranularer PAT nur für contents:write auf dieses Repo) oder ein explizites `gh workflow run site.yml` am Ende der Daten-Workflows.
2. `data/blog_import.json` auf `enabled: false` setzen, sobald der D1-Import alle Beiträge hat (spart 104 MB je Deploy).
3. Lenis-Scroll bleibt laut Vorgabe; die rAF-Schleife wird dann nur bei Bewegung aktiv gehalten (Teil von T9).

