"""Nur lesen: misst die Cache-Header der Seite (www.m365.fm, img.m365.fm), liest die Cache-Einstellungen der Cloudflare-Zone
und den Traffic der letzten 30 Tage (fuer Kostenschaetzungen wie Argo). Gibt keine Secrets und keine Zonen-ID aus.
Aufruf: python tools/cache_check.py  (Umgebung: CLOUDFLARE_API_TOKEN, CF_ZONE_ID optional)"""
import datetime as dt, json, os, re, time, urllib.error, urllib.request

B = "https://www.m365.fm"
URLS = [
    ("Startseite (GitHub Pages)", B + "/"),
    ("Folgenliste", B + "/show/episodes/"),
    ("Folge en", B + "/show/episodes/internal-developer-platforms/"),
    ("Folge pl (R2)", B + "/pl/show/episodes/internal-developer-platforms/"),
    ("Blog pl (R2)", B + "/pl/community/u/mirko-p/blog/how-to-generate-a-microsoft-purview-role-group-report-with-powershell/"),
    ("Entitaet", B + "/entity/copilot/"),
    ("Entitaet de", B + "/de/entity/copilot/"),
    ("CSS mit Hash", None),
    ("CSS a11y", B + "/assets/a11y.css"),
    ("JS page", B + "/assets/page.js"),
    ("Schrift", B + "/assets/fonts/barlow-latin-400-normal.woff2"),
    ("OG-Bild", B + "/og/index.png"),
    ("Icon", B + "/assets/apple-touch-icon.png"),
    ("Sitemap", B + "/sitemap.xml"),
    ("llms.txt", B + "/llms.txt"),
    ("R2-Bild", "https://img.m365.fm/i/5254f600109b589b2c2d.webp"),
    ("404", B + "/gibt-es-nicht-cache-check/"),
]
KEEP = ("cache-control", "cf-cache-status", "age", "etag", "last-modified", "expires", "vary", "content-encoding", "content-type", "server", "x-cache", "alt-svc", "x-robots-tag")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None


OPEN = urllib.request.build_opener(NoRedirect)


def get(url, extra=None):
    h = {"User-Agent": "Mozilla/5.0 (M365.FM cache-check)", "Accept": "text/html,*/*", "Accept-Encoding": "br, gzip"}
    h.update(extra or {})
    t = time.perf_counter()
    try: r = OPEN.open(urllib.request.Request(url, headers=h), timeout=30)
    except urllib.error.HTTPError as e: r = e
    ttfb = (time.perf_counter() - t) * 1000
    body = r.read(); total = (time.perf_counter() - t) * 1000
    return getattr(r, "status", None) or r.code, {k.lower(): v for k, v in r.headers.items()}, ttfb, total, len(body), body


def css_url():
    try:
        html = get(B + "/", {"Accept-Encoding": "identity"})[5].decode("utf-8", "replace")
        m = re.search(r'href="(https://www\.m365\.fm/assets/site\.[0-9a-f]+\.css)"', html)
        return m.group(1) if m else None
    except Exception: return None


print("## Cache-Messung (je Adresse 3 Abrufe im Abstand von 1 s, dann ein bedingter Abruf)\n")
for name, url in URLS:
    if url is None: url = css_url()
    if not url: print(f"### {name}: nicht gefunden\n"); continue
    print(f"### {name}\n`{url}`\n")
    first = None
    for i in range(3):
        try: st, hd, ttfb, total, n, _b = get(url)
        except Exception as e: print(f"- Abruf {i + 1}: Fehler {type(e).__name__}: {str(e)[:120]}"); continue
        first = first or hd
        print(f"- Abruf {i + 1}: HTTP {st}, TTFB {ttfb:.0f} ms, gesamt {total:.0f} ms, {n} Bytes, cf-cache-status={hd.get('cf-cache-status', '-')}, age={hd.get('age', '-')}")
        time.sleep(1)
    if first:
        for k in KEEP:
            if k in first: print(f"  - `{k}: {first[k][:160]}`")
        cond = {}
        if first.get("etag"): cond["If-None-Match"] = first["etag"]
        if first.get("last-modified"): cond["If-Modified-Since"] = first["last-modified"]
        if cond:
            try: st, hd, ttfb, total, n, _b = get(url, cond); print(f"- bedingter Abruf ({', '.join(cond)}): HTTP {st}, {n} Bytes")
            except Exception as e: print(f"- bedingter Abruf: Fehler {type(e).__name__}")
        else: print("- bedingter Abruf: weder ETag noch Last-Modified vorhanden")
    print()

