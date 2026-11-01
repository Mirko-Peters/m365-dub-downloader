#!/usr/bin/env python3
"""Listet Uebersetzungen mit Ersatzzeichen (U+FFFD) oder Mojibake (Ticket T5): data/blog_i18n/<lang>/*.json.gz, data/podpage_i18n/*.json.
Ausgabe je Treffer: Datei, Schluessel/Position, Ausschnitt - Grundlage fuer die Neuuebersetzung (Vormerkliste in der Verwaltung)."""
import gzip, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from site_text import bad


def walk(o, path, out):
    if isinstance(o, str):
        if bad(o): out.append((path, o[:80].replace("\n", " ")))
    elif isinstance(o, dict):
        for k, v in o.items(): walk(v, f"{path}/{k}", out)
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, f"{path}[{i}]", out)


def main():
    hits = []
    for f in sorted((ROOT / "data" / "blog_i18n").rglob("*.json.gz")):
        walk(json.loads(gzip.open(f, "rt", encoding="utf-8").read()), str(f.relative_to(ROOT)), hits)
    for f in sorted((ROOT / "data" / "podpage_i18n").glob("*.json")):
        walk(json.loads(f.read_text("utf-8")), str(f.relative_to(ROOT)), hits)
    for p, t in hits[:200]: print(p, "|", t)
    print(len(hits), "Treffer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
