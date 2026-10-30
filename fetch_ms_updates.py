"""Zieht die Microsoft-Produktupdates ueber die offiziellen Release-Communications-Schnittstellen (JSON, mit Produkt-Tags) und ordnet sie
den Produkt-Entitaeten zu. Ergebnis: data/product_updates.json {updated, items:[{id, src, title, desc, status, phase, when, created, modified, eids}]}.
Quellen: Microsoft 365 Roadmap (api/v1/m365) und Azure Updates (api/v2/azure). Es werden keine Links auf Microsoft-Seiten gespeichert."""
import json, re, sys, html, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
BASE = "https://www.microsoft.com/releasecommunications/api/"
DAYS_M365, DAYS_AZURE, PER_ENTITY, DESC_MAX = 240, 120, 14, 650
UA = {"user-agent": "M365FM-update-watch/2.0 (+https://www.m365.fm)", "accept": "application/json"}

# Produkt-Tag der Roadmap -> Entitaets-IDs (Produkt-Tags, die hier fehlen, werden ueber Namen/Aliase der Entitaeten zugeordnet)
TAG = {
    "Microsoft Copilot (Microsoft 365)": ["copilot"], "Microsoft Copilot Studio": ["copilot-studio", "power-platform"], "Microsoft Teams": ["teams"],
    "Microsoft Purview": ["purview"], "Outlook": ["outlook"], "Microsoft Viva": ["viva"], "SharePoint": ["sharepoint"], "PowerPoint": ["powerpoint"],
    "Microsoft 365": ["microsoft-365"], "Word": ["word"], "OneDrive": ["onedrive"], "Microsoft 365 app": ["microsoft-365-apps"], "Planner": ["microsoft-planner"],
    "Microsoft 365 admin center": ["microsoft-365-admin-center"], "Microsoft 365 Admin Center": ["microsoft-365-admin-center"], "Excel": ["excel"],
    "OneNote": ["onenote"], "Microsoft Intune": ["intune"], "Power Automate": ["power-automate", "power-platform"], "Power Apps": ["power-apps", "power-platform"],
    "Microsoft Entra": ["microsoft-entra"], "Power Pages": ["power-pages", "power-platform"], "Microsoft Defender for Office 365": ["defender"],
    "Microsoft Defender": ["defender"], "Microsoft 365 Defender": ["defender"], "Microsoft Dataverse": ["dataverse", "power-platform"], "Exchange": ["exchange-online"],
    "Access": ["access"], "Forms": ["microsoft-forms"], "Microsoft Stream": ["microsoft-stream"], "Visio": ["visio"], "Whiteboard": ["microsoft-whiteboard"],
    "Microsoft To Do": ["microsoft-to-do"], "Microsoft Project": ["project"], "Windows 365": ["windows-365"], "Microsoft Clipchamp": ["microsoft-clipchamp"],
    "Microsoft Agent 365": ["agent-365", "copilot"], "Work IQ": ["copilot"], "Microsoft Power Platform governance and administration": ["power-platform"],
    "Dynamics 365 Business Central": ["dynamics-365-business-central", "dynamics-365"], "Dynamics 365 Customer Service": ["dynamics-365-customer-service", "dynamics-365"],
    "Dynamics 365 Contact Center": ["dynamics-365-customer-service", "dynamics-365"], "Dynamics 365 Sales": ["dynamics-365-sales", "dynamics-365"],
    "Dynamics 365 Customer Insights - Journeys": ["dynamics-365-customer-insights", "dynamics-365"], "Dynamics 365 Customer Insights - Data": ["dynamics-365-customer-insights", "dynamics-365"],
    "Microsoft Information Protection": ["purview"], "SharePoint Syntex": ["sharepoint"],
}


def get(url):
    req = urllib.request.Request(url.replace(" ", "%20"), headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=120).read().decode("utf-8"))


