# imports/blog/ – Content-Pakete für den Blog (Ticket T15)

Ein Beitrag ist eine Datei `imports/blog/<sprache>/<slug>.md`, z. B. `imports/blog/de/copilot-lizenzen-richtig-planen.md`.
Der Seitenbau prüft jede Datei, rendert sie und veröffentlicht freigegebene Pakete unter `/blog-content/index.json`.
Der Worker-Cron `importContentBlog` legt sie als Community-Beitrag des Autors in der Datenbank an.

## Kopf (YAML)

```yaml
---
title: Copilot-Lizenzen richtig planen           # 10–140 Zeichen
summary: Wie Sie Lizenzen nach Rollen planen …    # 50–300 Zeichen
status: review                                   # review = liegt, approved = wird übernommen
publish: false                                   # false = wartet in der Verwaltung (Blog-Prüfung), true = sofort live
author: mirko-p                                  # Profil-Handle, Standard mirko-p
date: 2026-11-01
topics: [microsoft-365-copilot, copilot-studio]  # Entitäts-IDs (müssen existieren)
faq:
  - q: Brauche ich für jeden Nutzer eine Lizenz?
    a: Nein …
---
```

## Text (Markdown)

`##`-Überschriften, Absätze, Listen, `**fett**`, `*kursiv*`, `` `code` ``, `[Link](https://…)` und Bilder
`![Alt](https://img.m365.fm/…)`. Mindestens 300 Wörter. Bilder nur aus dem eigenen Bucket (`img.m365.fm`).
Kein HTML mit `script`, `iframe`, `style` oder `form`.

## Ablauf

1. Paket mit `status: review` anlegen.
2. QA prüft und setzt `status: approved` (optional `publish: true`).
3. Nach dem nächsten Seitenbau übernimmt der Worker das Paket (bis 40 je Lauf). Ohne `publish` erscheint es in der
   Verwaltung unter Blog-Prüfung und geht mit der Freigabe live.
4. Spätere Änderungen am Paket erneuern den Beitrag nur, solange ihn niemand im Editor oder in der Verwaltung geändert hat.

Fehler stehen im Build-Log („Content-Pakete Blog“) und in `/blog-content/report.json`. Nichts wird gelöscht:
Ein Paket, das aus dem Ordner verschwindet, lässt den Beitrag unverändert.
