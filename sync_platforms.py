#!/usr/bin/env python3
"""Ordnet die Folgen jeder Show den Folgen auf anderen Plattformen zu und schreibt die Links nach data/episode_links.json (Schluessel "<folge>:<sprache>").
Plattformen: Apple Podcasts (iTunes-API, ohne Zugang), Deezer (oeffentliche API), Spotify (SPOTIFY_CLIENT_ID/SECRET oder per scrape_spotify.py gesammelt),
YouTube (yt-dlp, Wiedergabelisten aus platforms.json "youtube_sources"), dazu die Links der Podpage-Sicherung (englische Show).
Zugeordnet wird per Titel (auch gekuerzt/leicht abweichend) und Datum (platform_match.py); unsichere Faelle bleiben offen und stehen in data/episode_links_report.json.
Eigene Korrekturen in data/episode_links_manual.json {"<folge>:<sprache>": {"apple": "https://..."}} gehen immer vor.

data/platforms.json:  {"de": {"apple_id": "1234567890", "spotify_id": "4abc...", "deezer_show": "https://www.deezer.com/show/123", "youtube_sources": ["https://www.youtube.com/playlist?list=..."]}, "en": {...}}
Weitere Plattformen: einen Konnektor (Funktion, die Kandidaten {title,url,date} liefert) in CONNECTORS eintragen.
"""
import base64, gzip, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

import platform_match as PM

ROOT = Path(__file__).parent
DATA = ROOT / "data"
COUNTRY = {"en": "us", "de": "de", "es": "es", "fr": "fr", "it": "it", "pt": "br", "nl": "nl", "pl": "pl", "id": "id", "ru": "ru",
           "uk": "ua", "ar": "ae", "he": "il", "hi": "in", "ja": "jp", "ko": "kr", "ml": "in", "pa": "in", "ta": "in", "te": "in"}
BASE_LANG = {"de-de": "de", "es-us": "es", "es-es": "es", "fr-fr": "fr", "pt-br": "pt", "nl-nl": "nl"}
SEARCH_CAP = 40   # einzelne Apple-Suchen je Lauf fuer Folgen, die nicht in der letzten 200er-Liste stehen


def jload(p, default):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:
        return default


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "m365-site-sync"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def strip(t):
    return re.sub(r"<[^>]+>", "", t or "").strip()


# ---------- eigene Folgen je Show ----------
def own_episodes(lang):
    """{schluessel: {title, date}} - Sprach-Shows aus episodes/*.json, englische Show aus den Spreaker-Show-Notes (data/show_notes/en.json)."""
    out = {}
    if lang == "en":
        for ep_id, e in (jload(DATA / "show_notes" / "en.json", {}).get("episodes") or {}).items():
            out[f"{ep_id}:en"] = {"title": e["title"], "date": e.get("published", "")}
        return out
    pub = jload(DATA / "published.json", {})
    for p in (ROOT / "episodes").glob("*.json"):
        for l, e in jload(p, {}).items():
            if BASE_LANG.get(l, l) == lang:
                out[f"{p.stem}:{lang}"] = {"title": strip(e.get("title")), "date": ((pub.get(f"{p.stem}:{lang}") or {}).get("at") or "")[:10]}
    return out


# ---------- Konnektoren: je Plattform eine Liste von Kandidaten ----------
def apple_candidates(lang, ids, ctx):
    r = get(f"https://itunes.apple.com/lookup?id={ids['apple_id']}&entity=podcastEpisode&limit=200&country={COUNTRY.get(lang, 'us')}")
    return [{"title": x.get("trackName"), "url": x["trackViewUrl"].split("&uo=")[0], "date": (x.get("releaseDate") or "")[:10]} for x in r.get("results", []) if x.get("trackViewUrl") and x.get("wrapperType") == "podcastEpisode"]


def apple_search(lang, ids, openkeys, own, budget=SEARCH_CAP):
    """Aeltere Folgen stehen nicht in der 200er-Liste: gezielt per Titel suchen (Antworten gefiltert auf die eigene Show)."""
    out = []
    for k in openkeys[:budget]:
        q = urllib.parse.quote(PM.normalize(own[k]["title"])[:80])
        try:
            r = get(f"https://itunes.apple.com/search?term={q}&media=podcast&entity=podcastEpisode&limit=8&country={COUNTRY.get(lang, 'us')}")
        except Exception:
            continue
        for x in r.get("results", []):
            if str(x.get("collectionId")) == str(ids["apple_id"]) and x.get("trackViewUrl"):
                out.append({"title": x.get("trackName"), "url": x["trackViewUrl"].split("&uo=")[0], "date": (x.get("releaseDate") or "")[:10]})
        time.sleep(3.2)   # iTunes-Limit ca. 20 Anfragen/Minute
    return out


