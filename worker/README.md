# Community-API (Cloudflare Worker + D1)

Login (Google/Microsoft), Kommentare, Abzeichen, Kurator pro Land, Web-Push und E-Mail-Digest für dub.m365.fm.
Läuft unter `https://api-dub.m365.fm`. Schlüssel (Session, VAPID, Cron) erzeugt der Workflow selbst.

## Einmalig einrichten (alles als GitHub-Secrets im Repo)
1. **Cloudflare**: Die Domain m365.fm muss im selben Cloudflare-Konto liegen. API-Token erstellen (Profil → API-Tokens → Vorlage „Edit Cloudflare Workers“, zusätzlich Rechte *D1: Edit* und *Zone → DNS: Edit* für m365.fm). Secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` (Account-ID steht rechts im Dashboard).
2. **Google-Login**: console.cloud.google.com → APIs & Dienste → Anmeldedaten → OAuth-Client-ID (Webanwendung). Autorisierte Weiterleitungs-URI: `https://api-dub.m365.fm/auth/callback/google`. Secrets: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
3. **Microsoft-Login**: entra.microsoft.com → App-Registrierungen → Neu; Kontotypen „Konten in allen Organisationsverzeichnissen und persönliche Microsoft-Konten“; Web-Redirect-URI `https://api-dub.m365.fm/auth/callback/microsoft`; unter Zertifikate & Geheimnisse ein Client-Geheimnis (Wert!). Secrets: `MS_CLIENT_ID` (Anwendungs-ID), `MS_CLIENT_SECRET`.
4. **E-Mail (Resend)**: resend.com → Domain `dub.m365.fm` (oder m365.fm) verifizieren (DNS-Einträge) → API-Key. Secret: `RESEND_API_KEY`. Absender steht in `wrangler.toml` (`MAIL_FROM`).
5. Optional `ADMIN_SUBS` = `google:<sub>` oder `microsoft:<sub>` (Moderator; die ID siehst du in D1 in der Tabelle users).
6. Workflow **„Community-API … einrichten“** starten (Actions → Run workflow). Er legt die D1-Datenbank `m365-dub` an, wendet `schema.sql` an, setzt Secrets, veröffentlicht den Worker.

Ohne Zugangsdaten tut der Workflow nichts; die Website blendet die Community-Bereiche automatisch aus, solange die API nicht erreichbar ist.

## Betrieb
- Täglicher Digest: Cron `0 6 * * *` (UTC). Der erste Lauf markiert vorhandene Folgen nur als bekannt (kein Massenversand).
- Manuell testen: `https://api-dub.m365.fm/api/admin/run-daily?key=<CRON_KEY>&dry=1` (CRON_KEY in Cloudflare → Worker → Settings → Variables; `dry=1` sendet nichts).
- Worker Free: 50 Subrequests pro Aufruf → bei vielen Abonnenten Workers Paid ($5/Monat) nutzen.
- Lokal: `cd worker && npm i && npx wrangler dev` (mit `.dev.vars`: `SESSION_SECRET`, `DEV_LOGIN=1`).

## Community-Wiki und Editoren
- Auf den Glossar-Begriffsseiten (de/en) gibt es unter der Kurzinfo ein Community-Wiki (Tabelle `wiki_rev`). Beitraege sind reiner Text (keine Links), je Nutzer ein offener Vorschlag, Limit 6/Stunde.
- Neue Mitglieder: Beitrag wartet auf Pruefung. Sofort live: Admin, Editoren und Mitglieder ab 25 Punkten. 3 Meldungen blenden eine Fassung aus (die vorherige kommt zurueck).
- Editor ernennen: auf der Community-Seite (als Admin angemeldet) im Bereich **Team** nach dem Namen suchen und „Zum Editor machen“. Editoren pruefen Beitraege direkt unter dem jeweiligen Begriff; sie erhalten das Abzeichen ✏️ Editor. Wer einen veroeffentlichten Beitrag hat, bekommt 📖 Wiki-Autor.
- Freigegebene Texte exportiert `GET /api/wiki/export?lang=de`; der Seitenbau uebernimmt sie statisch (indexierbar).
