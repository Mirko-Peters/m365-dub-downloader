#!/usr/bin/env python3
"""Zieht die Show Notes jeder Episode aus dem Spreaker-RSS (alle Shows aus config.json show_map) und schreibt data/show_notes/<sprache>.json:
Haupttext als Wiki-Markup (editierbar), Kernpunkte, FAQ, Kapitel, Personen (Gaeste), Dauer, Staffel/Folge. Kein Token noetig (oeffentlicher Feed)."""
import hashlib, json, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import show_notes as SN

ROOT = Path(__file__).parent
NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd", "podcast": "https://podcastindex.org/namespace/1.0", "content": "http://purl.org/rss/1.0/modules/content/"}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def fetch(url):
    for a in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "m365-site-bot"}), timeout=90).read().decode("utf-8", "replace")
        except Exception as e:
            if a == 3:
                raise
            time.sleep(4 * (a + 1))


def parse_feed(xml):
    root = ET.fromstring(xml)
    eps = {}
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        guid = (it.findtext("guid") or title).strip()
        enc = it.find("enclosure")
        audio = enc.get("url") if enc is not None else ""
        m = re.search(r"episodes?/[^/]*?(\d{6,})", audio) or re.search(r"(\d{6,})", guid)
        key = m.group(1) if m else hashlib.md5(guid.encode()).hexdigest()[:12]
        raw = (it.findtext("content:encoded", namespaces=NS) or it.findtext("description") or it.findtext("itunes:summary", namespaces=NS) or "").strip()
        markup = SN.html_to_markup(raw) if "<" in raw else raw
        body, key_pts, faq = SN.split_sections(markup)
        try:
            pub = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            pub = ""
        persons = [{"name": (p.text or "").strip(), "role": p.get("role") or "guest", "href": p.get("href") or "", "img": p.get("img") or ""}
                   for p in it.findall("podcast:person", NS) if (p.text or "").strip()]
        ch = it.find("podcast:chapters", NS)
        tr = it.find("podcast:transcript", NS)
        rec = {"id": key, "title": title, "key": norm(title), "published": pub, "duration": SN.hms(it.findtext("itunes:duration", namespaces=NS)),
               "link": (it.findtext("link") or "").strip(), "season": it.findtext("itunes:season", namespaces=NS) or "", "number": it.findtext("itunes:episode", namespaces=NS) or "",
               "image": (it.find("itunes:image", NS).get("href") if it.find("itunes:image", NS) is not None else ""),
               "markup": body, "keypoints": key_pts, "faq": faq, "persons": persons,
               "chapters_url": ch.get("url") if ch is not None and ch.get("url") else "", "transcript_url": tr.get("url") if tr is not None and tr.get("url") else ""}
        eps[key] = rec
    return eps


def main():
    cfg = json.load(open(ROOT / "config.json", encoding="utf-8"))
    out_dir = ROOT / "data" / "show_notes"
    out_dir.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:]   # optional: nur diese Sprachen
    for lang, sid in (cfg.get("show_map") or {}).items():
        if not sid or (only and lang not in only):
            continue
        try:
            eps = parse_feed(fetch(f"https://www.spreaker.com/show/{sid}/episodes/feed"))
        except Exception as e:
            print("Show Notes", lang, "uebersprungen:", str(e)[:120]); continue
        f = out_dir / f"{lang}.json"
        old = json.loads(f.read_text("utf-8")).get("episodes", {}) if f.exists() else {}
        for k, v in eps.items():   # eigene Bearbeitungen im Spreaker (neuer Text) gewinnen; nichts loeschen, was der Feed nicht mehr zeigt
            old[k] = v
        data = {"show": sid, "lang": lang, "episodes": dict(sorted(old.items(), key=lambda kv: kv[1].get("published", ""), reverse=True))}
        txt = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        if not f.exists() or f.read_text("utf-8") != txt:
            f.write_text(txt, encoding="utf-8"); print("Show Notes", lang, len(eps), "Folgen aktualisiert")
        else:
            print("Show Notes", lang, "unveraendert")


if __name__ == "__main__":
    main()