def deezer_candidates(lang, ids, ctx):
    m = re.search(r"/show/(\d+)", ids.get("deezer_show", ""))
    if not m:
        return []
    out, url = [], f"https://api.deezer.com/podcast/{m.group(1)}/episodes?limit=100"
    while url:
        r = get(url)
        out += [{"title": x.get("title"), "url": f"https://www.deezer.com/episode/{x['id']}", "date": (x.get("release_date") or "")[:10]} for x in r.get("data", [])]
        url = r.get("next")
    return out


def spotify_candidates(lang, ids, ctx):
    tok = ctx.get("spotify_token")
    if not tok or not ids.get("spotify_id"):
        return []
    out, url = [], f"https://api.spotify.com/v1/shows/{ids['spotify_id']}/episodes?limit=50&market=US"
    while url:
        r = get(url, {"Authorization": f"Bearer {tok}"})
        out += [{"title": x.get("name"), "url": x["external_urls"]["spotify"], "date": x.get("release_date", "")} for x in r.get("items", []) if x]
        url = r.get("next")
    return out


def youtube_candidates(lang, ids, ctx):
    srcs = ids.get("youtube_sources") or []
    if not srcs:
        return []
    try:
        import yt_dlp
    except ImportError:
        print("YouTube-Abgleich uebersprungen: yt-dlp nicht installiert (pip install yt-dlp)"); return []
    out = []
    with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": True, "ignoreerrors": True}) as y:
        for u in srcs:
            info = y.extract_info(u, download=False) or {}
            for e in info.get("entries") or []:
                if e and e.get("id") and e.get("title"):
                    d = e.get("upload_date") or ""
                    out.append({"title": e["title"], "url": f"https://www.youtube.com/watch?v={e['id']}", "date": f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 else ""})
    return out


def youtube_music_candidates(lang, ids, ctx):
    """YouTube Music: Die Folgen-IDs sind NICHT die Video-IDs, also nicht ableitbar. Wir finden den Podcast ueber eine bekannte Folge (Podpage-Sicherung), eine
    eingetragene ID (platforms.json "youtube_music_id") oder die Suche nach dem Show-Namen und lesen alle Folgen (inoffizielle Bibliothek ytmusicapi, ohne Anmeldung)."""
    try:
        from ytmusicapi import YTMusic
    except ImportError:
        print("YouTube Music uebersprungen: ytmusicapi nicht installiert (pip install ytmusicapi)"); return []
    yt = YTMusic()
    cands = [ids.get("youtube_music_id")] if ids.get("youtube_music_id") else []
    for vid in (ctx.get("ytm_seeds") or [])[:4]:
        if cands:
            break
        try:
            ep = yt.get_episode(vid) or {}
            cands += [x for x in (ep.get("playlistId"), (ep.get("podcast") or {}).get("id"), (ep.get("podcast") or {}).get("playlistId")) if x]
        except Exception as e:
            print("YouTube Music Folge", vid, str(e)[:80])
    if not cands and ids.get("youtube_music_name"):
        for r in yt.search(ids["youtube_music_name"], filter="podcasts", limit=5):
            if r.get("browseId"):
                cands.append(r["browseId"]); break
    for pid in cands:
        pid = re.sub(r"^MPSP", "", pid)
        try:
            pod = yt.get_podcast(pid, limit=None)
        except Exception as e:
            print("YouTube Music Podcast", pid, str(e)[:80]); continue
        ids["youtube_music_id"] = pid
        ids["youtube_music_show"] = f"https://music.youtube.com/playlist?list={pid}"
        out = []
        for e in pod.get("episodes") or []:
            if e.get("videoId") and e.get("title"):
                out.append({"title": e["title"], "url": f"https://music.youtube.com/podcast/{e['videoId']}", "date": ""})
        return out
    return []


def podpage_candidates(lang, ids, ctx):
    """Links der Podpage-Sicherung (englische Show): Apple, Spotify, YouTube Music je Folge."""
    if lang != "en":
        return {}
    f = DATA / "podpage" / "episodes.json.gz"
    if not f.exists():
        return {}
    eps = json.load(gzip.open(f, "rt", encoding="utf-8"))
    res = {"apple": [], "spotify": [], "youtube_music": []}
    for e in eps:
        d = (e.get("create_time") or "")[:10]
        for plat, field in (("apple", "episode_apple_url_path"), ("spotify", "episode_spotify_url_path"), ("youtube_music", "episode_youtube_music_url_path")):
            u = e.get(field)
            if u and u not in ("None", "False"):
                res[plat].append({"title": e.get("name"), "url": u.split("&uo=")[0], "date": d})
    return res


