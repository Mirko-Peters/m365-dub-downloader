#!/usr/bin/env python3
"""Holt Apple-Podcasts- und Spotify-Folgenlinks für die Sprach-Shows → data/episode_links.json.

data/platforms.json:  {"de": {"apple_id": "1234567890", "spotify_id": "4abc..."}, ...}   (IDs eintragen, sobald die Show dort existiert)
Apple braucht keinen Zugang (öffentliche iTunes-Lookup-API).
Spotify braucht SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET (kostenlose App auf developer.spotify.com) als GitHub-Secrets.
"""
import base64, json, os, re, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
COUNTRY = {"de": "de", "es": "es", "fr": "fr", "it": "it", "pt": "br", "nl": "nl", "pl": "pl", "id": "id", "ru": "ru",
           "uk": "ua", "ar": "ae", "he": "il", "hi": "in", "ja": "jp", "ko": "kr", "ml": "in", "pa": "in", "ta": "in", "te": "in"}


def norm(t): return re.sub(r"[\W_]+", "", (t or "").casefold())


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "m365-site-sync"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def main():
    plat = json.load(open(ROOT / "data" / "platforms.json", encoding="utf-8"))
    eps = {p.stem: json.load(open(p, encoding="utf-8")) for p in (ROOT / "episodes").glob("*.json")}
    titles = {}  # lang -> {norm(title): vid}
    for vid, langs in eps.items():
        for l, e in langs.items():
            titles.setdefault(l, {})[norm(e["title"])] = vid
    out = {}
    token = None
    cid, sec = os.environ.get("SPOTIFY_CLIENT_ID"), os.environ.get("SPOTIFY_CLIENT_SECRET")
    if cid and sec:
        req = urllib.request.Request("https://accounts.spotify.com/api/token", b"grant_type=client_credentials",
                                     {"Authorization": "Basic " + base64.b64encode(f"{cid}:{sec}".encode()).decode()})
        token = json.load(urllib.request.urlopen(req, timeout=60))["access_token"]
    for l, ids in plat.items():
        t = titles.get(l, {})
        if ids.get("apple_id"):
            try:
                r = get(f"https://itunes.apple.com/lookup?id={ids['apple_id']}&entity=podcastEpisode&limit=200&country={COUNTRY.get(l, 'us')}")
                for x in r.get("results", []):
                    vid = t.get(norm(x.get("trackName")))
                    if vid and x.get("trackViewUrl"):
                        out.setdefault(f"{vid}:{l}", {})["apple"] = x["trackViewUrl"]
            except Exception as e:
                print("Apple", l, e)
        if ids.get("spotify_id") and token:
            try:
                url = f"https://api.spotify.com/v1/shows/{ids['spotify_id']}/episodes?limit=50&market=US"
                while url:
                    r = get(url, {"Authorization": f"Bearer {token}"})
                    for x in r.get("items", []):
                        vid = t.get(norm(x.get("name")))
                        if vid:
                            out.setdefault(f"{vid}:{l}", {})["spotify"] = x["external_urls"]["spotify"]
                    url = r.get("next")
            except Exception as e:
                print("Spotify", l, e)
    # Show-Links ergänzen
    for l, ids in plat.items():
        if ids.get("apple_id"): ids["apple_show"] = f"https://podcasts.apple.com/podcast/id{ids['apple_id']}"
        if ids.get("spotify_id"): ids["spotify_show"] = f"https://open.spotify.com/show/{ids['spotify_id']}"
    json.dump(plat, open(ROOT / "data" / "platforms.json", "w", encoding="utf-8"), indent=1)
    json.dump(out, open(ROOT / "data" / "episode_links.json", "w", encoding="utf-8"), indent=1)
    print(len(out), "Folgenlinks")


if __name__ == "__main__":
    main()
