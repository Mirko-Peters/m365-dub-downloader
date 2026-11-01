"""T25 Test an EINER Folge (schon betroffen, schlechter kann sie nicht werden): Welcher Weg speichert HTML samt Links bei
Spreaker? Varianten nacheinander, Abbruch beim ersten Erfolg (description_html enthaelt so viele <a> wie die Datei).
Bericht reports/spreaker-html-test.md. Aufruf: python tools/spreaker_html_test.py <episode_id>"""
import html, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_shownotes as A

ROOT = A.ROOT


def simple(h):
    """Nur Tags, die Spreaker in den alten Beschreibungen hatte: <a>, <strong>, <br>. Absaetze -> <br><br>, Listen -> • Zeilen."""
    h = re.sub(r"(?is)<li[^>]*>", "• ", h); h = re.sub(r"(?is)</li>\s*", "<br>", h)
    h = re.sub(r"(?is)</?ul[^>]*>", "", h); h = re.sub(r"(?is)<p[^>]*>", "", h); h = re.sub(r"(?is)</p>\s*", "<br><br>", h)
    return re.sub(r"(<br>\s*){3,}", "<br><br>", h).strip()


def main():
    eid = int(sys.argv[1]) if len(sys.argv) > 1 else 72933742
    raw = (ROOT / "shownotes" / "spreaker" / f"{eid}.html").read_text("utf-8").strip()
    want = len(re.findall(r"<a\s", raw))
    sp = A.Spreaker()
    if not sp.login(): return 1
    L = [f"# Spreaker-HTML-Test an Folge {eid} ({A.now()})", "", f"Datei: {len(raw)} Zeichen, {want} Links", ""]
    variants = [("description_html = Spreaker-Fassung (<p> -> <br>, <strong> -> <b>)", {"description_html": A.spreaker_html(raw)}),
                ("description_html = Datei", {"description_html": raw}),
                ("description = vereinfacht (<a>, <strong>, <br>)", {"description": simple(raw)}),
                ("description_html = vereinfacht", {"description_html": simple(raw)})]
    ok = False
    for name, data in variants:
        try:
            sp.req("POST", f"/episodes/{eid}", data=data); time.sleep(2)
            ep = sp.req("GET", f"/episodes/{eid}")["episode"]
            dh = ep.get("description_html") or ""
            got = len(re.findall(r"<a\s", dh))
            L += [f"## {name}", "", f"description_html: {len(dh)} Zeichen, {got} Links, <strong>: {dh.count('<strong')}, <b>: {dh.count('<b>')}, <br>: {dh.count('<br')}, <li>: {dh.count('<li')}, <p>: {dh.count('<p')}", "",
                  "```html", dh[:900], "```", ""]
            if got >= want > 0:
                ok = True; L += [f"**Erfolg mit: {name}**", ""]; break
        except Exception as e:
            L += [f"## {name}", "", f"Fehler: {str(e)[:200]}", ""]
    if not ok: L += ["**Kein Weg hat die Links erhalten.**", ""]
    out = ROOT / "reports" / "spreaker-html-test.md"; out.parent.mkdir(parents=True, exist_ok=True); out.write_text("\n".join(L) + "\n", "utf-8")
    print("\n".join(L)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
