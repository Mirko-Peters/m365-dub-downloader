"""Holt aus dem Spreaker-RSS der englischen Show Audio, Dauer und Transkript je Folge.
Schreibt data/en_episodes.json (Schluessel: normalisierter Titel) und data/en_transcripts/<guid>.txt."""
import json, re, hashlib, sys, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parent
FEED = "https://www.spreaker.com/show/6704921/episodes/feed"
NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd", "podcast": "https://podcastindex.org/namespace/1.0"}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": "m365-site-bot"})
    return urllib.request.urlopen(r, timeout=60).read().decode("utf-8", "replace")


def clean_transcript(t):
    t = t.strip()
    if t.startswith("{") or t.startswith("["):
        try:
            j = json.loads(t)
            segs = j.get("segments", j) if isinstance(j, dict) else j
            return " ".join(s.get("body") or s.get("text", "") for s in segs).strip()
        except Exception:
            pass
    out, last = [], ""
    for ln in t.splitlines():
        ln = re.sub(r"<[^>]+>", "", ln).strip()
        if not ln or "-->" in ln or ln.startswith(("WEBVTT", "NOTE")) or ln.isdigit():
            continue
        if ln != last:
            out.append(ln); last = ln
    return " ".join(out)


def main():
    root = ET.fromstring(get(FEED))
    tdir = ROOT / "data" / "en_transcripts"; tdir.mkdir(parents=True, exist_ok=True)
    f = ROOT / "data" / "en_episodes.json"
    old = json.loads(f.read_text("utf-8")) if f.exists() else {}
    res = dict(old); n = 0
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        guid = (it.findtext("guid") or title).strip()
        h = hashlib.md5(guid.encode()).hexdigest()[:12]
        enc = it.find("enclosure")
        tr = it.find("podcast:transcript", NS)
        rec = {"title": title, "guid": guid, "audio": enc.get("url") if enc is not None else "",
               "duration": (it.findtext("itunes:duration", namespaces=NS) or "").strip(), "pub": it.findtext("pubDate") or ""}
        m = re.search(r"episodes?/[^/]*?(\d{6,})", rec["audio"]) or re.search(r"(\d{6,})", guid)
        rec["spreaker_id"] = m.group(1) if m else ""
        if tr is not None and tr.get("url"):
            rec["transcript_url"] = tr.get("url")
            p = tdir / f"{h}.txt"
            if not p.exists():
                try:
                    p.write_text(clean_transcript(get(tr.get("url"))), encoding="utf-8"); n += 1
                except Exception as e:
                    print("Transkript fehlt:", title[:50], e, file=sys.stderr)
            if p.exists() and p.stat().st_size > 50:
                rec["transcript"] = h
        res[norm(title)] = rec
    f.write_text(json.dumps(res, ensure_ascii=False, indent=0), encoding="utf-8")
    print(len(res), "Folgen,", n, "neue Transkripte")


if __name__ == "__main__":
    main()
