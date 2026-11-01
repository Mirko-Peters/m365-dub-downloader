#!/usr/bin/env python3
"""Prueft die Shownotes-Vollfassungen shownotes/site/*.md (T26) ohne Seitenbau: Frontmatter lesbar, episode_id passt zum Dateinamen,
Hook/Kapitel/Takeaways vorhanden, FAQ erkannt (3 Fragen mit Antwort), Entitaets-Links nur auf www.m365.fm, Kapitelzeiten aufsteigend.
Aufruf: python tools/check_shownotes.py [datei ...]   (ohne Argument: alle). Exit 1, wenn eine Datei Fehler hat."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import site_shownotes as S


def check(path):
    errs, warns = [], []
    rec = S.parse_file(path)
    meta, body = rec["meta"], rec["body"]
    if not meta: warns.append("kein Frontmatter")
    if meta.get("episode_id") and str(meta["episode_id"]) != path.stem: errs.append(f"episode_id {meta['episode_id']} passt nicht zum Dateinamen {path.stem}")
    if not (meta.get("hook") or body): errs.append("weder hook noch Text")
    blocks = S.md_blocks(body)
    faq, rest = S._faq_from_blocks(blocks)
    if not faq: faq = [x for x in (meta.get("faq") or []) if isinstance(x, dict)]
    if len(faq) < 3: warns.append(f"nur {len(faq)} FAQ-Fragen erkannt (Vorgabe 3)")
    for x in faq:
        n = len(str(x.get("a") or "").split())
        if n and not 25 <= n <= 90: warns.append(f"FAQ-Antwort mit {n} Woertern (Vorgabe 40-60)")
    ch = S._chapters(meta)
    tl = [b for b in blocks if b[0] in ("ul", "ol") and any(S._TIME.match(x) for x in b[1])]
    if not ch and not tl: warns.append("keine Kapitel mit Zeitmarken")
    secs = [c.get("start_s", c.get("time_s")) for c in (meta.get("chapters") or []) if isinstance(c, dict)]
    secs = [s for s in secs if isinstance(s, (int, float))]
    if secs != sorted(secs): errs.append("Kapitelzeiten nicht aufsteigend")
    if not (meta.get("takeaways") or any(b[0] == "h" and re.search(r"takeaway|wichtigste", b[1][1], re.I) for b in blocks)): warns.append("keine Takeaways")
    for m in re.finditer(r"\]\((https?://[^\s)]+)\)", body):
        u = m.group(1)
        if not re.match(r"^https://www\.m365\.fm(/|$)", u): errs.append(f"Link nicht auf https://www.m365.fm: {u[:80]}")
    if re.search(r"<(script|iframe|img|style)\b", body, flags=re.I): errs.append("HTML-Einbettung im Text")
    return errs, warns


def main(args):
    files = [Path(a) for a in args] or sorted((ROOT / "shownotes" / "site").glob("*.md"))
    bad = 0
    for f in files:
        try:
            errs, warns = check(f)
        except Exception as e:
            errs, warns = [f"nicht lesbar: {e}"], []
        if errs: bad += 1
        if errs or warns: print(f"{f.name}: " + "; ".join(["FEHLER " + e for e in errs] + ["Hinweis " + w for w in warns]))
    print(f"{len(files)} Dateien, {bad} mit Fehlern")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