CONNECTORS = {"apple": apple_candidates, "deezer": deezer_candidates, "spotify": spotify_candidates, "youtube": youtube_candidates, "youtube_music": youtube_music_candidates}


def spotify_token():
    cid, sec = os.environ.get("SPOTIFY_CLIENT_ID"), os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not (cid and sec):
        return None
    req = urllib.request.Request("https://accounts.spotify.com/api/token", b"grant_type=client_credentials", {"Authorization": "Basic " + base64.b64encode(f"{cid}:{sec}".encode()).decode()})
    return json.load(urllib.request.urlopen(req, timeout=60))["access_token"]


def main():
    plat = jload(DATA / "platforms.json", {})
    # Englische Show: Apple-ID aus der Podpage-Sicherung uebernehmen, wenn noch nicht eingetragen
    pc = jload(DATA / "podpage" / "podcast.json", {})
    if "en" not in plat:
        plat["en"] = {}
    if pc.get("apple_player_id") and not plat["en"].get("apple_id"):
        plat["en"]["apple_id"] = str(pc["apple_player_id"])
    out = jload(DATA / "episode_links.json", {})   # frueher gefundene Links bleiben erhalten (auch wenn eine Plattform gerade nicht antwortet)
    for k, u in jload(DATA / "spotify_links.json", {}).items():   # per scrape_spotify.py gesammelt (ohne API)
        out.setdefault(k, {}).setdefault("spotify", u)
    ctx = {}
    try:
        ctx["spotify_token"] = spotify_token()
    except Exception as e:
        print("Spotify-Token:", e)
    report = {}
    for lang, ids in plat.items():
        own = own_episodes(lang)
        if not own:
            continue
        rep = report.setdefault(lang, {})
        cands = {}
        pp = podpage_candidates(lang, ids, ctx) or {}
        ctx["ytm_seeds"] = [c["url"].rstrip("/").split("/")[-1] for c in pp.get("youtube_music", [])][::-1]   # juengste zuerst
        for name, fn in CONNECTORS.items():
            try:
                cands[name] = fn(lang, ids, ctx)
            except Exception as e:
                print(name, lang, str(e)[:120])
        for name, lst in pp.items():
            cands.setdefault(name, []).extend(lst)
        for name, lst in cands.items():
            hit, open_, amb = PM.match(own, lst)
            if name == "apple" and ids.get("apple_id") and open_:   # nicht in der 200er-Liste: gezielt suchen
                extra = apple_search(lang, ids, [k for k in open_ if k not in out or "apple" not in out[k]], own)
                if extra:
                    h2, open_, amb = PM.match(own, lst + extra)
                    hit = h2
            for k, u in hit.items():
                out.setdefault(k, {})[name] = u
            have = sum(1 for k in own if name in out.get(k, {}))
            rep[name] = {"candidates": len(lst), "matched_now": len(hit), "linked": have, "of": len(own),
                         "open": [own[k]["title"] for k in open_ if name not in out.get(k, {})][:40], "ambiguous": [own[k]["title"] for k in amb][:20]}
            print(f"{lang} {name}: {len(lst)} Kandidaten, {len(hit)} neu zugeordnet, {have}/{len(own)} verlinkt")
    for k, v in jload(DATA / "episode_links_manual.json", {}).items():   # eigene Korrekturen gehen vor
        if isinstance(v, dict):
            out.setdefault(k, {}).update({p: u for p, u in v.items() if u})
    # Show-Links ergaenzen
    for l, ids in plat.items():
        if ids.get("apple_id"): ids["apple_show"] = f"https://podcasts.apple.com/podcast/id{ids['apple_id']}"
        if ids.get("spotify_id"): ids["spotify_show"] = f"https://open.spotify.com/show/{ids['spotify_id']}"
    json.dump(plat, open(DATA / "platforms.json", "w", encoding="utf-8"), indent=1)
    json.dump(out, open(DATA / "episode_links.json", "w", encoding="utf-8"), indent=1, sort_keys=True)
    json.dump({"generated": time.strftime("%Y-%m-%d"), "shows": report}, open(DATA / "episode_links_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(out), "Folgen mit Plattform-Links")


if __name__ == "__main__":
    main()
