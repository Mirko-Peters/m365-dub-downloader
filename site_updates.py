"""Microsoft-Produktupdates je Entitaet (vom Update-Waechter im Worker gesammelt): nur Titel, Link, Datum, offizielle Quelle."""
from datetime import datetime, timezone
from site_i18n import T
from site_learn import esc, _fetch_json

BY = {}      # eid -> Liste (neueste zuerst)
ALL = []


def load(api):
    BY.clear(); ALL.clear()
    for u in (_fetch_json(f"{api}/api/updates/export") or {}).get("items", []):
        BY.setdefault(u["eid"], []).append(u); ALL.append(u)


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def block(lang, eid, n=10):
    it = BY.get(eid, [])[:n]
    if not it:
        return ""
    li = "".join(f'<li><a href="{esc(u["url"])}" rel="nofollow noopener" target="_blank">{esc(u["title"])}</a> <span class="mut">· {day(u["published"])} · {esc(u["source"])}</span></li>' for u in it)
    return f'<section class="en-upd"><h2>{esc(T(lang, "Latest updates", "Neueste Updates"))}</h2><ul>{li}</ul><p class="mut">{esc(T(lang, "Titles and links from official Microsoft sources, checked regularly.", "Titel und Links aus offiziellen Microsoft-Quellen, regelmäßig geprüft."))}</p></section>'
