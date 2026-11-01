#!/usr/bin/env python3
"""T14: Pruefbericht zur Podpage-Migration gegen die Live-Seite. Jede fruehere Podpage-Adresse (Blog /blog/<slug>, Folgen /<slug>,
Gaeste /guests/<slug>, Seiten, Listen) muss mit genau einer 301 auf ein Ziel zeigen, das mit 200 antwortet. Fuer eine Stichprobe von
Blogbeitraegen (Standard 50) wird die Zielseite genauer geprueft: Titel, Canonical = Ziel, kein noindex, H1, BlogPosting-Schema, Autor,
Wortzahl gegenueber dem Original und Bilder nur von eigenen Hosts (img.m365.fm/www.m365.fm, Spreaker-CloudFront erlaubt).
Ausgabe: reports/migration-check.md und .json. Aufruf: python tools/check_migration.py [--sample 50] [--limit 0] [--base https://www.m365.fm]
Nur lesende GET-Anfragen, hoechstens 6 parallel."""
import argparse, gzip, json, random, re, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
PD = ROOT / "data" / "podpage"
UA = {"User-Agent": "m365fm-migration-check/1.0 (+https://www.m365.fm/)"}
OWN_IMG = ("img.m365.fm", "www.m365.fm", "m365.fm", "api-dub.m365.fm", "d3wo5wojvuv7l.cloudfront.net")   # api-dub: eigene Community-API (Bilder-Proxy)   # Spreaker-Folgenbilder bleiben vorerst auf CloudFront (CLAUDE.md)
SKIPP = {"episodes", "blog", "reviews", "podroll", "courses", "store", "videos", "guests", "people", "sponsors", "contact", "join", "leave_review", "rate",
         "guest_intake", "newsletter", "follow", "voicemail"}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None


OPEN = urllib.request.build_opener(NoRedirect)


def load(name):
    p = PD / f"{name}.json.gz"
    if p.exists(): return json.loads(gzip.decompress(p.read_bytes()).decode("utf-8"))
    p = PD / f"{name}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else []


def get(url, body=False):
    """-> (status, location, html). Folgt keiner Weiterleitung."""
    for attempt in range(3):
        try:
            with OPEN.open(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.status, r.headers.get("location") or "", (r.read().decode("utf-8", "replace") if body else "")
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 307, 308): return e.code, e.headers.get("location") or "", ""
            if e.code in (429, 503) and attempt < 2: time.sleep(2 + 3 * attempt); continue
            return e.code, "", ""
        except Exception as e:
            if attempt < 2: time.sleep(2); continue
            return 0, str(e)[:80], ""


def follow(base, path, body=False):
    """Folgt bis zu 4 Weiterleitungen. -> dict(path, hops, chain, status, final, html)"""
    url, chain = base + path, []
    for _ in range(5):
        st, loc, h = get(url, body)
        chain.append(st)
        if st in (301, 302, 307, 308) and loc:
            url = urljoin(url, loc); continue
        return {"path": path, "hops": len(chain) - 1, "chain": chain, "status": st, "final": url, "html": h}
    return {"path": path, "hops": len(chain) - 1, "chain": chain, "status": -1, "final": url, "html": ""}


def legacy_paths():
    """(Art, alter Pfad, Datensatz) fuer alles, was es auf Podpage gab."""
    out = []
    for p in load("blog_posts"): out.append(("blog", f"/blog/{p['slug']}/", p))
    for e in load("episodes"):
        if e.get("published") not in (False, "False") and e.get("hidden") not in (True, "True"): out.append(("episode", f"/{e['slug']}/", e))
    for g in load("guests"):
        if g.get("hidden") not in (True, "True"): out.append(("guest", f"/guests/{g['slug']}/", g))
    for pg in load("pages"):
        if pg.get("slug") and pg["slug"] not in SKIPP: out.append(("page", f"/{pg['slug']}/", pg))
    for x in ("episodes", "guests", "blog", "reviews", "sponsors", "hosts", "contact", "follow", "newsletter", "videos"): out.append(("list", f"/{x}/", {}))
    return out


