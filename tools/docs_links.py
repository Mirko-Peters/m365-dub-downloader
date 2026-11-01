#!/usr/bin/env python3
"""T13: offizielle Dokumentations-Links (sameAs) fuer Entitaeten ohne jede Quelle. Kandidaten stehen in CAND; jeder wird live geprueft:
Status 200 nach hoechstens 5 Weiterleitungen, Ziel-Host in der Allowlist, kein Such- oder Fehlerpfad. Nur dann wird das Feld (docs oder web)
gesetzt, und nur wenn die Entitaet dort noch nichts hat. Bericht: data/docs_links_report.json. Aufruf: python tools/docs_links.py [--apply]"""
import json, re, sys, time, urllib.error, urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "entities.json"
UA = {"User-Agent": "m365fm-entity-bot/1.0 (+https://www.m365.fm/)"}
OK_HOSTS = {"learn.microsoft.com", "docs.github.com", "openai.com"}
CAND = {   # Entitaet -> (Feld, URL); nur Produkte/Plattformen, deren Dokumentationsseite eindeutig ist
    "azure-ai-foundry": ("docs", "https://learn.microsoft.com/en-us/azure/ai-foundry/"),
    "purview": ("docs", "https://learn.microsoft.com/en-us/purview/"),
    "graph": ("docs", "https://learn.microsoft.com/en-us/graph/"),
    "viva": ("docs", "https://learn.microsoft.com/en-us/viva/"),
    "chatgpt": ("web", "https://openai.com/chatgpt/"),
    "azure-api-management": ("docs", "https://learn.microsoft.com/en-us/azure/api-management/"),
    "azure-ai-search": ("docs", "https://learn.microsoft.com/en-us/azure/search/"),
    "entra-connect": ("docs", "https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/"),
    "microsoft-365-admin-center": ("docs", "https://learn.microsoft.com/en-us/microsoft-365/admin/"),
    "viva-insights": ("docs", "https://learn.microsoft.com/en-us/viva/insights/"),
    "viva-learning": ("docs", "https://learn.microsoft.com/en-us/viva/learning/"),
    "dynamics-365-customer-service": ("docs", "https://learn.microsoft.com/en-us/dynamics365/customer-service/"),
    "dynamics-365-sales": ("docs", "https://learn.microsoft.com/en-us/dynamics365/sales/"),
    "dynamics-365-customer-insights": ("docs", "https://learn.microsoft.com/en-us/dynamics365/customer-insights/"),
    "power-platform-cli": ("docs", "https://learn.microsoft.com/en-us/power-platform/developer/cli/introduction"),
    "github-actions": ("docs", "https://docs.github.com/en/actions"),
    "teams-toolkit": ("docs", "https://learn.microsoft.com/en-us/microsoftteams/platform/toolkit/teams-toolkit-fundamentals"),
}


def check(url):
    """-> (ok, endgueltige URL, Status)"""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
            fin = r.geturl(); u = urlparse(fin)
            bad = bool(re.match(r"^(/[a-z]{2}-[a-z]{2})?/search(/|$)", u.path)) or "404" in u.path or "/error" in u.path.lower()   # Suchseite von Learn, nicht Produkte wie /azure/search/
            return (r.status == 200 and u.netloc in OK_HOSTS and not bad), fin, r.status
    except urllib.error.HTTPError as e:
        return False, url, e.code
    except Exception as e:
        return False, url, str(e)[:60]


def main(apply=False):
    raw = F.read_text("utf-8"); ents = json.loads(raw); by = {e["id"]: e for e in ents}
    rep, n = [], 0
    for eid, (field, url) in CAND.items():
        e = by.get(eid)
        if not e: rep.append({"id": eid, "result": "Entitaet fehlt"}); continue
        if e.get(field): rep.append({"id": eid, "result": f"{field} schon gesetzt"}); continue
        ok, fin, st = check(url); time.sleep(0.5)
        rep.append({"id": eid, "field": field, "url": url, "final": fin, "status": st, "result": "gesetzt" if ok and apply else ("geprueft" if ok else "abgelehnt")})
        if ok and apply:
            e[field] = url if urlparse(fin).path.rstrip("/") == urlparse(url).path.rstrip("/") else fin; n += 1
    if apply and n:
        ind = 1 if raw.startswith("[\n {") else 2
        F.write_text(json.dumps(ents, ensure_ascii=False, indent=ind) + "\n", "utf-8")
    (ROOT / "data" / "docs_links_report.json").write_text(json.dumps({"generated": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()), "items": rep}, ensure_ascii=False, indent=1) + "\n", "utf-8")
    for r in rep: print(r["id"], "-", r["result"], r.get("status", ""), r.get("final", "")[:90])
    print(f"{n} Links eingetragen" if apply else "Nur Pruefung (ohne --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main("--apply" in sys.argv))