print("## Cloudflare-Zone (nur lesen)\n")
tok = os.environ.get("CLOUDFLARE_API_TOKEN", "")
if not tok:
    print("Kein CLOUDFLARE_API_TOKEN - Zone nicht gelesen"); raise SystemExit(0)


def cf(path, body=None):
    hdr = {"Authorization": "Bearer " + tok, "Content-Type": "application/json"}
    req = urllib.request.Request("https://api.cloudflare.com/client/v4" + path, json.dumps(body).encode() if body else None, hdr, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return 200, json.load(r)
    except urllib.error.HTTPError as e:
        try: d = json.load(e)
        except Exception: d = {}
        return e.code, d
    except Exception as e:
        return 0, {"errors": [{"message": type(e).__name__}]}


def err(d): return [e.get("message") for e in (d.get("errors") or [])][:1]


zone = os.environ.get("CF_ZONE_ID", "")
if not zone:
    st, d = cf("/zones?name=m365.fm"); zone = ((d.get("result") or [{}])[0]).get("id", "")
if not zone: print("Zone nicht gefunden (Token ohne Zone:Read?)"); raise SystemExit(0)
st, d = cf(f"/zones/{zone}")
print(f"- Zone: HTTP {st}, Tarif: {((d.get('result') or {}).get('plan') or {}).get('name', '?')}")
st, d = cf(f"/zones/{zone}/settings")
WANT = ("cache_level", "browser_cache_ttl", "always_online", "early_hints", "http3", "0rtt", "brotli", "rocket_loader", "polish", "mirage", "minify",
        "development_mode", "sort_query_string_for_cache", "crawler_hints", "speed_brain", "fonts", "h2_prioritization", "image_resizing", "webp",
        "always_use_https", "automatic_https_rewrites", "min_tls_version", "tls_1_3", "ssl", "cache_deception_armor", "opportunistic_encryption")
if st == 200:
    for s in d.get("result") or []:
        if s.get("id") in WANT: print(f"  - `{s['id']}` = `{json.dumps(s.get('value'))[:80]}`" + ("" if s.get("editable", True) else " (im Tarif nicht aenderbar)"))
else:
    print(f"  - Einstellungen nicht lesbar: HTTP {st} {err(d)} (Token braucht 'Zone Settings: Read')")
for label, path in (("Smart Tiered Cache", f"/zones/{zone}/cache/tiered_cache_smart_topology_enable"), ("Tiered Caching", f"/zones/{zone}/argo/tiered_caching"),
                    ("Argo Smart Routing", f"/zones/{zone}/argo/smart_routing"), ("Cache Reserve", f"/zones/{zone}/cache/cache_reserve"),
                    ("Regional Tiered Cache", f"/zones/{zone}/cache/regional_tiered_cache")):
    st, d = cf(path); print(f"- {label}: HTTP {st}, Wert {json.dumps((d.get('result') or {}).get('value'))}" + ("" if st == 200 else f" {err(d)}"))
st, d = cf(f"/zones/{zone}/rulesets/phases/http_request_cache_settings/entrypoint")
rules = (d.get("result") or {}).get("rules") or []
print(f"- Cache Rules: HTTP {st}, {len(rules)} Regeln" + ("" if st in (200, 404) else f" {err(d)}"))
for r in rules: print(f"  - {r.get('description') or '-'}: `{r.get('expression', '')[:140]}` -> {json.dumps(r.get('action_parameters', {}))[:200]}")
st, d = cf(f"/zones/{zone}/pagerules")
pr = d.get("result") or []
print(f"- Page Rules: HTTP {st}, {len(pr)} Regeln" + ("" if st == 200 else f" {err(d)}"))
for r in pr: print(f"  - {[t.get('constraint', {}).get('value') for t in r.get('targets', [])]} -> {[str(a.get('id')) + '=' + str(a.get('value')) for a in r.get('actions', [])]} ({r.get('status')})")
st, d = cf(f"/zones/{zone}/workers/routes")
print(f"- Worker-Routen: HTTP {st}, {[str(x.get('pattern')) + ' -> ' + str(x.get('script')) for x in (d.get('result') or [])]}")

print("\n## Traffic der letzten 30 Tage (GraphQL Analytics, nur lesen)\n")
until = dt.date.today(); since = until - dt.timedelta(days=29)
Q = """query($z:String!,$s:Date!,$u:Date!){viewer{zones(filter:{zoneTag:$z}){httpRequests1dGroups(limit:31,orderBy:[date_ASC],filter:{date_geq:$s,date_leq:$u}){
dimensions{date} sum{requests cachedRequests bytes cachedBytes pageViews} uniq{uniques}}}}}"""
st, d = cf("/graphql", {"query": Q, "variables": {"z": zone, "s": since.isoformat(), "u": until.isoformat()}})
if st != 200 or d.get("errors"):
    print(f"Analytics nicht lesbar: HTTP {st} {[e.get('message') for e in (d.get('errors') or [])][:1]} (Token braucht 'Analytics: Read')")
else:
    rows = (((d.get("data") or {}).get("viewer") or {}).get("zones") or [{}])[0].get("httpRequests1dGroups") or []
    T = {"requests": 0, "cachedRequests": 0, "bytes": 0, "cachedBytes": 0, "pageViews": 0}
    for r in rows:
        for k in T: T[k] += r["sum"].get(k) or 0
    gb = lambda b: b / 1e9
    days = max(len(rows), 1)
    print(f"- {days} Tage, Anfragen {T['requests']:,}, davon aus dem Cache {T['cachedRequests']:,} ({T['cachedRequests'] / max(T['requests'], 1):.1%})")
    print(f"- Datenmenge {gb(T['bytes']):.2f} GB, davon aus dem Cache {gb(T['cachedBytes']):.2f} GB ({T['cachedBytes'] / max(T['bytes'], 1):.1%}), ungecacht {gb(T['bytes'] - T['cachedBytes']):.2f} GB")
    print(f"- Seitenaufrufe {T['pageViews']:,}, Besucher je Tag im Mittel {sum((r.get('uniq') or {}).get('uniques') or 0 for r in rows) / days:,.0f}")
    per30 = 30 / days
    allgb, uncgb = gb(T["bytes"]) * per30, gb(T["bytes"] - T["cachedBytes"]) * per30
    print(f"- Argo-Schaetzung (5 USD Grundgebuehr inkl. 1 GB, dann 0,10 USD/GB; Listenpreis, bitte im Dashboard bestaetigen):")
    print(f"  - falls nach gesamter Auslieferung abgerechnet: {5 + max(allgb - 1, 0) * 0.10:.2f} USD/Monat ({allgb:.1f} GB)")
    print(f"  - falls nur ungecachter Verkehr zaehlt: {5 + max(uncgb - 1, 0) * 0.10:.2f} USD/Monat ({uncgb:.1f} GB)")
    print("\n| Tag | Anfragen | Cache-Quote | GB |\n|---|---|---|---|")
    for r in rows:
        s = r["sum"]; print(f"| {r['dimensions']['date']} | {s['requests']:,} | {s['cachedRequests'] / max(s['requests'], 1):.0%} | {gb(s['bytes']):.2f} |")
