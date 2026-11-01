#!/usr/bin/env python3
"""Prueft das erzeugte HTML (docs/) auf Mojibake (Ticket T5): "ÔÇ" (CP850) und "â€" (CP1252) sind Fehler (Exit 1); das Ersatzzeichen U+FFFD
und "Ã"-Folgen werden gezaehlt und mit den haeufigsten Dateien gemeldet (Hinweis, meist aus KI-Uebersetzungen; Liste fuer die Neuuebersetzung)."""
import re, sys
from collections import Counter
from pathlib import Path

DOCS = Path(__file__).parent / "docs"
HARD = re.compile("ÔÇ|â€")
SOFT = re.compile("�|Ã[\u0080-ÿ]")


def main():
    hard, soft, n = Counter(), Counter(), 0
    for p in DOCS.rglob("*.html"):
        n += 1
        try:
            h = p.read_text("utf-8")
        except UnicodeDecodeError:
            hard[str(p.relative_to(DOCS))] += 1; continue
        a, b = len(HARD.findall(h)), len(SOFT.findall(h))
        if a: hard[str(p.relative_to(DOCS))] += a
        if b: soft[str(p.relative_to(DOCS))] += b
    print(f"{n} Seiten geprueft: {sum(hard.values())} Mojibake-Treffer in {len(hard)} Dateien, {sum(soft.values())} U+FFFD/Ã-Treffer in {len(soft)} Dateien")
    for f, c in hard.most_common(20): print("FEHLER", c, "x", f)
    for f, c in soft.most_common(15): print("HINWEIS", c, "x", f)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
