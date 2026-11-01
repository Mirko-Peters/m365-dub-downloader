# Hinweise für GitHub Copilot (Coding Agent) – M365.FM

Willkommen im Team. Dieses Repo baut **www.m365.fm**. Der Dev-Chef (Claude) prüft und merged deine Pull Requests. Bitte merge nicht selbst.

## Aufbau
- **Statischer Seitenbau:** `generate_site.py` und `site_*.py` schreiben nach `docs/` (GitHub Pages) und `r2out/` (Cloudflare R2). Beides wird nicht committet.
- **Site-Worker:** `sitewrk/index.js`, Cloudflare vor der Seite (Weiterleitungen, R2-Auslieferung).
- **Community-API:** `worker/` (Cloudflare Worker mit D1). Migrationen liegen in `worker/migrations/`, Crons in `worker/src/index.js`.
- **Daten:** `data/*.json(.gz)` liegen im Repo und sind die Quelle für den Seitenbau. `data/podpage/` ist die Sicherung der alten Podpage-Seite und wird nur gelesen.
- **Workflows:** `.github/workflows/`. `site.yml` baut die Seite. Die blockierenden Prüfungen sind `check_sitemaps.py`, `check_encoding.py`, `check_titles.py` und `check_schema.py`.

## Feste Regeln
1. **Nichts löschen.** Keine Dateien, Datensätze oder D1-Zeilen löschen und keine Sicherung verkleinern. Alte Fassungen werden als `old` markiert oder archiviert.
2. **Keine Secrets.** Keine Schlüssel oder Tokens in Code, Logs, Commits oder PR-Texten. Zugangsdaten kommen nur aus GitHub Secrets.
3. **Bilder** liegen nur im eigenen R2-Bucket und werden über `https://img.m365.fm/…` ausgeliefert (siehe `CLAUDE.md`). Fremde Bild-URLs nicht neu einbauen.
4. **Nicht anfassen:**
   - `shownotes/`: Bereich der Shownotes-Generator- und QA-Sitzungen, einschließlich `APPROVED` und `PAUSED`.
   - `data/r2_map.json`: wird nur vom Workflow `r2-images.yml` geschrieben.
   - `data/podpage/*`.
5. **Sprache:** Kommentare, Commit-Messages, PR-Titel und PR-Texte auf Deutsch, kurz und sachlich.
6. **Kleine, gezielte Änderungen.** Bitte keine Umformatierung ganzer Dateien und keine neuen Abhängigkeiten ohne Grund.

## Vor dem PR prüfen
- Python: `python3 -m py_compile <geänderte Dateien>`. Dazu ein kleiner Test oder ein Nachweis im PR-Text, zum Beispiel ein Befehl und seine Ausgabe.
- Worker (`worker/`): `cd worker && node --test`, außerdem `node tools/check_mcp_coverage.mjs` (muss „Alles abgedeckt.“ melden).
- Site-Worker: `node --check sitewrk/index.js`.
- Workflows: YAML muss gültig sein. Ein Commit-Schritt darf Fehler nicht verschlucken: vor dem Push `git pull --rebase --autostash` ausführen und es mehrmals versuchen.
- Der volle Seitenbau dauert rund 20 Minuten. Bei Änderungen am Seitenbau beschreibe im PR, welche Seiten betroffen sind und wie du es geprüft hast.

## PR-Text
Gliederung: **Warum** (Problem mit Beleg), **Was** (Änderung), **Test** (was du geprüft hast, mit Ergebnis). Verweise auf Dateien mit `datei:zeile`.
