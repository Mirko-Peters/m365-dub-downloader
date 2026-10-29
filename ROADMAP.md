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

## Offen (Betrieb)
- Microsoft-Login (MS_CLIENT_ID/MS_CLIENT_SECRET), Resend (RESEND_API_KEY), ADMIN_SUBS
- Glossar-Definitionen in 17 weitere Sprachen übersetzen, Muttersprachler-Prüfung ml/pa/ta/te/he/ar
- Tags schrittweise durch Glossar/Entitäten ersetzen (sichtbare Tags und Tag-Seiten entfernen, wenn die Entitäten die häufigen Tags abdecken)
- Monatsbudget für Artikel, Popularitäts-Reihenfolge, Original-Porträt fürs Presskit
