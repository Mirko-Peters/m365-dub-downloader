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

## Podcast-Umzug (gebaut, Betrieb offen)
- Mitglieder ziehen per RSS-URL zu M365.FM um (`/shows/<slug>/`), Import + Tagesabgleich + Transkripte; Freigabe durch Team, Einwilligung wird gespeichert.
- Einnahmen: Werbung auf den Show-Seiten gehört M365.FM, eigenes Sponsoring des Podcasters bleibt bei ihm. Später Bezahl-Option: solange bezahlt wird, ist die Werbung auf seiner Show abgeschaltet.
- Geplant: Umzug über die Spreaker-API (Show im M365.FM-Konto anlegen, Folgen hochladen, neuen Feed ausgeben) als GitHub-Action-Job; klären: Tarif/Speicher, neue Folgen nachziehen.
- Offen: Nutzungsbedingungen rechtlich formulieren, Werbe-/Sponsoring-Platz auf Show-Seiten, eigener M365.FM-Feed je Show (`itunes:new-feed-url`).

## Mail-System (gebaut, Versand braucht RESEND_API_KEY)
- Bestätigte Adresse je Konto, Arten einzeln schaltbar (Antworten auf Kommentare, Wunsch-Status, Show-Freigabe, Einladungen), Warteschlange mit Wiederholung, Abmeldelink und List-Unsubscribe in jeder Mail, Cron-Versand alle 30 Minuten.
- Offen: Absender-Domain bei Resend verifizieren (SPF/DKIM für m365.fm), weitere Auslöser (neue Microsoft-Updates je Produkt, Gäste-/Speaker-Anfragen, Digest wöchentlich).

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
Jede neue Funktion der Plattform (Log, Events, Firmen, Forum, Blog, Copilot-Bibliothek, Folgen …) bekommt zugleich ein MCP-Tool in `worker/src/mcp.js` (mit `de`-Beschreibung). Die Anleitungsseite `/community/mcp/` liest die Tool-Liste automatisch daraus (`tools/dump_mcp_tools.mjs`). **Täglicher Abgleich** (`.github/workflows/mcp-check.yml`, `tools/check_mcp_coverage.mjs`): jede API-Route muss in `worker/mcp_coverage.json` einem Tool zugeordnet oder begründet ausgenommen sein, sonst schlägt der Lauf fehl und ein Issue `mcp-sync` entsteht; neue Seitenfunktionen also immer als Tool in `BRIDGE`/`TOOLS` ergänzen. Die Anleitungsseite und der Skill werden täglich neu gebaut, der Worker täglich neu ausgerollt. Gilt für Claude, ChatGPT und Microsoft Copilot (Copilot Studio / M365-Agenten). Phase 2: OAuth für direkte Anmeldung; Phase 3: Tools für Events/Sessions, Firmen, Log, Folgen.

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

## Teilnehmer und Speaker (gebaut)
- Anmeldung `/api/event/:h/register` mit Warteliste (Plätze via `/capacity`), Sichtbarkeit in der Teilnehmerliste wählt jeder selbst (Standard aus), Block „Anmeldung" auf der Event-Seite, E-Mail-Einladung `/invite-mail` (braucht RESEND_API_KEY).
- Speaker: MCP `list_my_speaker_requests`, `respond_speaker_request`, `update_my_session`; bestätigte Speaker pflegen Beschreibung und Aufzeichnung ihrer Session selbst (Titel/Zeit bleiben beim Team).
- Offen: Sponsor-/Medienpartner-Bestätigung, iCal-Export, „Meine Anmeldungen" im Profil.

