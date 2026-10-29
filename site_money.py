"""Money-Keyword-Liste fuer die interne Verlinkung (data/money_keywords.json).

Pro Sprache: Schluesselbegriff -> Ziel-Folge (video-id). Die Liste wird bei jedem Seitenbau automatisch aktualisiert:
- auto=true  : vom Generator gepflegt (neue Begriffe kommen dazu, ungueltige Ziele werden neu gewaehlt, Ziele bleiben sonst stabil)
- auto=false : von Hand eingetragen, wird nie ueberschrieben (Begriff 'target' = video-id; 'off': true schaltet einen Eintrag ab)
Der Verlinker nutzt diese Begriffe zuerst (bis MAX_LINKS Links pro Artikel), danach spezifische Tags."""
import json
from datetime import date
from pathlib import Path

MAX_LINKS = 10
PER_LANG = 150
MIN_DF = 2
# Produkt-/Fachbegriffe, die in allen Sprachen unuebersetzt vorkommen; Ziel = Folge mit dem Begriff im Titel
TERMS = ["Copilot Studio", "Microsoft Purview", "Purview", "Entra ID", "SharePoint", "Power Automate", "Power Apps", "Power BI", "Microsoft Fabric",
         "Azure AI Foundry", "Intune", "Defender", "Dataverse", "Microsoft Graph", "Azure OpenAI", "Key Vault", "Business Central", "Dynamics 365",
         "OneDrive", "Exchange Online", "Logic Apps", "API Management", "Zero Trust", "Conditional Access", "Sentinel", "Azure Functions",
         "Microsoft Teams", "Teams", "Azure DevOps", "GitHub Copilot", "Agent 365", "Power Platform", "Microsoft 365 Copilot", "Windows 365", "Azure Arc",
         "Active Directory", "Microsoft Loop", "Viva Engage", "Planner", "Entra", "Azure"]


def update(path, by_lang, tagraw, today=None):
    path = Path(path)
    today = today or date.today().isoformat()
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        data = {}
    langs = data.setdefault("languages", {})
    data["version"] = 1
    data["max_links_per_article"] = MAX_LINKS
    data["help"] = ("Begriff -> Ziel-Folge. auto=false-Eintraege (von Hand) bleiben immer erhalten; "
                    "'off': true deaktiviert einen Begriff. auto=true wird bei jedem Build gepflegt.")
    for l, pool in by_lang.items():
        vids = {o["vid"]: o for o in pool}
        tags = {}
        for o in pool:
            for t in tagraw[l].get(o["vid"], []):
                tags.setdefault(t.lower(), {"label": t, "vids": []})["vids"].append(o["vid"])
        cur = langs.setdefault(l, {})
        # ungueltige Ziele entfernen
        for k, v in list(cur.items()):
            if v.get("target") not in vids and v.get("auto", True):
                del cur[k]
        ranked = sorted((x for x in tags.items() if len(x[1]["vids"]) >= MIN_DF and len(x[0]) >= 4), key=lambda x: (-len(x[1]["vids"]), x[0]))
        for k, info in ranked[:PER_LANG]:
            label = info["label"]
            if any(e.get("auto", True) is False and name.lower() == k for name, e in cur.items()):
                continue
            ex = next((name for name in cur if name.lower() == k), None)
            if ex and cur[ex].get("auto", True) and cur[ex]["target"] in info["vids"]:
                continue  # stabil lassen
            cands = info["vids"]
            def score(v):
                title = (vids[v]["e"]["title"] or "").lower()
                return (k in title, title.startswith(k), vids[v]["date"])
            best = max(cands, key=score)
            if ex:
                del cur[ex]
            cur[label] = {"target": best, "auto": True, "added": today}
        for term in TERMS:
            k = term.lower()
            if any(n.lower() == k for n in cur):
                continue
            hit = [o for o in pool if k in (o["e"]["title"] or "").lower()]
            if hit:
                cur[term] = {"target": max(hit, key=lambda o: (o["e"]["title"].lower().startswith(k), o["date"]))["vid"], "auto": True, "added": today}
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    return data


def registry_for(data, lang):
    """{phrase: vid} ohne deaktivierte Eintraege."""
    return {k: v["target"] for k, v in data.get("languages", {}).get(lang, {}).items() if not v.get("off")}
