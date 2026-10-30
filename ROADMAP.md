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

## LinkedIn Marketing-APIs (Lead Sync, Matched Audiences) – bewertet 30.10.
- Lead Sync API: holt Leads aus LinkedIn-Lead-Gen-Formularen von Anzeigen (braucht Werbekonto + Kampagnen). Nur sinnvoll, wenn wir z. B. für M365Con-Anmeldungen bezahlte Lead-Ads schalten → dann Sync in Newsletter/Teilnehmerliste.
- Matched Audiences: Retargeting/Kontaktlisten-Upload für Anzeigen; braucht Werbebudget, Insight-Tag mit Einwilligung bzw. Rechtsgrundlage für E-Mail-Uploads (DSGVO). Für die Community-Plattform selbst nicht nötig.
- Entscheidung: Backlog, nur bei geplanter LinkedIn-Werbung.

## Events – Stand 30.10.
- Gebaut: Tabellen `events`/`event_sessions`, Worker-API (`src/events.js`), Verwaltung in der Community-Seite (`assets/events.js`: Event anlegen/ändern, Sessions mit Speakern, Vorschläge von Mitgliedern mit Freigabe, Sponsoren-Ansicht für Veranstalter), öffentliche Seiten `/community/events/` + je Event (Schema.org Event, subEvent, performer → Profil-@id, about → Entitäten, organizer), Sessions auf Profilseiten, Events auf Firmen-/Profilseiten, Hub-Karte.
- Noch offen: Sponsoren-Zusage/Anzeige auf Eventseite (erst nach Bestätigung der Firma), iCal-Export, LinkedIn-Event-Posting (Events Management API), Speaker-Einladung per Link.

## Ideen (30.10.): Blog, Podcast-Upload, Stick-Man-Video
- Eigener Blog je Mitglied: Beiträge schreiben (Wiki-Markup, Quellen), eigene Seite `/community/u/<handle>/blog/`, Schema.org BlogPosting/Blog, Upvotes, Moderation für Neue, Feed (zählt als Creator-Feed). Punkte/Badge „Autor".
- Podcast-Upload ins m365con.net-Netzwerk: Mitglieder reichen Podcast-Folgen/Shows ein (RSS-Feed anmelden oder Audio hochladen), Prüfung durch Redaktion, Anzeige im Netzwerk; Schema.org PodcastSeries/PodcastEpisode. Technische Frage: Speicher (R2) oder nur RSS-Verknüpfung.
- Eigenes Stick-Man-Video aus Blog/Podcast: Mitglied bekommt aus seinem Beitrag ein animiertes Erklärvideo (Pipeline wie bei den Dubs). Offen: Kosten/Kontingent pro Mitglied, Qualitätsprüfung, Warteschlange – eher als Belohnung (Punkte) oder Premium.

## Präzisierung Podcast (30.10.): Community-Episoden mit Upvote-Schwelle
- Mitglieder laden **Episoden (Audio) hoch** (nicht nur RSS): Titel, Beschreibung, Themen (Entitäten), Cover, Sprache, Erklärung „Rechte liegen bei mir / KI-Einsatz offengelegt“.
- Community-Liste mit **Upvotes**. Ab **X Upvotes** (Vorschlag: 25 von verschiedenen Konten, Mindestalter der Konten) wandert die Episode in die **redaktionelle Prüfung** durch Mirko (Freigabe/Ablehnung mit Notiz).
- Nach Freigabe: Veröffentlichung auf **m365.fm** (Spreaker-Entwurf über die bestehende Pipeline, Mirko veröffentlicht), mit Autor-Credit und Link zum Profil; Schema.org PodcastEpisode.
- Technik: Audio in Cloudflare R2 (mp3, max. ~100 MB), Worker-Endpunkte für Upload/Votes/Review, Admin-Queue; Missbrauchsschutz (Rate-Limit, Dateityp-Prüfung, Melden-Button).
- Offen: Schwellenwert X, Speicherlimit je Mitglied, ob Upload nur für verifizierte/aktive Mitglieder.

