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


def page_block(lang, eurl, names, n=60):
    """Gesamtliste der neuesten Microsoft-Updates fuer die Updates-Seite: nach Tag gruppiert, mit Link auf die Produktseite."""
    if not ALL:
        return ""
    out, cur = [], None
    for u in sorted(ALL, key=lambda x: x["published"], reverse=True)[:n]:
        d = day(u["published"])
        if d != cur:
            if cur: out.append("</ul>")
            out.append(f'<h3>{d}</h3><ul>'); cur = d
        nm = names.get(u["eid"], u["eid"])
        out.append(f'<li><a href="{esc(u["url"])}" rel="nofollow noopener" target="_blank">{esc(u["title"])}</a> <span class="mut">· <a href="{esc(eurl(u["eid"]))}">{esc(nm)}</a> · {esc(u["source"])}</span></li>')
    out.append("</ul>")
    return f'<section><h2>{esc(T(lang, "Microsoft updates", "Microsoft-Updates"))}</h2>' + "".join(out) + f'<p class="mut">{esc(T(lang, "Titles and links from official Microsoft sources; matched to products automatically.", "Titel und Links aus offiziellen Microsoft-Quellen, automatisch den Produkten zugeordnet."))}</p></section>'
