"""T25 Nachkontrolle: Kommt das, was apply-shownotes geschrieben hat, im oeffentlichen Spreaker-RSS an (Apple, Spotify lesen
den Feed)? Je geschriebener Folge (shownotes/APPLIED.txt, Status ok/mismatch/unchanged) wird content:encoded mit der
Datei shownotes/spreaker/<id>.html verglichen: Textinhalt gleich? Wie viele <a href> auf www.m365.fm im Feed vs. in der Datei?
Bericht: reports/spreaker-feed-check.md/.json (nur Folgen-IDs und Zahlen)."""
import html, json, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEEDS = ["https://www.spreaker.com/show/6704921/episodes/feed"]
NS = {"content": "http://purl.org/rss/1.0/modules/content/"}
OUT = ROOT / "reports" / "spreaker-feed-check"


def get(u):
    for a in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "m365-site-bot"}), timeout=90).read().decode("utf-8", "replace")
        except Exception:
            if a == 3: raise
            time.sleep(4 * (a + 1))


def text_key(h):
    return re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", h or "")))


def links(h):
    return len(re.findall(r'<a\s[^>]*href="https://www\.m365\.fm/', html.unescape(h or ""), flags=re.I))


def main():
    applied = {}
    for line in (ROOT / "shownotes" / "APPLIED.txt").read_text("utf-8").splitlines():
        f = line.split("\t")
        if len(f) >= 4 and f[1].isdigit() and f[2] in ("ok", "mismatch", "unchanged"): applied[f[1]] = f[2]
    feed = {}
    for u in FEEDS:
        root = ET.fromstring(get(u))
        for it in root.iter("item"):
            enc = it.find("enclosure"); audio = enc.get("url") if enc is not None else ""
            m = re.search(r"episodes?/[^/]*?(\d{6,})", audio) or re.search(r"(\d{6,})", it.findtext("guid") or "")
            if m: feed[m.group(1)] = (it.findtext("content:encoded", namespaces=NS) or it.findtext("description") or "")
    rows, same, keep = [], 0, 0
    for eid in sorted(applied):
        f = ROOT / "shownotes" / "spreaker" / f"{eid}.html"
        if not f.exists(): continue
        mine, got = f.read_text("utf-8").strip(), feed.get(eid)
        if got is None:
            rows.append({"id": eid, "im_feed": False}); continue
        r = {"id": eid, "im_feed": True, "text_gleich": text_key(got) == text_key(mine), "links_datei": links(mine), "links_feed": links(got),
             "html_im_feed": "<a " in html.unescape(got) or "<li" in html.unescape(got), "zeichen_feed": len(got)}
        same += r["text_gleich"]; keep += r["links_feed"] >= r["links_datei"] > 0
        rows.append(r)
    rep = {"generated": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()), "geschrieben": len(rows), "im_feed": sum(1 for r in rows if r["im_feed"]),
           "text_gleich": same, "links_vollstaendig": keep, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.with_suffix(".json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", "utf-8")
    L = [f"# Spreaker-Feed gegen geschriebene Shownotes ({rep['generated']})", "",
         f"Geschrieben: {rep['geschrieben']} · im Feed: {rep['im_feed']} · Text gleich: {same} · alle m365-Links im Feed: {keep}", "",
         "| Folge | im Feed | Text gleich | Links Datei | Links Feed | HTML im Feed |", "|---|---|---|---|---|---|"]
    L += [f"| {r['id']} | {'ja' if r['im_feed'] else 'nein'} | {'ja' if r.get('text_gleich') else 'nein'} | {r.get('links_datei', '')} | {r.get('links_feed', '')} | {'ja' if r.get('html_im_feed') else 'nein'} |" for r in rows[:150]]
    OUT.with_suffix(".md").write_text("\n".join(L) + "\n", "utf-8")
    print("\n".join(L[:4]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