## Podcast-Upload direkt zu Spreaker (30.10., ersetzt R2-Idee)
- Worker lädt die Audiodatei beim Einreichen per Spreaker-API als **unveröffentlichten Entwurf** hoch (Show „Community“); kein eigener Speicher (R2) nötig. Grenze: Worker-Speicher → mp3 bis ca. 50 MB.
- Auf unserer Seite bleibt die Episode „ausstehend“; die Community stimmt über den Pitch (Titel, Beschreibung, Themen, Autor) ab – Audio ist im Entwurf nur für Mirko hörbar.
- Bei X Upvotes: **Benachrichtigung an Mirko** (Web-Push über vorhandenes `push.js`, später E-Mail über Resend) mit Link zum Spreaker-Entwurf. Mirko prüft/veröffentlicht in Spreaker; „Ablehnen“ löscht den Entwurf.
- Schutz: nur Mitglieder mit öffentlichem Profil, 1 Upload/Woche, Dateityp-Prüfung, Entwurf wird nach 30 Tagen ohne Schwelle gelöscht (Spreaker-Speicherlimit schonen).
- Voraussetzungen: Spreaker-API-Token als Worker-Secret (Spreaker-Re-Auth steht ohnehin offen), Show-ID der Community-Show.

## Kompletter Kreislauf Community-Episode → Stick-Man-Video (30.10., Präzisierung)
1. Mitglied lädt Episode hoch → Worker legt sie als **Entwurf bei Spreaker** an (Entwurfs-ID wird gespeichert).
2. **25 Upvotes** → Benachrichtigung an Mirko zur Prüfung.
3. Mirko **veröffentlicht in Spreaker**.
4. Der Worker-Cron (alle 30 Min) fragt die Spreaker-API ab: Ist die gespeicherte Episode jetzt veröffentlicht? Dann Status „veröffentlicht“, Autor wird benachrichtigt, Credit/Link auf Profil.
5. Die veröffentlichte Episode löst die **Stick-Man-Video-Produktion** aus (bestehende Pipeline Episode → Video); das fertige Video wird dem Mitglied zugeordnet (Link im Profil/Beitrag) – das Video ist die Belohnung für die freigegebene Episode.
- Offen: wie die Video-Pipeline angestoßen wird (GitHub-Workflow per Dispatch aus dem Worker vs. Pipeline pollt Spreaker selbst), wo das Video erscheint (YouTube-Kanal, Episodenseite).
- **Sprache (30.10.):** Beim Upload wird die Episodensprache gewählt; der Entwurf geht in die **Spreaker-Show dieser Sprache** (bestehende 19 M365.FM-Sprach-Shows, Zuordnung Sprache → Show-ID wie im Dub-Downloader), und Stick-Man-Video/Benachrichtigungen/Anzeige folgen derselben Sprache. Keine eigene „Community-Show“ nötig.

## Stand 30.10. (nachts) – Gebaut seit der letzten Runde
- Punkte-System (Skala + Einlösen), flüchtige Nachrichten (7 Tage, Tageslimit), Sponsor-Anfragen (2 frei, weitere 1000 Punkte), Abzeichen (nur erreichte sichtbar), Programm-Icons (MVP/MCT/RD/MSA/Mitarbeiter/Partner), verifizierte Programme dürfen bearbeiten
- Community-Abstimmung über Wiki-/Entitäts-Änderungen (Mehrheit ab 3 Stimmen, Eigentümer entscheidet sofort), Posteingang, bestätigte Experten stimmen mit
- Profile/Firmen/Events sind selbst verwaltete Entitäten; M365.FM/M365Con/Event/Profil für den Admin zugeordnet (Cron)
- Community-Reiter, Glossar aus Entitäten, Kurzbeschreibung Pflicht, Autorenbox aus Profil, Artikel-Autolinks entfernt, Speaker-Einladung per E-Mail/LinkedIn-Text

## Offen (neu, 30.10. nachts)
- Schema.org-Autor in Artikeln aus dem Profil, Hover-Fenster für Personen, Abstimmungs-Anzeige/Folgen von Themen, Sofort-Anzeige neuer Profile/Events im Verzeichnis (statt stündlich), Datenschutz-Text zu flüchtigen Nachrichten, Übersetzungs-Angebote für Kurzbeschreibungen, Event-Entität mit Link zur Eventseite

