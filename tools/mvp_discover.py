"""T31 Erkundung MVP-Verzeichnis (einmalig, workflow_dispatch): Welche Schnittstelle laedt die Suche auf
https://mvp.microsoft.com/en-US/search?target=Profile&program=MVP, was erlauben robots.txt und die Nutzungsbedingungen?
Schreibt nur Technik in reports/mvp-discovery.md/.json: Endpunkte, Methoden, Parameter, Antwortstruktur (Schluessel, Typen,
Gesamtzahl), keine Namen, Profile, Fotos oder andere Personendaten."""
import json, re, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "mvp-discovery"
URL = "https://mvp.microsoft.com/en-US/search?target=Profile&program=MVP"
UA = {"User-Agent": "Mozilla/5.0 (compatible; M365FM-discovery/1.0; +https://www.m365.fm/)"}


def shape(v, depth=0):
    """Struktur ohne Werte: Schluessel und Typen, Listen nur mit Laenge und Form des ersten Elements."""
    if depth > 4: return "…"
    if isinstance(v, dict): return {k: shape(x, depth + 1) for k, x in list(v.items())[:40]}
    if isinstance(v, list): return {"list": len(v), "item": shape(v[0], depth + 1) if v else None}
    if isinstance(v, (int, float)) and not isinstance(v, bool): return "number" if depth > 1 else v   # Zaehler auf oberster Ebene behalten (z. B. totalCount)
    return type(v).__name__


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", -1), str(e)[:200]


def main():
    rep = {"generated": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()), "page": URL, "requests": []}
    rep["robots_status"], rep["robots"] = get("https://mvp.microsoft.com/robots.txt")
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(user_agent=UA["User-Agent"])
        def on_resp(r):
            req = r.request
            if req.resource_type not in ("xhr", "fetch"): return
            ent = {"method": req.method, "url": re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<id>", re.sub(r"[?#].*$", "", r.url), flags=re.I), "query": sorted(set(re.findall(r"[?&]([^=&]+)=", r.url))), "status": r.status,
                   "type": (r.headers or {}).get("content-type", ""), "post_keys": []}
            try:
                if req.post_data: ent["post_keys"] = shape(json.loads(req.post_data))
            except Exception: ent["post_keys"] = "nicht JSON"
            try:
                if "json" in ent["type"]:
                    j = r.json(); ent["response_shape"] = shape(j)
                    if not rep.get("_pid") and isinstance(j, dict):   # erste Profilkennung merken (nur zur Navigation, nicht im Bericht)
                        for it in (j.get("communityLeaderProfiles") or [])[:1]: rep["_pid"] = it.get("userProfileIdentifier")
            except Exception: pass
            rep["requests"].append(ent)
        pg.on("response", on_resp)
        pg.goto(URL, wait_until="networkidle", timeout=90000); pg.wait_for_timeout(4000)
        pg.mouse.wheel(0, 4000); pg.wait_for_timeout(3000)   # Nachladen beim Scrollen / naechste Seite
        links = pg.eval_on_selector_all("a[href]", "els => els.map(e => [e.textContent.trim().slice(0,60), e.href])")
        rep["terms_links"] = sorted({h for t, h in links if re.search(r"terms|privacy|legal|nutzungs|datenschutz", t + h, re.I)})[:10]
        rep["profile_link_pattern"] = sorted({re.sub(r"[0-9a-f]{8}-[0-9a-f-]{27}", "<id>", h) for _, h in links if "/profile/" in h.lower()})[:5]
        rep["profile_links_on_first_page"] = sum(1 for _, h in links if "/profile/" in h.lower())
        # T33: ein Profil oeffnen (erste Kennung aus der Suche), um die Detail-Schnittstelle zu sehen (Award-Kategorien usw.)
        pid = rep.get("_pid")
        if pid:
            n0 = len(rep["requests"])
            pg.goto(f"https://mvp.microsoft.com/en-US/MVP/profile/{pid}", wait_until="networkidle", timeout=90000); pg.wait_for_timeout(4000)
            rep["profile_requests"] = [r for r in rep["requests"][n0:] if "mavenapi" in r["url"] or "/api/" in r["url"]]
        rep.pop("_pid", None)
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_suffix(".json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", "utf-8")
    L = [f"# Erkundung MVP-Verzeichnis ({rep['generated']})", "", f"Seite: {URL}", "", f"robots.txt (Status {rep['robots_status']}):", "", "```", rep["robots"][:3000], "```", "",
         f"Profil-Links auf der ersten Seite: {rep['profile_links_on_first_page']} · Muster: {', '.join(rep['profile_link_pattern']) or '-'}", "",
         "Nutzungsbedingungen / Datenschutz: " + (", ".join(rep["terms_links"]) or "-"), "", "## Abrufe der Seite (XHR/fetch)", ""]
    for r in rep.get("profile_requests", []):
        L += [f"- PROFIL `{r['method']} {r['url']}` → {r['status']} {r['type']}" + (f" · Parameter: {', '.join(r['query'])}" if r["query"] else ""),
              *( [f"  - Antwort: `{json.dumps(r.get('response_shape'), ensure_ascii=False)[:1500]}`"] if r.get("response_shape") else [])]
    L += ["", "## Abrufe der Suchseite", ""]
    for r in rep["requests"]:
        L += [f"- `{r['method']} {r['url']}` → {r['status']} {r['type']}" + (f" · Parameter: {', '.join(r['query'])}" if r["query"] else ""),
              *( [f"  - Anfrage: `{json.dumps(r['post_keys'], ensure_ascii=False)[:600]}`"] if r["post_keys"] else []),
              *( [f"  - Antwort: `{json.dumps(r.get('response_shape'), ensure_ascii=False)[:900]}`"] if r.get("response_shape") else [])]
    OUT.with_suffix(".md").write_text("\n".join(L) + "\n", "utf-8")
    print("\n".join(L[:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