## Event-App (Premium-Idee, später)
- Idee: Eine eigene App für Event-Veranstalter (iOS/Android) als bezahltes Zusatzprodukt, das Veranstalter für einen kleinen Betrag bekommen. Veranstalter bekommen ihre Event-App mit Programm, Merkliste, Anmeldung, Teilnehmerliste (nur wer sichtbar sein will) und Push-Nachrichten.
- Technik-Weg: Zuerst PWA (Manifest, Icons, Installationshinweis, Push über den vorhandenen Service Worker), danach bei Bedarf eine Hülle mit Capacitor für App Store und Play Store. Gleiche API wie die Webseite.
- Offene Punkte: Preismodell (einmalig je Event oder Abo), Branding je Event (Logo, Farben), Zahlungsanbieter, Store-Gebühren (Apple 99 $/Jahr, Google 25 $ einmalig). Erst nach der M365Con entscheiden.

## Partner, iCal, Weitergabe an m365con.net (gebaut)
- Sponsoren/Medienpartner: `event_partners`, eine Seite schlägt vor, die andere bestätigt (Event-Team ↔ Firma), API `/api/event/:h/partners`, Eingang `/api/events/partners-mine`, MCP `manage_event_partner`; bestätigte Partner erscheinen auf der Event-Seite und als `sponsor` im Schema.org-Event.
- iCal: `event.ics` je Event (inkl. Sessions) mit Button auf der Event-Seite.
- m365con.net: Wer sich hier für M365Con anmeldet, kann per Haken einwilligen, dass Name und E-Mail einmalig an HeySummit (Event 229506) gehen. Tabelle `event_transfers`; MCP-Admin-Tools `list_event_transfers` und `mark_event_transfers_done` (Adresse wird danach gelöscht). Übertragen wird mit der HeySummit-Anbindung (`create_attendee`) in einer Claude-Sitzung, die auch den dub-MCP verbunden hat – später als geplante Aufgabe automatisierbar.
- Offen: direkter HeySummit-API-Schlüssel im Worker (dann ohne Claude-Sitzung), Mail-System (Einladungen, Bestätigungen).

## Veröffentlichungs-Strecke: Podcast-Upload + YouTube-Upload (Idee)
- Eine Folge einmal hochladen → Entwurf bei Spreaker (Podcast) und Video bei YouTube; Titel, Beschreibung, Kapitel und Sprache aus denselben Daten; Episodenseite auf dub.m365.fm entsteht automatisch.
- YouTube: Data API `videos.insert`, OAuth-Recht „Videos hochladen". Hürden: Uploads aus ungeprüften API-Projekten bleiben zunächst privat (Audit des API-Projekts nötig, kann Wochen dauern); Kontingent ca. 1.600 von 10.000 Einheiten pro Upload und Tag (≈ 6 Videos/Tag, mehr nur per Antrag).
- Ausführung nicht im Cloudflare-Worker (große Dateien), sondern in GitHub Actions oder lokal, ähnlich dem Dub-Downloader.
- Reihenfolge: nach der Konferenz; vorher Google-Projekt und Audit-Antrag anstoßen, weil die Wartezeit der Engpass ist.

## Mehrsprachigkeit Stufe 1 (gebaut)
- Community-Seiten (Mitglieder, Firmen, Events, Entitäten) gibt es zusätzlich auf fr, es, it, nl, pt, pl (`site_i18n.py`, Texte in `data/ui_i18n.json`). Oberfläche übersetzt; Inhalte ohne Übersetzung fallen auf Englisch zurück; Seiten dieser Sprachen sind `noindex` und stehen nicht in der Sitemap.
- Offen: JS-Oberflächen (`assets/*.js`) in den neuen Sprachen, Texte im Code mit `if lang == "de"` (ca. 25 Stellen, derzeit englisch), Entitäten-Beschreibungen/Inhalte per MCP/Stapel, weitere 11 Sprachen, hreflang erst wenn Inhalte echt übersetzt sind.

## Speaker-Verknüpfung (gebaut)
- Vom Veranstalter importierte Speaker (M365Con-Programm) bekommen einen Verknüpfungslink (Token). Der Speaker meldet sich an, legt sein öffentliches Profil an und verbindet es per Link; danach erscheinen seine Sessions auf dem Profil und bestätigen seine Expertise. Kopierbutton im Event-Editor.