def plain(h):
    t = re.sub(r"<(br|/p|/li|/h\d)\s*/?>", "\n", h or "", flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    t = re.sub(r"[ \t\r\f\v]+", " ", t); t = re.sub(r"\n\s*\n+", "\n", t).strip()
    return (t[:DESC_MAX].rsplit(" ", 1)[0] + "…") if len(t) > DESC_MAX else t


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def entity_index():
    ents = json.loads((ROOT / "data" / "entities.json").read_text("utf-8"))
    by_name, ids = {}, set()
    for e in ents:
        if e["type"] not in ("product", "platform"): continue
        ids.add(e["id"])
        for n in {e["name"], *(e.get("aliases") or [])}:
            if n and len(n) >= 4: by_name.setdefault(norm(n), e["id"])
    return by_name, ids


def m365(cut, by_name, ids):
    out = []
    for x in get(BASE + "v1/m365?$orderby=modified desc&$top=5000"):
        mod = (x.get("modified") or "")[:10]
        if mod < cut: continue
        eids = []
        for p in (x.get("tagsContainer") or {}).get("products", []):
            t = p.get("tagName", "")
            for e in TAG.get(t) or ([by_name[norm(t)]] if norm(t) in by_name else []):
                if e in ids and e not in eids: eids.append(e)
        if not eids: continue
        ph = [p["tagName"] for p in (x.get("tagsContainer") or {}).get("releasePhase", [])]
        when = " · ".join(v for v in (("GA: " + x["publicDisclosureAvailabilityDate"]) if x.get("publicDisclosureAvailabilityDate") else "",
                                      ("Preview: " + x["publicPreviewDate"]) if x.get("publicPreviewDate") else "") if v)
        out.append({"id": f"m365-{x['id']}", "src": "Microsoft 365 Roadmap", "title": (x.get("title") or "").strip(), "desc": plain(x.get("description")),
                    "status": x.get("status") or "", "phase": ph, "when": when, "created": (x.get("created") or "")[:10], "modified": mod, "eids": eids})
    return out


def azure(cut, by_name, ids):
    out, url = [], BASE + "v2/azure?$orderby=modified desc&$top=200&$filter=" + urllib.parse.quote(f"modified ge {cut}T00:00:00Z")
    pages = 0
    while url and pages < 30:
        j = get(url); pages += 1
        for x in j.get("value", []):
            eids = ["azure"]
            for p in x.get("products") or []:
                e = by_name.get(norm(p))
                if e in ids and e not in eids: eids.append(e)
            av = x.get("availabilities") or []
            when = " · ".join(f"{a.get('ring')}: {a.get('month')} {a.get('year')}" for a in av[:2] if a.get("ring"))
            out.append({"id": f"azure-{x['id']}", "src": "Azure Updates", "title": (x.get("title") or "").strip(), "desc": plain(x.get("description")),
                        "status": x.get("status") or "", "phase": [], "when": when, "created": (x.get("created") or "")[:10], "modified": (x.get("modified") or "")[:10], "eids": eids})
        url = j.get("@odata.nextLink")
    return out


def main():
    today = datetime.now(timezone.utc).date()
    by_name, ids = entity_index()
    items, err = [], []
    for fn, days in ((m365, DAYS_M365), (azure, DAYS_AZURE)):
        try:
            got = fn((today - timedelta(days=days)).isoformat(), by_name, ids); items += got; print(fn.__name__, len(got))
        except Exception as ex:
            err.append(f"{fn.__name__}: {ex}"); print("FEHLER", fn.__name__, ex, file=sys.stderr)
    if not items:
        raise SystemExit("keine Updates geholt, alte Datei bleibt: " + "; ".join(err))
    # je Entitaet nur die PER_ENTITY neuesten behalten (Datei klein halten)
    items.sort(key=lambda i: (i["modified"], i["created"]), reverse=True)
    cnt, keep = {}, []
    for i in items:
        use = [e for e in i["eids"] if cnt.get(e, 0) < PER_ENTITY]
        if not use: continue
        for e in use: cnt[e] = cnt.get(e, 0) + 1
        keep.append(dict(i, eids=use))
    # ohne Aenderung nichts neu schreiben (kein unnoetiger Build)
    dst = ROOT / "data" / "product_updates.json"
    old = json.loads(dst.read_text("utf-8")) if dst.exists() else {}
    if old.get("items") == keep: print("unveraendert"); return
    dst.write_text(json.dumps({"updated": today.isoformat(), "errors": err, "items": keep}, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print("gespeichert:", len(keep), "Updates fuer", len(cnt), "Entitaeten")


if __name__ == "__main__":
    main()