def detail(r, post):
    """Inhaltspruefung einer Blog-Zielseite."""
    h, issues = r["html"], []
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    if not t or not t.group(1).strip(): issues.append("Titel fehlt")
    c = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    if not c: issues.append("Canonical fehlt")
    elif c.group(1).rstrip("/") != r["final"].rstrip("/"): issues.append(f"Canonical zeigt woanders hin ({urlparse(c.group(1)).path})")
    if re.search(r'<meta name="robots" content="[^"]*noindex', h): issues.append("noindex")
    if "<h1" not in h: issues.append("H1 fehlt")
    if '"BlogPosting"' not in h and '"Article"' not in h: issues.append("kein BlogPosting-Schema")
    if '"author"' not in h: issues.append("kein Autor im Schema")
    main = h.split("<main", 1)[-1].split("</main>", 1)[0]
    words = len(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", main, flags=re.S)).split())
    want = int(str(post.get("words") or "0") or 0)
    if want and words < 0.8 * want: issues.append(f"Text kuerzer ({words} statt ~{want} Woerter)")
    hosts = {urlparse(urljoin(r["final"], s)).netloc for s in re.findall(r'<img[^>]+src="([^"]+)"', main)}
    bad = sorted(x for x in hosts if x and x not in OWN_IMG)
    if bad: issues.append("fremde Bilder: " + ", ".join(bad[:3]))
    return {"path": r["path"], "final": urlparse(r["final"]).path, "words": words, "want": want, "issues": issues}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://www.m365.fm")
    ap.add_argument("--sample", type=int, default=50)
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N Adressen (0 = alle)")
    ap.add_argument("--out", default=str(ROOT / "reports" / "migration-check"))
    a = ap.parse_args()
    items = legacy_paths()
    if a.limit: items = items[: a.limit]
    t0 = time.time()
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda it: follow(a.base, it[1]), items))
    blog = [(r, it[2]) for r, it in zip(res, items) if it[0] == "blog" and r["status"] == 200]
    rnd = random.Random(time.strftime("%Y-%m-%d"))
    sample = rnd.sample(blog, min(a.sample, len(blog)))
    with ThreadPoolExecutor(6) as ex:
        det = list(ex.map(lambda rp: detail(follow(a.base, rp[0]["path"], body=True), rp[1]), sample))
    kinds = {}
    for r, it in zip(res, items):
        k = kinds.setdefault(it[0], {"gesamt": 0, "ok": 0, "zwei_oder_mehr_301": 0, "ohne_301": 0, "fehler": 0})
        k["gesamt"] += 1
        if r["status"] != 200: k["fehler"] += 1
        elif r["hops"] == 0: k["ohne_301"] += 1
        elif r["hops"] > 1: k["zwei_oder_mehr_301"] += 1
        else: k["ok"] += 1
    fails = [{"art": it[0], "pfad": r["path"], "kette": r["chain"], "ziel": urlparse(r["final"]).path} for r, it in zip(res, items) if r["status"] != 200 or r["hops"] > 1]
    # alte Adressen ueber dub.m365.fm: muessen ebenfalls in einem Schritt am Ziel ankommen
    dub = [it for it in items if it[0] in ("blog", "episode")][:20]
    if dub and "www.m365.fm" in a.base:
        with ThreadPoolExecutor(6) as ex:
            dres = list(ex.map(lambda it: follow(a.base.replace("www.m365.fm", "dub.m365.fm"), it[1]), dub))
        try:   # wer antwortet auf dub.m365.fm? Cloudflare (Worker aktiv) oder GitHub Pages (DNS-Eintrag nicht proxied)
            with OPEN.open(urllib.request.Request(a.base.replace("www.m365.fm", "dub.m365.fm") + dub[0][1], headers=UA), timeout=30) as r: hdr = r.headers
        except urllib.error.HTTPError as e:
            hdr = e.headers
        except Exception:
            hdr = {}
        dub_server = f"server={(hdr or {}).get('server', '?')}, cf-ray={'ja' if (hdr or {}).get('cf-ray') else 'nein'}"
        k = kinds.setdefault("dub-host", {"gesamt": 0, "ok": 0, "zwei_oder_mehr_301": 0, "ohne_301": 0, "fehler": 0})
        for r, it in zip(dres, dub):
            k["gesamt"] += 1
            if r["status"] != 200: k["fehler"] += 1
            elif r["hops"] > 1: k["zwei_oder_mehr_301"] += 1
            else: k["ok"] += 1
            if r["status"] != 200 or r["hops"] > 1: fails.append({"art": "dub-host", "pfad": r["path"], "kette": r["chain"], "ziel": urlparse(r["final"]).path})
    rep = {"generated": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()), "base": a.base, "seconds": round(time.time() - t0), "kinds": kinds, "dub_server": locals().get("dub_server", ""),
           "failures": fails, "sample": det, "sample_ok": sum(1 for d in det if not d["issues"])}
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", "utf-8")
    L = [f"# Prüfbericht Podpage-Migration ({rep['generated']})", "", f"Geprüft gegen {a.base}: {len(items)} frühere Adressen in {rep['seconds']} s.", "",
         "| Art | gesamt | genau eine 301 auf 200 | 200 ohne 301 | mehrere 301 | Fehler |", "|---|---|---|---|---|---|"]
    for k, v in kinds.items(): L.append(f"| {k} | {v['gesamt']} | {v['ok']} | {v['ohne_301']} | {v['zwei_oder_mehr_301']} | {v['fehler']} |")
    if rep["dub_server"]: L += ["", f"Antwort auf dub.m365.fm: {rep['dub_server']}"]
    L += ["", f"Stichprobe Blog: {rep['sample_ok']} von {len(det)} Beiträgen ohne Befund.", ""]
    if any(d["issues"] for d in det):
        L += ["| alter Pfad | Ziel | Befund |", "|---|---|---|"] + [f"| {d['path']} | {d['final']} | {'; '.join(d['issues'])} |" for d in det if d["issues"]]
    if fails:
        L += ["", f"## Adressen mit Abweichung ({len(fails)}, erste 100)", "", "| Art | alter Pfad | Statusfolge | Ziel |", "|---|---|---|---|"]
        L += [f"| {f['art']} | {f['pfad']} | {' → '.join(map(str, f['kette']))} | {f['ziel']} |" for f in fails[:100]]
    out.with_suffix(".md").write_text("\n".join(L) + "\n", "utf-8")
    print("\n".join(L[:12 + len(kinds)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
