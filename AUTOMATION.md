# Automatik: Texte & Transkripte für die Dub-Folgen

Dieses Dokument ist die Arbeitsanleitung für den geplanten Claude-Lauf (alle 3 Stunden).
Der PC von Mirko (Windows-Aufgabe „M365 Dub Downloader“, alle 3 h) lädt Dubs, erstellt Whisper-Transkripte
und lädt alle Folgen hoch, für die in `episodes/<VIDEO-ID>.json` Texte stehen. Claude liefert diese Texte
und die Transkripte.

## Orte
- PC-Ordner (über die Geräte-Tools erreichbar): `S:\Downloads\Dub Downloader`
  - `state.json` → `downloads` = `{"<VIDEO-ID>:<sprache>": {video_id, language, title, file, ...}}`
  - Sprachordner `de-de`, `es-us`, `fr-fr`, `he`, `hi`, `id`, `it`, `ja`, `ko`, `ml`, `nl-nl`, `pa`, `pl`, `pt-br`, `ru`, `ta`, `te`, `uk`, `bn`, `ar` …
  - Pro Folge: `<Titel> [<sprache>].mp3`, `.json` (Metadaten), `.vtt` (Whisper-Transkript, sobald fertig)
  - `uploaded.json` → was schon auf Spreaker ist
- Repo: `Mirko-Peters/m365-dub-downloader`
  - `episodes/<VIDEO-ID>.json` → `{ "<lang>": {show, title, desc, tags, tr} }`
  - `transcripts/<lang>/<VIDEO-ID>.vtt`, öffentlich über `https://raw.githubusercontent.com/Mirko-Peters/m365-dub-downloader/main/transcripts/<lang>/<VIDEO-ID>.vtt`

## Sprach-Shows (Spreaker, Netzwerk 18613266)
de 7393187 · es 7393248 · fr 7393223 · it 7393231 · pt 7393243 · nl 7393222 · pl 7393242 · id 7393230 ·
ru 7393247 · uk 7393254 · ar 7393221 · he 7393227 · hi 7393228 · ja 7393232 · ko 7393236 · ml 7393238 ·
pa 7393244 · ta 7393250 · te 7393253. **Keine Show** für bn (und andere) → überspringen.
Sprachschlüssel im JSON = Basissprache (`de-de`→`de`, `es-us`→`es`, `pt-br`→`pt`, `nl-nl`→`nl`, `fr-fr`→`fr`).

## Ablauf pro Lauf
1. `state.json` vom PC holen (stage). Videos ermitteln, deren Sprachen noch keinen Eintrag in `episodes/<ID>.json` haben.
2. Pro Video das **deutsche** Transkript lesen (`de-de/<Titel> [de-de].vtt`). Gibt es das noch nicht → Video überspringen (kommt im nächsten Lauf).
3. Für **alle** Sprachen mit Show Titel + Beschreibung schreiben (siehe Stil) und in `episodes/<ID>.json` eintragen,
   `"tr": ""`, solange kein brauchbares Transkript im Repo liegt.
4. Alle neuen `.vtt` vom PC holen, auf Qualität prüfen (ersten Zeilen lesen: echter Text in der richtigen Sprache?
   Whisper liefert bei ml/pa/ta/te/bn oft Zeichensalat → dann NICHT veröffentlichen),
   brauchbare nach `transcripts/<lang>/<ID>.vtt` kopieren und im JSON `"tr"` auf die raw-URL setzen.
   (Der PC hängt Transkripte auch nachträglich an schon veröffentlichte Folgen.)
5. Commit + Push. Pro Lauf höchstens ~6 Videos, damit es sauber bleibt.

## Stil (vom Kanal-Inhaber freigegeben)
- **Titel** in der Landessprache, prägnant, SEO-stark, inhaltlich statt wörtlich übersetzt, max. 140 Zeichen,
  am Ende die Dub-Kennzeichnung:
  de (KI-Synchronfassung) · es (Doblaje IA) · fr (Doublage IA) · it (Doppiaggio IA) · pt (Dublagem IA) ·
  nl (AI-nasynchronisatie) · pl (Dubbing AI) · id (Sulih Suara AI) · ru (ИИ-дубляж) · uk (ШІ-дубляж) ·
  ar (دبلجة بالذكاء الاصطناعي) · he (דיבוב AI) · hi (AI डबिंग) · ja （AI吹き替え） · ko (AI 더빙) ·
  ml (AI ഡബ്ബിംഗ്) · pa (AI ਡਬਿੰਗ) · ta (AI டப்பிங்) · te (AI డబ్బింగ్)
- **Beschreibung** (HTML) in der Landessprache, Aufbau:
  1. Einstieg (2–3 Sätze): Problem/Nutzen der Folge, aus dem Transkript
  2. **„Das erfahren Sie:“** (lokalisiert) + 5 konkrete Punkte aus dem Inhalt
  3. Zielgruppe (1 Satz)
  4. Hinweis: „Diese Folge ist eine KI-synchronisierte <Sprache> Fassung des animierten Erklärvideos aus der M365 Show von Microsoft MVP Mirko Peters.“
  5. Links: ▶ Video `https://youtu.be/<ID>` · 🎧 `https://www.m365.fm` · 🎤 M365Con `https://m365con.net` · 💼 LinkedIn `https://www.linkedin.com/in/m365showpodcast/`
- **tags**: 5–7 kommagetrennte Stichworte.
- Fakten nur aus dem Transkript, nichts erfinden.
