"""T25 Diagnose (nur lesend, ohne Token): Was sagt die Spreaker-Doku zu description/description_html beim Aktualisieren
einer Folge, und was liefert das oeffentliche Episoden-Objekt einer am 1.11. geschriebenen Folge? Bericht reports/spreaker-api.md"""
import html, json, re, sys, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PAGES = ["https://developers.spreaker.com/api/episodes/", "https://developers.spreaker.com/guides/upload-an-episode/"]
EPS = ["72933742", "74640221"]


def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "m365-site-bot"}), timeout=60) as r: return r.read().decode("utf-8", "replace")
    except Exception as e:
        return f"FEHLER {e}"


def text(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", "", h); h = re.sub(r"(?i)<br\s*/?>|</(p|li|tr|h\d|div|pre)>", "\n", h)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


L = ["# Spreaker-API: Beschreibung als HTML (Diagnose)", ""]
for u in PAGES:
    t = text(get(u)); L += [f"## {u}", ""]
    hits = [m.start() for m in re.finditer(r"(?i)description", t)]
    seen = set()
    for i in hits:
        a = max(0, i - 300); k = a // 400
        if k in seen: continue
        seen.add(k); L += ["```", t[a:i + 500].strip(), "```", ""]
        if len(seen) >= 14: break
for e in EPS:
    raw = get(f"https://api.spreaker.com/v2/episodes/{e}")
    try:
        ep = json.loads(raw)["response"]["episode"]
        L += [f"## Episode {e} (oeffentliches Objekt)", "", "Felder: " + ", ".join(sorted(ep.keys())), "",
              f"description ({len(ep.get('description') or '')} Zeichen): `{(ep.get('description') or '')[:300]}`", "",
              f"description_html ({len(ep.get('description_html') or '')} Zeichen): `{(ep.get('description_html') or '')[:600]}`", ""]
    except Exception as x:
        L += [f"## Episode {e}: {str(x)[:100]} {raw[:200]}", ""]
out = ROOT / "reports" / "spreaker-api.md"; out.parent.mkdir(parents=True, exist_ok=True); out.write_text("\n".join(L) + "\n", "utf-8")
print("\n".join(L)[:4000])
