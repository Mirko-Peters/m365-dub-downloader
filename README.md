# M365 Dub Downloader

Läuft täglich per GitHub Actions: prüft den YouTube-Kanal **@m365show** auf Dub-Tonspuren
(alle Sprachen außer der Originalsprache, inklusive Deutsch), lädt jede neue Spur als MP3,
lädt sie als **private** Episode in die passende M365.FM-Sprach-Show auf Spreaker hoch und löscht die Datei wieder.
Was erledigt ist, steht in `state.json`.

## Einmalig einrichten
Repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Inhalt |
|---|---|
| `SPREAKER_TOKEN` | Spreaker → Developers → deine App → *Generate access token* → Copy |
| `YT_COOKIES` *(optional, falls YouTube blockt)* | Inhalt einer `cookies.txt` (Netscape-Format) von youtube.com, z. B. mit der Browser-Erweiterung „Get cookies.txt LOCALLY“ |

## Starten
**Actions → YouTube-Dubs zu Spreaker → Run workflow**. Für einen ersten Test `limit` = 5 und `dry_run` anhaken.
Danach läuft es automatisch jede Nacht um 03:17.

## Einstellungen (`config.json`)
- `show_map`: Sprache → Spreaker-Show-ID
- `max_downloads_per_run`: wie viele neue Dubs pro Lauf (Standard 40)
- `create_missing_shows`: `true` legt Shows für Sprachen ohne Show an, mit SEO-Texten aus `shows_seo.json`
- `upload_visibility`: `PRIVATE` (Standard) oder `PUBLIC`
