# Roadmap Community-Plattform (dub.m365.fm)

Stand: 2026-10-29. Reihenfolge nach Absprache mit Mirko; alles mit Schema.org-Verknüpfung zu den Entitäten (`data/entities.json`).

## Fertig
- Glossar A–Z, Lernpfade, Trainer, Presskit
- Community-API (Cloudflare Worker, D1): Login Google/Microsoft, Kommentare, Abzeichen, Wiki, Editor-Rolle
- Wiki mit Formatierung, Quellen/Fußnoten, `[[Begriff]]`-Links, Verlauf mit Änderungen, Wiederherstellen
- Entitätsdatenbank (89 Einträge, Beziehungen, JSON-LD, `/entities.json`, `/entities.jsonld`), neue Themen anlegen
- Experten-Profile (Programme MVP/MCT/RD/Student Ambassador/Mitarbeiter/Partner, Themen mit Level, Zertifizierungen, Kanäle mit Feeds, Bestätigungen), Firmen-Konten mit Team, Mitgliederverzeichnis, Feed mit Upvotes

## Als Nächstes (Ideen von Mirko)
1. **Events und Veranstalter**: Veranstalter-Konten (Firma/Person), Events (online/vor Ort/hybrid, Datum, Ort, Ticket-Link), Sessions je Event, Speaker mit Sessions verknüpft. Schema.org: `Event` + `subEvent` (Sessions) + `performer`/`organizer` + `location`/`VirtualLocation`.
2. **Speaker-Profil**: Speaker hinterlegt seine Sessions (Titel, Abstract, Thema/Entität, Level, Sprache, Video/Folien-Link), Verfügbarkeit, Referenzen. Schema.org: `Person` + `performerIn`, Sessions als `Event`/`PresentationDigitalDocument`.
3. **Copilot-Bibliothek**: Prompts, Skills, Plugins, Agenten-Anweisungen, Declarative-Agent-Manifeste, Copilot-Studio-Themen, Power-Automate-Flows, Power-Apps-Vorlagen, KQL-Abfragen, DAX-Maße, Excel-Formeln, Graph-Abfragen, PowerShell-Skripte, Adaptive Cards, Custom Instructions. Mit Upvotes, Kommentaren, Teilen, Versionen, Entitäts-Zuordnung. Schema.org: `CreativeWork`/`SoftwareSourceCode`/`HowTo`.
4. Weitere Ideen: Usergroups/Meetups (wiederkehrende Events), Call for Speakers, Kurse/Trainings (`Course`), Open-Source-Projekte (`SoftwareSourceCode`), Fallstudien, Fragen und Antworten (`QAPage`), Stellen/Aufträge (`JobPosting`), Podcast-Gäste.

5. **Community-Spotlight**: Aktive Mitglieder sammeln Punkte; ab einer Schwelle (z. B. 100) gibt es einen Spotlight-Platz (max. wenige pro Monat). Eigenen Beitrag (Feed-Artikel/Wiki) einreichen, Team prüft in einer Warteschlange, Teilen auf der LinkedIn-Firmenseite „M365 Show“ als „Aus der Community“ mit Einwilligung des Mitglieds, zunächst per LinkedIn-Teilen-Dialog (kein API-Zugang nötig), später automatisch (Community Management API, `w_organization_social`, LinkedIn-Freigabe nötig). Dazu Abzeichen „Spotlight“. Zusätzlich: „Auf LinkedIn teilen“-Knopf für Profile, Firmen, Events.

## Backlog (später, wenn die Plattform genutzt wird)
- **LinkedIn Events Management API** (Standard Tier, Self-Service): Events von Veranstaltern automatisch mit LinkedIn synchronisieren (anlegen/ändern, Anmeldungen, Leads). Vorher klären: Rechte/Endpunkte in der technischen Doku, ob ein Eintrag auf der Firmenseite „M365 Show“ möglich ist. Bis dahin: „Auf LinkedIn teilen“ + Anfrage „Auf M365 Show vorstellen“ mit Prüfung durch das Team.
- **LinkedIn Member Data Portability API (Member)**: Mitglied (nur EWR/Schweiz) verknüpft sein LinkedIn und übernimmt eigene Beiträge/Artikel in den Feed (Scope `r_dma_portability_self_serve`, App mit der vorgegebenen Standard-Firmenseite). Vor dem Bauen die Nutzungsbedingungen lesen; Verknüpfung einzeln und widerrufbar.
- **Automatisches Posten auf LinkedIn** (`w_member_social`, für Firmenseiten Community Management API / `w_organization_social`, Freigabe nötig).

## Offen (Betrieb)
- Microsoft-Login (MS_CLIENT_ID/MS_CLIENT_SECRET), Resend (RESEND_API_KEY), ADMIN_SUBS
- Glossar-Definitionen in 17 weitere Sprachen übersetzen, Muttersprachler-Prüfung ml/pa/ta/te/he/ar
- Tags schrittweise durch Glossar/Entitäten ersetzen (sichtbare Tags und Tag-Seiten entfernen, wenn die Entitäten die häufigen Tags abdecken)
- Monatsbudget für Artikel, Popularitäts-Reihenfolge, Original-Porträt fürs Presskit

## Idee: Foren je Thema (vom Nutzer, 30.10.)
- Zu jedem Thema/jeder Entität ein Forum; **nicht indexierbar** (noindex, nur eingeloggt oder per robots/Header gesperrt, nicht im Sitemap/llms.txt).
- Exklusive Bereiche für MVPs, MCTs, Regional Directors, Student Ambassadors usw. – auch **für ehemalige MVPs** (Former MVP).
- Zugang nur mit **geprüfter** Mitgliedschaft: Programm-Status wird bisher von Redaktion/Admin bestätigt (`programs.verified`); dafür braucht es Nachweis-Workflow (Nachweislink/MVP-Profil, Admin-Check, ggf. Ablauf/Re-Verify jährlich, Status „aktiv“ vs. „ehemalig“ mit Jahren).
- Offene Entscheidungen: Prüfmethode (Link zum offiziellen MVP-Profil + manuelle Bestätigung vs. Microsoft-Login-Claim), Moderation, Sichtbarkeit (komplett privat vs. lesbar für Mitglieder).

## Sponsoring-Matching (vom Nutzer, 30.10.)
- Firmen können privat angeben, ob sie Events sponsern wollen, plus Kriterien (Themen, Format, Mindest-Publikum, Regionen, Budget, Notizen) – **gebaut** (Tabelle `org_sponsor`, nur Inhaber/Admins sehen/ändern, nie öffentlich/exportiert).
- Offen: Veranstalter-Seite, sobald es Events gibt – Veranstalter sehen nur „sucht Sponsoren: ja/nein“ + die Kriterien passender Firmen (kein Export, nur eingeloggt als Veranstalter), Kontaktaufnahme über die Plattform.

## Struktur (vom Nutzer, 30.10.): Mitglieder, Firmen und Events getrennt
- Drei eigene Bereiche mit eigenen Verzeichnissen, Seiten und Menüpunkten: Mitglieder (`/community/members/`, gebaut), Firmen (`/community/companies/`, gebaut), Events (`/community/events/`, geplant) – Events haben eigene Veranstalter-Konten/Rollen und sind nicht Teil des Firmenprofils; Verknüpfung nur per Relation (Firma/Person ↔ organizer/sponsor/speaker).