## Oberflächen-Übersetzung über den Worker (gebaut)
- Der Worker übersetzt mit dem Cloudflare-Secret `ANTHROPIC_API_KEY` (Haiku) die Texte aus `ui_js_en.json` (297 Texte) in fr, es, it, nl, pt, pl: je Cron-Lauf 2 Blöcke à 40 Texte (≈ 7–8 Stunden insgesamt), gespeichert in der Tabelle `ui_i18n`, Notaus wie bei der Entitäten-Übersetzung. Der Seitenbau holt sie stündlich über `/api/ui-i18n` und schreibt `assets/ui-<sprache>.js`.
- Status: `/api/admin/translate` (Felder `ui_done`, `ui_error`). `tools/translate_ui.py` bleibt als lokaler Weg.

## Meine Anmeldungen (gebaut)
- Im Events-Bereich der Community: Block „Meine Anmeldungen" mit Status (angemeldet/Warteliste), Sichtbarkeit in der Teilnehmerliste, Hinweis zur Übergabe an m365con.net und Abmelden. API `/api/events/my-registrations`, MCP `list_my_registrations`. Die neuen Texte (`events.RQ`) übersetzt der Worker automatisch mit.
- Offen: Abzeichen/Hinweise in der Kopfzeile („Du hast X Anmeldungen"), iCal-Sammelexport aller eigenen Events.

## Mehrsprachigkeit Stufe 2 (gebaut, 30.10.)
- Community-Seiten jetzt in allen 20 Sprachen (zusätzlich id, ru, uk, ar, he, hi, ja, ko, ml, pa, ta, te; ar/he rechts-nach-links). Seiten der weiteren Sprachen sind noindex, nicht in der Sitemap.
- Der Worker übersetzt Skript-Texte **und** Texte aus dem Seitencode (Schlüssel `py:...` in `ui_js_en.json`) für alle 18 Sprachen (3 Blöcke je 30-Minuten-Lauf); der Seitenbau holt sie von `/api/ui-i18n`. Fortschritt: `ui_done` unter `/api/admin/translate`.
- Offen: Muttersprachler-Prüfung, echte Inhalts-Übersetzung, hreflang erst dann.

## Blog je Mitglied (gebaut, 30.10.)
- Worker `src/blog.js`: Tabellen `blog_posts`/`blog_votes`; Speichern/Einreichen (Wiki-Markup mit Quellen wie im Glossar, Themen = Entitäten, 20 Sprachen), Neue → Prüfung (`/api/admin/blog`, `/api/admin/blog/decide`), ab 25 Punkten/Pro/Redaktion sofort live, Upvotes (nicht für eigene Beiträge), Export `/api/blog/export`, Live-Votes `/api/blog/votes`.
- Seiten: `/community/u/<handle>/blog/<slug>/` (BlogPosting, author → Personen-Entität, about → Themen, citation → Quellen), Autoren-Blog, Gesamt-Blog `/community/blog/`; nur in der Sprache des Beitrags; en/de indexierbar, übrige noindex.
- Oberfläche: Reiter „Blog“ in der Community (`assets/blog.js`). MCP: `list_my_blog_posts`, `save_blog_post`, `delete_blog_post` (+ HOWTO „blog“).
- Prüf-Warteschlange: im Reiter Blog für Admin/Redaktion (gebaut). Offen: Badge „Autor“, Punkte für veröffentlichte Beiträge, Blog-Link auf der Profilseite, Feed-Aufnahme (Creator-Feed), Hover/Teilen, Kommentare, Stick-Man-Video aus Beitrag (Punkte-Katalog „video“).

- Blog-Regel (30.10.): Jeder kann bloggen, Beiträge sind sofort live (öffentliches Profil nötig). In den Google-Index und die Sitemap kommt ein Beitrag erst ab 10 Upvotes (`INDEX_VOTES` in `site_blog.py`); Verzeichnisse sind nur indexierbar, wenn sie mindestens einen solchen Beitrag enthalten. Die Prüf-Warteschlange bleibt für Meldungen/Sonderfälle; Redaktion kann Beiträge löschen.

## Idee (30.10., vom Nutzer): Produkt-Updates und News von Microsoft einziehen
- Updates und News von Microsoft automatisch einlesen (Microsoft-365-Roadmap, Message Center/„What's new“, Release-Notes und Blogs der Produkte, RSS/Atom wo vorhanden) und den **Entitäten** (Produkte/Plattformen) zuordnen.
- Je Entität eine Zeitleiste „Updates & News“; Nutzer können Themen folgen (siehe „Thema folgen“); Wichtigkeit bewerten (Community-Upvotes, später KI-Einstufung), Übersetzung über den Worker.
- Nur Titel, Link, Datum und eigene Kurzfassung speichern (kein Volltext der Quellen, Quellenangabe Pflicht). Technisch ähnlich zu `feed_items`/Feeds im Worker; Abgrenzung zur Idee „Microsoft-Updates-Seite“ (Update-Tracker nach Themen und Wichtigkeit).

## Idee (30.10., vom Nutzer): Freiwillige Unterstützung im Medium-Stil
- Leser unterstützen freiwillig (Mitgliedschaft oder Einzelbetrag); die Einnahmen werden nach einem festen Schlüssel an die Autoren verteilt (z. B. nach Lesezeit/Upvotes/Abonnenten der unterstützten Autoren). **Komplett freiwillig**, keine Bezahlschranke; **kein PayPal** (Anbieter noch offen, z. B. Stripe/Mollie – Auszahlung an Creator, Steuer/Rechnungen und DSGVO vorher klären).
- Vorher klären: Auszahlungsschwelle, Gebühren, Rechtsform (Plattform als Vermittler), Transparenz-Seite, was mit Beiträgen von Nutzern ohne Auszahlungsdaten passiert.
- Passt zu Blog, später Podcast; Voraussetzung ist ein stabiler Blog mit Abonnenten (Follow).

## Blog Ergänzungen (gebaut, 30.10.)
- Blog-Link auf der Profilseite, Badge „Blog-Autor“ (`author`), Punkte (5 je veröffentlichtem Beitrag bis 20, 1 je Upvote bis 200), Beiträge erscheinen im Creator-Feed (Kanal „blog“), Kommentare unter Beiträgen (vorhandenes Kommentar-System, `vid=blog<id>`, auch Englisch), Blog abonnieren (Follow, `blog_follows`) und RSS je Autor und gesamt (`feed.xml`).
- Offen: E-Mail-Benachrichtigung an Abonnenten (mit dem Mailsystem/Resend), Newsletter-Kanal des Creators beim Abonnieren zeigen, Übersetzung der Badge-Texte (bisher Englisch/Deutsch).

## Podcast-Kanäle der Community (als Nächstes, wie der Blog)
- Gleiche Mechanik wie Blog: Creator, Folgen, Upvotes, Follow/RSS, Kommentare, Badge „Podcaster“, Creator-Feed. Unterschied: **Prüfung durch Mirko in Spreaker** (Folge wird dort als Entwurf geprüft und freigegeben, danach Anzeige/Index); Index-Schwelle wie im Blog (Upvotes), Details (Upload direkt zu Spreaker, Show je Creator) siehe „Podcast-Upload direkt zu Spreaker“.

## Community-Podcast (gebaut, 30.10.)
- Worker `src/podcast.js`: Einreichen mit mp3 (max. 50 MB, Magic-Byte-Prüfung, Rechte-Haken, KI-Offenlegung) → **Entwurf in der Spreaker-Show der Sprache** (`POST /episodes/drafts`, danach Audio per `POST /episodes/<id>`); Abstimmung (Konten ab 24 h, nicht für eigene Folgen); ab **25 Stimmen** Status „review“ + Web-Push an Admins/Redaktion; Mirko prüft und veröffentlicht **in Spreaker**; der Cron (30 Min) erkennt `published_at`/PUBLIC und setzt „published“ (Creator-Feed, Badge „Podcaster“, 20 Punkte). Ablehnen löscht den Entwurf; 30 Tage ohne Schwelle → Entwurf wird gelöscht. Eine Einreichung pro Woche, öffentliches Profil nötig. Secret `SPREAKER_TOKEN` nötig.
- Seiten: `/community/podcast/<id-slug>/` (PodcastEpisode, Spreaker-Player, Kommentare `vid=podcast<id>`, Themen bis 10), `/community/podcast/` und `feed.xml`; indexierbar (Redaktion hat geprüft). Reiter „Podcast“ in der Community inkl. Admin-Bereich. MCP: `list_podcast_pitches`, `vote_podcast_pitch`, `list_my_podcast_episodes`.
- Blog und Podcast: bis zu **10 Themen (Entitäten)** je Beitrag/Folge.
- Offen/ungetestet live: Spreaker-API-Details (Entwurf + Audio nachladen; Token-Rechte), Stick-Man-Video nach Veröffentlichung, Follow für Podcast-Autoren (nutzt vorerst das Blog-Follow), E-Mail-Benachrichtigungen (Mailsystem später).

- Präzisierung (30.10.): Bei 25 Stimmen bekommt Mirko die Benachrichtigung „Stick-Man-Video erstellen und in Spreaker freigeben“ (Web-Push, im Reiter Podcast als 🎬-Aufgabe, MCP-Tool `list_podcast_todo`); E-Mail dazu mit dem Mailsystem. Veröffentlichen macht Mirko selbst in Spreaker.

## Startseite als Inhalts-Hub (gebaut, 30.10.)
- Startseite (`/`) und die Sprach-Startseiten zeigen jetzt gemischte Inhalte (Blog, Community-Podcast, kommende Events, Stick-Man-Videos) nach Datum mit Filter-Chips; Stick-Man-Videos sind ein Filter-Punkt (`site_home.py`). Titel/Beschreibung der Wurzelseite auf Community umgestellt; die Sprach-Startseiten behalten ihre SEO-Titel.
- Offen: weitere Filter (Mitglieder neu, Wiki/Glossar-Änderungen, Microsoft-News), eigene Seite nur für Stick-Man-Videos, Sprach-Startseiten stärker auf Community umstellen, Hero der Sprach-Startseiten übersetzen.

## Creator-Videos auf den YouTube-Kanal „m365 Show“ hochladen (30.10., vom Nutzer)
- Ziel: Creators laden ihre Videos über die Plattform hoch; sie erscheinen auf dem YouTube-Kanal **m365 Show** (Kanal gehört Mirko) – wie beim Podcast: Entwurf/privat, Community-Abstimmung, Freigabe durch Mirko, dann Veröffentlichung, Anzeige im Startseiten-Filter „Videos“ und Creator-Feed.
- Technik (Skizze): YouTube Data API `videos.insert` über das OAuth-Konto des Kanals (Refresh-Token als Worker-Secret). Der Worker legt eine **resumable Upload-Session** an und gibt die Upload-URL an den Browser; die Datei geht direkt Browser → YouTube (kein Worker-Limit für große Videos). Sichtbarkeit zuerst **privat**; nach Freigabe `privacyStatus=public` (oder Zeitplan, siehe Taja-/Veröffentlichungs-Workflow). Cron fragt den Status ab wie beim Podcast.
- Zu klären/Voraussetzungen: Google-Cloud-Projekt mit YouTube Data API v3 + OAuth-Zustimmungsbildschirm; **API-Audit** nötig, sonst sind per API hochgeladene Videos gesperrt/privat; Kontingent (Upload ≈ 1.600 von 10.000 Einheiten/Tag → rund 6 Uploads/Tag, Erhöhung beantragen); Rechte-/Urheberrechtserklärung, KI-Kennzeichnung, Kinder-/Altersangaben (`madeForKids`), Titel/Beschreibung/Tags/Thumbnail, Kategorie; Abstimmungsschwelle und Benachrichtigung an Mirko; Missbrauchsschutz (Konten-Alter, 1 Upload/Woche, Größen-/Dauerlimit).
- Passt zur Veröffentlichungs-Strecke (Podcast + YouTube) weiter oben; Google-Projekt und Audit früh starten.
- Kontingent (Klärung 30.10.): Erhöhung nur per **Antrag** (YouTube API Services – Audit and Quota Extension Form), kostenlos; ein Bezahl-Tarif für mehr Kontingent ist mir nicht bekannt. Nicht mit mehreren Projekten umgehen (verstößt gegen die Nutzungsbedingungen). Zu Beginn reichen die 10.000 Einheiten für etwa 6 Uploads am Tag.

## Gäste-Börse (gebaut, 30.10.)
- Podcaster, YouTuber und Veranstalter („Host“, bis zu 5 Einträge: Show/Kanal/Event) finden Gäste und Speaker („Speaker“, 1 Eintrag: als Gast verfügbar) – und umgekehrt. Zuordnung über **gemeinsame Themen (Entitäten, bis zu 10)**, dazu Sprache und Format (Podcast, YouTube, Event, Webinar, Blog); Treffer-Punkte = 3 je gemeinsames Thema + 2 je Sprache + 1 je Format, ohne gemeinsames Thema kein Treffer.
- Worker `src/guests.js` (`guest_listings`), Reiter „Gäste“ (`assets/guests.js`) mit eigenen Einträgen und passenden Treffern, Kontakt über die Plattform-Nachrichten (`?msg=<handle>`), öffentliche Seite `/community/guests/` (nur öffentliche Profile; en/de indexierbar), MCP `list_guest_listings`, `save_guest_listing`, `list_my_guest_matches`.
- Offen: Benachrichtigung bei neuem passenden Treffer (Mailsystem), „Gast in Folge“ aus Podcast-/Event-Daten verknüpfen (Speaker-Badge/Referenz), Bewertung/Empfehlung nach Auftritt, Filter nach Thema auf der öffentlichen Seite.

## Creator-Videos auf YouTube (gebaut, 30.10., ungetestet live)
- Worker `src/youtube.js`: `/api/video/init` legt per YouTube Data API eine **resumable Upload-Session (privat)** an, der Browser lädt direkt zu YouTube hoch (`assets/video.js`, Fortschrittsanzeige), `/api/video/confirm` prüft die Video-ID (nur private Videos des Kanals sind sichtbar), Abstimmung ab 24 h alten Konten, **25 Stimmen → Push an Admins** („Video prüfen und in YouTube Studio freigeben“), Admin-Liste/Ablehnen (löscht das Video), Cron erkennt `privacyStatus=public` → veröffentlicht (Creator-Feed „youtube“, Badge „Video-Creator“, 20 Punkte). 30 Tage ohne Schwelle → Video wird gelöscht; hängende Uploads nach 2 Tagen bereinigt.
- Seiten `/community/video/<id-slug>/` (VideoObject, Embed, Kommentare `vid=video<id>`), Verzeichnis, RSS; Startseiten-Filter „Creator-Videos“; Reiter „Videos“; MCP: `list_video_pitches`, `vote_video_pitch`, `list_my_videos`, `list_video_todo`.
- Secrets: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` (Scope `https://www.googleapis.com/auth/youtube`, nötig zum Hochladen **und Löschen**). Browser-Upload braucht CORS: die Session wird mit `Origin` der Seite angelegt. Datei bis 2 GB, eine Einreichung pro Woche.
- Ungetestet gegen das echte YouTube (lokal nur mit Attrappe); API-Audit/Kontingent siehe oben.

## Externe Quellen und Bibliothek (umgesetzt)
- **Externe Quellen im Feed**: Feeds werden jetzt automatisch gefunden (YouTube-@Handle → channel_id, GitHub `.atom`, Bluesky/Mastodon-RSS, sonst `<link rel="alternate">` der Webseite; täglich bis 3 Versuche je Kanal). Nur Titel + Link + Datum, `nofollow ugc`. Öffentlicher Export `/api/feed/export` → Startseiten-Filter „Von den Creatorn“. Offen: Kanal-Typen ohne Feed (LinkedIn, X, Twitch) bleiben ohne Inhalte.
- **Bibliothek** (`library.js`, `site_library.py`, `assets/library.js`): 16 Arten (Prompt, Custom Instructions, Agenten-Anweisung, Skill, Plugin, Manifest, Copilot-Studio-Thema, Flow, Power-Apps-Vorlage, KQL, DAX, Excel, Graph, PowerShell, Adaptive Card, Sonstiges), sofort sichtbar, Google-Index ab 10 Upvotes, Version zählt bei Inhaltsänderung hoch, Kommentare `lib<id>`, Kopieren-Knopf, Schema.org `SoftwareSourceCode`/`CreativeWork`, MCP-Tools `list_library`, `save_library_item`, `list_my_library`. Offen: Versionsverlauf, Forks/Remix, Punkte/Badge „Bibliothekar“.

## Update-Wächter (umgesetzt)
- Worker-Job `updates.js` (alle 30 Min., je Quelle höchstens alle 6 h): liest offizielle Feeds (M365-Roadmap, Azure Updates, Power-BI-, Fabric-, Power-Platform-, M365-, Dynamics-, Security-Blog), ordnet Meldungen den Produkt-/Plattform-Entitäten über Namen/Aliase zu (max. 3) und speichert nur Titel, Link, Datum, Quelle. Entitätsseiten zeigen „Neueste Updates“, Startseite hat den Filter „Microsoft-Updates“. Admin-Knopf „Update-Check jetzt“. Quellenliste: `SOURCES` in `updates.js` (Feeds ohne Antwort werden nach 8 Fehlversuchen pausiert).
- Offen: weitere Quellen je Produkt (Tech-Community-Blogs, Learn „What’s new“), Wichtigkeits-Bewertung, Updates-Übersichtsseite, E-Mail/Push bei Updates zu gefolgten Produkten (Mailsystem).

## Roadmap & Wunschliste, Profil/Community (umgesetzt, 30.10.)
- Reiter „Roadmap & Wünsche“ im Profil-Bereich (nur mit Konto sichtbar): Wünsche einreichen, abstimmen; Admin übernimmt (planned), hakt ab (done → Archiv) oder lehnt ab. Offene Plattform-Punkte werden vom Worker automatisch als „planned“ eingetragen (`seedRoadmap`).
- Umbenennung: Account-Bereich heißt „Profil“, Menü „Inhalte“ heißt „Community“.
- Eigene Seiten für gezogene Inhalte (`/community/feed/<id>-<slug>/`), SEO-Text per Editor oder MCP (`save_feed_item_text`), Push bei neuen Inhalten. Updates-Seite (`/updates/`) mit Microsoft-Updates und Tages-Batches.
- Offen (siehe Roadmap im Profil-Bereich): Microsoft-Login, Mail-System, Statuswechsel-Benachrichtigung, Firmen-Angebote auf Entitäten-Seiten, Update-Wichtigkeit, Bibliothek-Versionen/Forks, OG-Bilder inkrementell, YouTube-Audit.
