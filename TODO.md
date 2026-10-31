# TODO (später)

## Spotify-Folgenlinks per API (ab 1. Dezember 2026)
Spotify erlaubt Entwickler-Apps nur mit Premium-Konto. Bis dahin läuft der Abgleich ohne Spotify-API weiter
(Apple, Deezer, YouTube, Podpage-Sicherung und die gesammelten Spotify-Links aus `data/spotify_links.json`).

Wenn Premium da ist:
1. Auf https://developer.spotify.com/dashboard eine App anlegen (Client Credentials reichen).
2. In GitHub unter Settings → Secrets → Actions `SPOTIFY_CLIENT_ID` und `SPOTIFY_CLIENT_SECRET` eintragen.
3. Den Workflow "Site" einmal manuell starten: `sync_platforms.py` nutzt die Secrets automatisch (bisher 375 von 1000 englischen Folgen verlinkt).

## Apple Podcasts und YouTube für die Show (Dezember 2026)
`@m365-show` ist der Hauptkanal auf YouTube; der Podcast läuft dort als Playlist/Feed. Der Podcast ist bei Apple Podcasts und YouTube noch nicht angelegt beziehungsweise nicht verifiziert. Im Dezember nachziehen:
1. Apple Podcasts Connect: Show einreichen/verifizieren (die ID `1810175174` in `data/platforms.json` prüfen, ob sie zur eigenen, verifizierten Show gehört).
2. YouTube: Podcast-Playlist (`PLNdQ7ciTZo2k` in `data/platforms.json`, `youtube_sources`) als Podcast einreichen und prüfen, ob die ID stimmt.
3. Danach `sync_platforms.py` einmal manuell laufen lassen (Workflow „Site“ starten), damit Folgenlinks zugeordnet werden.

## Weitere offene Punkte
- Gäste zusammenführen: `data/guest_match_report.json` (Dieter Kempeneers doppelt, Jean-Sébastien Duchêne, Mirko Peters).
- Plattform-Abgleich dauert in CI ca. 21 Minuten (Apple-Einzelsuchen); bei Bedarf kürzen.
- Sprach-Shows haben noch keine `apple_id` / `youtube_sources` in `data/platforms.json`.

## OAuth 2.1 für den MCP-Server und Agent-Erkennung (beschlossen, nach dem Datenbank-Umzug)
Ziel: MCP-Clients (Claude, ChatGPT, Cursor) verbinden sich mit einem Klick, statt dass ein Mitglied einen `m365_…`-Token kopiert. Gleichzeitig bestehen dann die Prüfungen auf isitagentready.com, die heute bewusst auf "fail" stehen (keine erfundenen Metadaten).
1. Worker: `/authorize` (Anmeldung über die bestehende Sitzung plus Einwilligungsseite), `/token` (Authorization Code mit PKCE, Refresh), Schlüssel (`/jwks.json`) und Registrierung von Clients (RFC 7591). Tokens in D1, wie die bisherigen KI-Tokens widerrufbar im Profil.
2. `/.well-known/oauth-authorization-server` (RFC 8414) mit `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`, `grant_types_supported`, `response_types_supported`; optional `/.well-known/openid-configuration`.
3. `/.well-known/oauth-protected-resource` (RFC 9728) mit `resource`, `authorization_servers`, `scopes_supported`, `bearer_methods_supported: ["header"]`; der MCP-Server antwortet bei 401 mit `WWW-Authenticate: Bearer resource_metadata="…"`.
4. `auth.md` um `agent_auth` ergänzen. Der alte Weg über persönliche Tokens bleibt bestehen.
5. Erst auf einer Testumgebung bauen und prüfen (Sicherheit und Anmeldung betroffen), danach mit Freigabe live schalten.

## Gemeldet am 31.10.2026 (Mirko)
- **Bug, englische Seiten:** In der Sidebar-Karte „M365.FM Show“ (Home, Episodes, Blog, Guests, Hosts, Sponsors, Reviews, Work with me, About) stimmt etwas nicht – prüfen: Links (Blog zeigt noch auf /show/blog/, das nur noch weiterleitet), Reihenfolge und ob die Karte auf allen englischen Seiten erscheinen soll.
- **Live Show als Events (nur Englisch):** Der Menüpunkt „M365 Show Live“ bleibt auf den englischen Seiten. Die gelaufenen und die kommenden Streams (auch die der M365Con) werden als Events im Community-System geführt (ein Event je Stream, Vergangenes als vergangenes Event), „Live“ wird ein Untermenüpunkt (z. B. unter Show), und zu jedem Stream entsteht ein Beitrag (Feed/Blog) – Quelle data/live.json (sync_live.py, heute 113 Streams). Umsetzung als eigenes Paket nach Paket 12: Import-Cron im Worker (Event je Stream, idempotent über die YouTube-ID), Seitenbau liest die Events, Menü anpassen.
## Datenmodell Übersetzungen (Mirko, 31.10.): keine Dopplung je Sprache
Ein Inhalt existiert genau einmal (Entität, Folge, Beitrag) in seiner Originalsprache; jede Sprachfassung ist ein Eintrag „ist Übersetzung von“ mit nur den übersetzten Feldern:
`translation(kind, item_id, lang, field, text, src, quality, created)` – kind = entity | episode | blog | notes, field = title | summary | body | desc | long | keypoints | faq. Seiten entstehen aus Original plus Überlagerung der Sprachfassung; fehlt ein Feld, bleibt das Original sichtbar und markiert. Das ersetzt `item_tr`, `ent_tr`, `data/blog_i18n`, `data/podpage_i18n` (Paket 17) und spart die Mehrfachspeicherung ganzer Datensätze je Sprache. Ausspielung aus der Datenbank bzw. als fertige Seite im R2-Bucket, GitHub Pages trägt nur Englisch/Deutsch.

## Expertise-Stufen (Paket 22, 1.11.2026)
- Belege kommen aus Blog, Sessions, Podcast, Video, Bibliothek, Wiki, Entitäten, geprüften Zertifikaten, Antworten und Bestätigungen (`worker/src/levels.js`). Noch nicht als Beleg: Gastauftritte in der Hauptshow (Folgen-Register aus Paket 16/17, `episode_guest` ↔ beanspruchte Personen-Entität) – nach dem Merge von PR 69 als Beleg-Art `show` (Gewicht 4) ergänzen.
- Firmenprofile tragen ihre Themen weiterhin selbst ein; bei Bedarf aus den Belegen der Team-Mitglieder ableiten.
- Seitengröße (Messung 1.11.): je Seite stecken im Schnitt 4–6 KB Inline-CSS (`<style>` der Lern-/Wiki-/Mitglieder-Blöcke) und 4 KB Menü; Inline-CSS ins gehashte Stylesheet verschieben spart rund 150 MB über alle Seiten.