## Backlog: Englisch als eigene Sprache (30.10., vom Nutzer)
- Englisch soll als gleichwertige Sprache neben den 19 Dub-Sprachen stehen (`/en/` mit Episodenseiten, Sprachwahl, Hreflang, Sitemap). Bisher ist Englisch nur die Startseite `/`, es gibt keine englischen Episodenseiten.
- Quelle: Hauptshow auf Spreaker, Show-ID `6704921` (in `config.json` als `show_map.en`, in `never_auto_map_show_ids`, also nicht automatisch anfassen).
- Plan: Sync-Schritt im Seitenbau (braucht `SPREAKER_TOKEN`) holt die Hauptshow-Episoden, ordnet sie über den Video-Link im Folgentext den YouTube-IDs zu und legt je Folge einen `en`-Eintrag in `episodes/<id>.json` an (Titel, Beschreibung, Show-ID). Danach `en` in `LANGS` (inkl. Texte TOP_L/REC_L/UI) und einen Testlauf im echten Bau, weil das Token lokal nicht ausführbar ist.
- Risiko: betrifft den gesamten Seitenbau (500+ Seiten); bestehende Sprachen dürfen sich nicht ändern.
- Community-Plattform bleibt mit Englisch als Basissprache (Kurzbeschreibung in einer Sprache Pflicht, weitere freiwillig).


## Grundregel: MCP & KI-Anbindung wachsen mit
Jede neue Funktion der Plattform (Log, Events, Firmen, Forum, Blog, Copilot-Bibliothek, Folgen …) bekommt zugleich ein MCP-Tool in `worker/src/mcp.js` (mit `de`-Beschreibung). Die Anleitungsseite `/community/mcp/` liest die Tool-Liste automatisch daraus (`tools/dump_mcp_tools.mjs`). Gilt für Claude, ChatGPT und Microsoft Copilot (Copilot Studio / M365-Agenten). Phase 2: OAuth für direkte Anmeldung; Phase 3: Tools für Events/Sessions, Firmen, Log, Folgen.

Ausgemusterte Seiten: in `data/retired.json` eintragen (mit `to` = Nachfolger-Verknüpfung, ohne = „gibt es nicht mehr“). Wird beim Build zur Hinweisseite (noindex). Gilt bei jeder umbenannten/entfernten Seite.

## Übersetzungen (Regel)
- Fehlende EN/DE-Texte zuerst über die Community: MCP-Tool `list_translation_tasks` + `propose_entity_edit` (kostet die Plattform nichts). Nur der Rest wird mit `tools/translate_missing.py` (Haiku) im Stapel übersetzt.
- Namen werden nie übersetzt: Session-Titel, Event-, Produkt-, Personen- und Firmennamen, Abkürzungen, Prüfungscodes.

## Podpage-Ablösung (nach der Konferenz M365Con, Jan 2027)
Podpage kostet 65 $/Monat (ca. 780 $/Jahr). Ziel: m365.fm komplett auf dub.m365.fm umziehen und Podpage kündigen. Bis zur Konferenz wird dub.m365.fm weiter ausgebaut; Podpage bleibt unverändert.
- Inventur M365 FM Podcast (Stand 30.10.2026): 1.115 Episoden, 2.426 Videos, 5 Hosts, 13 Links, 6 Sponsoren. Blog, Seiten, Gäste, Bewertungen, Weiterleitungen, Downloads und Shop waren wegen Podpage-Serverfehler (502) nicht abrufbar, erneut prüfen.
- Schritte: 1) alles als JSON ins Repo sichern (Podpage-MCP, read-only), 2) Seiten für Videos, Hosts, Sponsoren, Links, Blog/Seiten im Generator ergänzen, 3) Weiterleitungen aller alten Podpage-URLs, 4) Domain www.m365.fm umziehen (Suchplätze erhalten), 5) erst dann Podpage kündigen.
- Nur mit Server nötig: Kontaktformular, Sprachnachrichten, Newsletter, Bewertungen (Worker + Resend/R2). Shop weglassen oder extern verlinken.
- Weitere Podpage-Podcasts im Konto: "Business → IT | IT → Business" und "DataScience Show Podcast" (bei der Ablösung mitprüfen).

## Event-Rollen (gebaut: Team)
- Tabelle `event_roles`; Rollen: Organisator (alles), Co-Organisator (Event, Programm, Sponsoring, Rollen), Programm-Manager (Sessions), Sponsoren-Manager (Anfragen), Kommunikation (Texte/Links), Helfer (nur im Team genannt). Zentrale Prüfung `canManage(db,user,ev,perm)`.
- API `/api/event/:handle/team` (GET/POST/DELETE), MCP `get_event_team`, `set_event_role`, UI-Block „Team und Rollen" im Event-Editor.
- Offen: Teilnehmer-Anmeldung mit Warteliste, Sponsor-/Medienpartner-Bestätigung, Einladung per E-Mail (RESEND_API_KEY).
