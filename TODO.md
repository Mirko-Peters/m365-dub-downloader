# TODO (später)

## Spotify-Folgenlinks per API (ab 1. Dezember 2026)
Spotify erlaubt Entwickler-Apps nur mit Premium-Konto. Bis dahin läuft der Abgleich ohne Spotify-API weiter
(Apple, Deezer, YouTube, Podpage-Sicherung und die gesammelten Spotify-Links aus `data/spotify_links.json`).

Wenn Premium da ist:
1. Auf https://developer.spotify.com/dashboard eine App anlegen (Client Credentials reichen).
2. In GitHub unter Settings → Secrets → Actions `SPOTIFY_CLIENT_ID` und `SPOTIFY_CLIENT_SECRET` eintragen.
3. Den Workflow "Site" einmal manuell starten: `sync_platforms.py` nutzt die Secrets automatisch (bisher 375 von 1000 englischen Folgen verlinkt).

## Weitere offene Punkte
- Gäste zusammenführen: `data/guest_match_report.json` (Dieter Kempeneers doppelt, Jean-Sébastien Duchêne, Mirko Peters).
- Plattform-Abgleich dauert in CI ca. 21 Minuten (Apple-Einzelsuchen); bei Bedarf kürzen.
- Sprach-Shows haben noch keine `apple_id` / `youtube_sources` in `data/platforms.json`.
