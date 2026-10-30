#!/usr/bin/env python3
"""M365 Show (Livestream-Show auf YouTube, laufend): holt Streams des Kanals -> data/live.json.
Quelle 1 (immer): oeffentlicher YouTube-Kanal-Feed (letzte ~15 Videos mit Titel, Datum, Beschreibung, Vorschaubild, Aufrufen).
Quelle 2 (wenn yt-dlp da ist und YouTube antwortet): Reiter 'Streams' mit live_status (is_live / is_upcoming / was_live) und geplanter Startzeit.
Kanal aus config.json (youtube_channel_url). Bereits bekannte Streams bleiben erhalten (Archiv bis 300)."""
import json, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}


def channel_id():
    cfg = json.loads((ROOT / "config.json").read_text("utf-8"))
    m = re.search(r"/channel/(UC[\w-]{20,})", cfg.get("youtube_channel_url", ""))
    return m.group(1) if m else ""


def fetch(url):
    for a in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "m365-site-bot"}), timeout=60).read().decode("utf-8", "replace")
        except Exception:
            if a == 2:
                raise
            time.sleep(3 * (a + 1))


def parse_rss(xml):
    out = []
    for e in ET.fromstring(xml).findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS)
        if not vid:
            continue
        g = e.find("m:group", NS)
        views = g.find("m:community/m:statistics", NS).get("views") if g is not None and g.find("m:community/m:statistics", NS) is not None else ""
        out.append({"id": vid, "title": (e.findtext("a:title", namespaces=NS) or "").strip(), "published": (e.findtext("a:published", namespaces=NS) or "")[:19],
                    "description": ((g.findtext("m:description", namespaces=NS) if g is not None else "") or "").strip(), "views": int(views) if str(views).isdigit() else 0})
    return out


def ytdlp_streams(cid):
    """Streams-Reiter: Live, geplante und vergangene Streams. Leere Liste, wenn yt-dlp fehlt oder YouTube blockt (z. B. Bot-Pruefung ohne Cookies)."""
    try:
        import yt_dlp
    except ImportError:
        print("yt-dlp nicht installiert - nur Kanal-Feed"); return []
    opts = {"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "skip_download": True, "ignoreerrors": True, "playlistend": 60}
    if (ROOT / "cookies.txt").exists():
        opts["cookiefile"] = str(ROOT / "cookies.txt")
    out = []
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            info = y.extract_info(f"https://www.youtube.com/channel/{cid}/streams", download=False) or {}
            entries = [e for e in (info.get("entries") or []) if e and e.get("id")]
            full = dict(opts); full["extract_flat"] = False
            with yt_dlp.YoutubeDL(full) as yf:
                for e in entries:
                    st = e.get("live_status") or ""
                    rec = {"id": e["id"], "title": e.get("title") or "", "live_status": st, "views": e.get("view_count") or 0, "duration": e.get("duration") or 0}
                    if st in ("is_live", "is_upcoming") or not st:   # Startzeit und Beschreibung nur fuer laufende/geplante (oder unbekannte) Streams im Detail holen
                        d = yf.extract_info(f"https://www.youtube.com/watch?v={e['id']}", download=False) or {}
                        rec.update({"live_status": d.get("live_status") or st, "description": (d.get("description") or "").strip(), "views": d.get("view_count") or rec["views"],
                                    "start": datetime.fromtimestamp(d["release_timestamp"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if d.get("release_timestamp") else ""})
                    out.append(rec)
    except Exception as ex:
        print("yt-dlp Streams:", str(ex)[:150])
    return out


def main():
    cid = channel_id()
    if not cid:
        sys.exit("Kein Kanal in config.json (youtube_channel_url)")
    f = ROOT / "data" / "live.json"
    old = json.loads(f.read_text("utf-8")) if f.exists() else {}
    streams = {s["id"]: s for s in old.get("streams", [])}
    try:
        for s in parse_rss(fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")):
            streams.setdefault(s["id"], {}).update(s)
    except Exception as e:
        print("Kanal-Feed:", str(e)[:120])
    yd = ytdlp_streams(cid)
    for s in yd:
        cur = streams.setdefault(s["id"], {})
        cur.update({k: v for k, v in s.items() if v not in (None, "", 0) or k == "live_status"})
    for s in streams.values():   # Streams, die laut Reiter nicht mehr live/geplant sind, nicht als solche halten
        if s.get("live_status") in ("is_upcoming", "is_live") and yd and s["id"] not in {x["id"] for x in yd}:
            s["live_status"] = "was_live"
    arch = sorted(streams.values(), key=lambda s: s.get("start") or s.get("published") or "", reverse=True)[:300]
    data = {"channel": cid, "handle": "@m365show", "source": "rss+yt-dlp" if yd else old.get("source", "rss"), "streams": arch}
    txt = json.dumps(data, ensure_ascii=False, indent=1)
    if not f.exists() or json.loads(f.read_text("utf-8")) != data:
        f.write_text(txt, encoding="utf-8"); print("live.json:", len(arch), "Streams,", sum(1 for s in arch if s.get("live_status") == "is_upcoming"), "geplant,", sum(1 for s in arch if s.get("live_status") == "is_live"), "live")
    else:
        print("live.json unveraendert")


if __name__ == "__main__":
    main()
