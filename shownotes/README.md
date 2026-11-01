# shownotes/ – Entitäten-Extraktion aus Transkripten (Ticket T23)

Hier liegen die von der Content-KI erzeugten Extraktionen je Episode. Sie sind Arbeitsmaterial (Status „review“)
und werden noch nicht automatisch in die Seite eingebaut – wie sie auf m365.fm landen, entscheidet Mirko.

## Datenquellen
- Episodenliste Hauptshow (Spreaker 6704921): `data/en_episodes.json` (Schlüssel = normalisierter Titel,
  Felder `spreaker_id`, `title`, `duration`, `pub`, `transcript`) und `data/show_notes/en.json` (Show-Notes-Text, Link).
  Öffentlich auch unter https://www.m365.fm/episodes.json.
- Transkripte: `data/en_transcripts/<transcript>.txt` (Fließtext, nur vereinzelt `HH:MM:SS`-Zeitmarken).
- Meistgehörte: `data/top.json` → `langs.en[]` (`episode_id`, `score`).
- Entitäten-Stammdaten: `data/entities.json`, `data/guest_entities.json`, `data/speaker_entities.json`
  (Feld `id` = slug, `name`, `aliases`, `type`). Entity-Seiten: `https://www.m365.fm/entity/<slug>/`.

## Dateien
- `shownotes/entities/<spreaker_episode_id>.json` – eine Datei je Episode:
  `episode_id, slug, title, lang, duration_s, transcript_source, time_basis, entities[], new_entities[], quotes[],
  chapters[], takeaways[], hook, youtube_video_id, generated_at`.
  - `entities[]`: `slug, name, type, score (0–100), mentions, first_mention_s, quote (≤ 120 Zeichen), url`.
    Rangfolge Personen > Konzepte > Tools/Produkte.
  - `quotes[]`: 3–5 wörtliche Zitate (15–45 Wörter) mit `text, speaker, speaker_slug, time_s, entities, why`;
    nur mit eindeutig benanntem Sprecher (an die Personen-Entität gebunden), sonst leer. Keine eigenen Quote-Entitäten.
  - `time_basis: "estimated"` – Zeitmarken sind aus der Wortposition geschätzt (linear zwischen den echten
    `HH:MM:SS`-Ankern im Transkript bzw. Anfang/Ende), also ungefähre Werte.
- `imports/entities/<slug>.json` – Vorschläge für fehlende Entitäten (`status: "review"`, `evidence[]` je Episode).

## Arbeitsteilung
- Agent A: Hauptshow, gerade Spreaker-ID · Agent B: Hauptshow, ungerade ID · dritter Agent: die 14 Sprach-Shows.
- Episoden mit vorhandener vollständiger Datei (mit `quotes[]`) werden nicht erneut angefasst.
