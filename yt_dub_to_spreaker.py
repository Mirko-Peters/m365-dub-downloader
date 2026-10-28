#!/usr/bin/env python3
"""
YouTube Dub Downloader -> Spreaker
=================================
Lädt von deinem YouTube-Kanal alle Dub-Tonspuren (alle Sprachen außer der
Originalsprache, inkl. Deutsch) als MP3 herunter und lädt sie danach in
die passende Spreaker-Show der jeweiligen Sprache hoch.

Befehle:
  python yt_dub_to_spreaker.py run          # scannen + laden + hochladen (für den Zeitplan)
  python yt_dub_to_spreaker.py download     # nur scannen + laden
  python yt_dub_to_spreaker.py upload       # nur noch nicht hochgeladene MP3s hochladen
  python yt_dub_to_spreaker.py shows        # Spreaker-Shows + Sprach-Zuordnung anzeigen
  python yt_dub_to_spreaker.py shows --create-missing   # fehlende Sprach-Shows anlegen (SEO-Texte aus shows_seo.json)
  python yt_dub_to_spreaker.py status       # Übersicht: geladen / hochgeladen / offen

Optionen: --limit N (max. Videos scannen), --full-rescan, --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
    from yt_dlp import YoutubeDL
except ImportError:  # pragma: no cover
    print("Fehlende Pakete. Bitte ausführen:  pip install -U yt-dlp requests")
    sys.exit(1)

BASE = Path(__file__).resolve().parent
CONFIG_FILE = BASE / "config.json"
STATE_FILE = BASE / "state.json"
SEO_FILE = BASE / "shows_seo.json"
SHOWS_CACHE = BASE / "spreaker_shows.json"
LOCK_FILE = BASE / ".running.lock"
API = "https://api.spreaker.com/v2"

log = logging.getLogger("dubs")

LANG_NAMES = {
    "en": "Englisch", "es": "Spanisch", "fr": "Französisch", "it": "Italienisch",
    "pt": "Portugiesisch", "hi": "Hindi", "id": "Indonesisch", "ja": "Japanisch",
    "ko": "Koreanisch", "nl": "Niederländisch", "pl": "Polnisch", "ru": "Russisch",
    "tr": "Türkisch", "uk": "Ukrainisch", "ar": "Arabisch", "zh": "Chinesisch",
    "vi": "Vietnamesisch", "th": "Thailändisch", "bn": "Bengalisch", "ta": "Tamil",
    "te": "Telugu", "he": "Hebräisch", "ml": "Malayalam", "mr": "Marathi", "gu": "Gujarati",
    "pa": "Punjabi", "kn": "Kannada", "ur": "Urdu", "de": "Deutsch",
}


# --------------------------------------------------------------------------- helpers
def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            log.error("Kann %s nicht lesen (%s)", path.name, e)
            raise SystemExit(1)
    return default


def save_json(path: Path, data) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


LANG_ALIASES = {"iw": "he", "in": "id", "ji": "yi", "jw": "jv"}


def norm_lang(code: str | None) -> str | None:
    if not code:
        return None
    c = code.strip().lower().replace("_", "-")
    head, _, tail = c.partition("-")
    head = LANG_ALIASES.get(head, head)
    return f"{head}-{tail}" if tail else head


def base_lang(code: str | None) -> str | None:
    c = norm_lang(code)
    return c.split("-")[0] if c else None


def glob_escape(name: str) -> str:
    return re.sub(r"([\[\]*?])", r"[\1]", name)


def safe_filename(name: str, max_len: int = 140) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(". ")
    return (name[:max_len].rstrip(". ") or "episode")


def setup_logging(cfg) -> None:
    log_dir = Path(os.environ.get("DUB_LOG_DIR") or cfg.get("log_dir") or (BASE / "logs"))
    if not log_dir.is_absolute():
        log_dir = BASE / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    log.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    fh = logging.FileHandler(log_dir / "dub_downloader.log", encoding="utf-8")
    fh.setFormatter(fmt)
    log.handlers[:] = [sh, fh]
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows-Konsole: Umlaute/Asiatisch
    except Exception:
        pass


class RunLock:
    """Verhindert, dass zwei gleichartige Läufe gleichzeitig laufen."""

    def __init__(self, name: str = "run"):
        global LOCK_FILE
        self.file = BASE / (".running.lock" if name != "upload" else ".upload.lock")
        LOCK_FILE = self.file

    def __enter__(self):
        if LOCK_FILE.exists():
            age = time.time() - LOCK_FILE.stat().st_mtime
            if age < 6 * 3600:
                log.warning("Ein anderer Lauf ist noch aktiv (Lock %d min alt) – beende.", age // 60)
                raise SystemExit(0)
            log.warning("Alter Lock gefunden (>6 h) – wird übernommen.")
        LOCK_FILE.write_text(str(os.getpid()))
        return self

    def __exit__(self, *exc):
        try:
            LOCK_FILE.unlink()
        except FileNotFoundError:
            pass


# --------------------------------------------------------------------------- YouTube
def ydl_base_opts(cfg) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "ignoreerrors": False,
        "retries": 5,
        "socket_timeout": 30,
        "sleep_interval_requests": cfg.get("sleep_between_requests", 1),
        # Löst YouTubes JS-Challenge (sonst wird der Download stark gedrosselt)
        "remote_components": list(cfg.get("remote_components", ["ejs:github"])),
    }
    if cfg.get("deno_path"):
        opts["js_runtimes"] = {"deno": {"path": cfg["deno_path"]}}
    if cfg.get("ffmpeg_location"):
        opts["ffmpeg_location"] = cfg["ffmpeg_location"]
    cf = cfg.get("cookies_file")
    if cf and not os.path.isabs(cf):
        cf = str(BASE / cf)
    if cf and os.path.exists(cf) and os.path.getsize(cf) > 0:
        opts["cookiefile"] = cf
    elif cfg.get("cookies_from_browser"):
        opts["cookiesfrombrowser"] = (cfg["cookies_from_browser"],)
    return opts


def list_channel_videos(cfg, limit: int | None) -> list[dict]:
    url = cfg["youtube_channel_url"].rstrip("/")
    sources = cfg.get("source_urls") or [f"{url}/{t}" for t in (cfg.get("channel_tabs") or ["videos"])]
    videos, seen = [], set()
    for src in sources:
        opts = ydl_base_opts(cfg) | {"extract_flat": "in_playlist"}
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(src, download=False)
        except Exception as e:
            log.warning("Quelle %s nicht lesbar: %s", src, str(e).splitlines()[0])
            continue
        min_dur = cfg.get("min_duration_seconds", 0)
        entries = list((info or {}).get("entries") or [])
        skipped = 0
        log.info("Quelle: %d Einträge", len(entries))
        for e in entries:
            if limit and len(videos) >= limit:
                break
            vid = e.get("id")
            dur = e.get("duration")
            if min_dur and (("/shorts/" in (e.get("url") or "")) or (dur is not None and dur < min_dur)):
                skipped += 1
                continue  # Shorts überspringen
            if vid and vid not in seen:
                seen.add(vid)
                videos.append({"id": vid, "title": e.get("title")})
        log.info("Davon %d Shorts übersprungen", skipped)
    log.info("Kanal: %d Videos gefunden", len(videos))
    return videos


def video_info(cfg, video_id: str, lang: str | None = None) -> dict:
    opts = ydl_base_opts(cfg)
    if lang:
        # Metadaten (Titel/Beschreibung) in der Zielsprache, falls YouTube sie liefert
        opts["extractor_args"] = {"youtube": {"lang": [lang]}}
    with YoutubeDL(opts) as ydl:
        return ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)


def find_dub_tracks(info: dict, cfg) -> dict[str, dict]:
    """Liefert {sprache: bestes_audio_format} für alle Dub-Spuren (ohne Original, ohne ausgeschlossene)."""
    audio = [
        f for f in info.get("formats") or []
        if f.get("acodec") not in (None, "none")
        and f.get("vcodec") in (None, "none")
        and norm_lang(f.get("language"))
        and "descriptive" not in (f.get("format_note") or "").lower()
    ]
    langs = {norm_lang(f["language"]) for f in audio}
    if len(langs) < 2:
        return {}  # nur eine Tonspur -> kein Dub

    # Originalsprache bestimmen
    orig = None
    for f in audio:
        if "original" in (f.get("format_note") or "").lower():
            orig = norm_lang(f["language"])
            break
    if not orig:
        best = max(audio, key=lambda f: f.get("language_preference") or -100)
        if (best.get("language_preference") or -100) >= 10:
            orig = norm_lang(best["language"])
    if not orig:
        orig = norm_lang(info.get("language"))

    excluded = {base_lang(x) for x in cfg.get("exclude_languages", [])}
    only = {base_lang(x) for x in cfg.get("only_languages") or []}

    result: dict[str, dict] = {}
    for f in audio:
        lang = norm_lang(f["language"])
        if lang == orig or base_lang(lang) == base_lang(orig):
            continue
        if base_lang(lang) in excluded:
            continue
        if only and base_lang(lang) not in only:
            continue
        cur = result.get(lang)
        score = (f.get("abr") or f.get("tbr") or 0, 1 if f.get("ext") == "m4a" else 0)
        if not cur or score > (cur.get("abr") or cur.get("tbr") or 0, 1 if cur.get("ext") == "m4a" else 0):
            result[lang] = f
    return result


def thumbnail_url(info: dict) -> str | None:
    vid = info.get("id")
    for name in ("maxresdefault.jpg", "sddefault.jpg", "hqdefault.jpg"):
        url = f"https://i.ytimg.com/vi/{vid}/{name}"
        try:
            r = requests.head(url, timeout=15)
            if r.status_code == 200:
                return url
        except requests.RequestException:
            pass
    return info.get("thumbnail")


def download_dub(cfg, info: dict, lang: str, fmt: dict, dry: bool) -> dict | None:
    vid = info["id"]
    out_root = Path(os.environ.get("DUB_DIR") or cfg["download_dir"])
    if not out_root.is_absolute():
        out_root = BASE / out_root
    lang_dir = out_root / lang
    lang_dir.mkdir(parents=True, exist_ok=True)

    # lokalisierte Metadaten holen
    title, desc = info.get("title") or vid, info.get("description") or ""
    if cfg.get("localized_metadata", True):
        try:
            li = video_info(cfg, vid, YT_CODES.get(base_lang(lang), base_lang(lang)))
            title = li.get("title") or title
            desc = li.get("description") or desc
        except Exception as e:  # nicht kritisch
            log.debug("Lokalisierte Metadaten fehlgeschlagen: %s", e)

    stem = safe_filename(f"{title} [{lang}]")
    target = lang_dir / f"{stem}.mp3"
    if dry:
        log.info("  [dry-run] würde laden: %s", target)
        return None

    opts = ydl_base_opts(cfg) | {
        "format": fmt["format_id"],
        "outtmpl": str(lang_dir / f"{stem}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": str(cfg.get("mp3_bitrate", 192)),
        }],
        "overwrites": True,
    }
    if cfg.get("audio_channels"):
        opts["postprocessor_args"] = {"ExtractAudio": ["-ac", str(cfg["audio_channels"])]}
    if cfg.get("ffmpeg_location"):
        opts["ffmpeg_location"] = cfg["ffmpeg_location"]
    with YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={vid}"])
    if not target.exists():
        raise RuntimeError(f"MP3 nicht gefunden nach Download: {target}")

    transcript = None

    # Cover (YouTube-Thumbnail) für Spreaker
    cover = None
    turl = thumbnail_url(info) if cfg.get("episode_cover", False) else None
    if turl:
        try:
            r = requests.get(turl, timeout=30)
            r.raise_for_status()
            cover = lang_dir / f"{stem}.jpg"
            cover.write_bytes(r.content)
        except requests.RequestException as e:
            log.warning("  Thumbnail nicht geladen: %s", e)

    # Metadaten neben die MP3 legen (für manuelle Uploads praktisch)
    meta = {
        "video_id": vid,
        "language": lang,
        "title": title,
        "description": desc,
        "youtube_url": f"https://youtu.be/{vid}",
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration"),
        "tags": (info.get("tags") or [])[:20],
        "file": str(target),
        "cover": str(cover) if cover else None,
        "transcript": transcript,
        "downloaded_at": now_iso(),
    }
    target.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def fetch_transcript(cfg, vid: str) -> str | None:
    """Lädt das (automatische) englische Transkript einmal pro Video als Text."""
    tdir = Path(os.environ.get("DUB_DIR") or cfg["download_dir"])
    if not tdir.is_absolute():
        tdir = BASE / tdir
    tdir = tdir / "_transkripte"
    tdir.mkdir(parents=True, exist_ok=True)
    out_txt = tdir / f"{vid}.txt"
    if out_txt.exists():
        return str(out_txt)
    opts = ydl_base_opts(cfg) | {
        "skip_download": True, "writesubtitles": True, "writeautomaticsub": True,
        "subtitleslangs": ["en.*", "en"], "subtitlesformat": "vtt",
        "outtmpl": str(tdir / f"{vid}.%(ext)s"),
    }
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={vid}"])
    except Exception as e:
        log.warning("  Transkript nicht geladen: %s", str(e).splitlines()[0])
        return None
    vtts = sorted(tdir.glob(f"{vid}*.vtt"))
    if not vtts:
        return None
    lines, last = [], ""
    for line in vtts[0].read_text(encoding="utf-8", errors="ignore").splitlines():
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")) or line.isdigit():
            continue
        if line != last:
            lines.append(line)
            last = line
    out_txt.write_text(" ".join(lines), encoding="utf-8")
    for v in vtts:
        v.unlink()
    log.info("  📝 Transkript gespeichert")
    return str(out_txt)


YT_CODES = {"he": "iw", "id": "id"}


def fetch_dub_transcript(cfg, vid: str, lang: str, lang_dir: Path, stem: str) -> str | None:
    """Automatisches YouTube-Transkript in der Dub-Sprache als <stem>.vtt."""
    final = lang_dir / f"{stem}.vtt"
    if final.exists():
        return str(final)
    code = YT_CODES.get(base_lang(lang), base_lang(lang))
    opts = ydl_base_opts(cfg) | {
        "skip_download": True, "writeautomaticsub": True, "writesubtitles": True,
        "subtitleslangs": [code, f"{code}-.*"], "subtitlesformat": "vtt",
        "outtmpl": str(lang_dir / f"{stem}.%(ext)s"),
    }
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={vid}"])
    except Exception as e:
        log.warning("  Transkript (%s) nicht geladen: %s", lang, str(e).splitlines()[0])
        return None
    vtts = sorted(lang_dir.glob(glob_escape(stem) + ".*.vtt"))
    if not vtts:
        log.warning("  Kein Transkript für %s gefunden", lang)
        return None
    os.replace(vtts[0], final)
    for extra in vtts[1:]:
        extra.unlink(missing_ok=True)
    return str(final)


_WHISPER = None


def _whisper_model(cfg):
    """Lädt Whisper einmal: GPU (CUDA) wenn möglich, sonst CPU."""
    global _WHISPER
    if _WHISPER is not None:
        return _WHISPER
    import importlib.util
    # CUDA-DLLs aus den pip-Paketen nvidia-* bekannt machen (ohne PATH zu ändern)
    spec = importlib.util.find_spec("nvidia")
    if spec and spec.submodule_search_locations and hasattr(os, "add_dll_directory"):
        for root in spec.submodule_search_locations:
            for b in Path(root).glob("*/bin"):
                try:
                    os.add_dll_directory(str(b))
                    os.environ["PATH"] = str(b) + os.pathsep + os.environ.get("PATH", "")  # nur für diesen Prozess
                except OSError:
                    pass
    from faster_whisper import WhisperModel
    size = cfg.get("whisper_model", "large-v3-turbo")
    try:
        _WHISPER = WhisperModel(size, device="cuda", compute_type="float16")
        log.info("Whisper %s läuft auf der GPU", size)
    except Exception as e:
        log.warning("GPU nicht nutzbar (%s) – Whisper läuft auf der CPU", str(e).splitlines()[0][:120])
        _WHISPER = WhisperModel(cfg.get("whisper_model_cpu", "small"), device="cpu", compute_type="int8")
    return _WHISPER


def _decode_audio(cfg, f: Path):
    """MP3 -> 16 kHz Mono float32 per FFmpeg (umgeht PyAV-Versionsprobleme)."""
    import subprocess
    import numpy as np
    ff = "ffmpeg"
    if cfg.get("ffmpeg_location"):
        cand = Path(cfg["ffmpeg_location"]) / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if cand.exists():
            ff = str(cand)
    raw = subprocess.run([ff, "-nostdin", "-v", "error", "-i", str(f), "-f", "s16le", "-ac", "1",
                          "-ar", "16000", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def _ts(sec: float) -> str:
    h, r = divmod(sec, 3600)
    m, s_ = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{s_:06.3f}"


def whisper_transcribe(cfg, meta: dict) -> str | None:
    f = Path(meta["file"])
    out = f.with_suffix(".vtt")
    if out.exists():
        return str(out)
    if not f.exists():
        return None
    model = _whisper_model(cfg)
    lang = base_lang(meta["language"])
    t0 = time.time()
    audio = _decode_audio(cfg, f)
    segments, _info = model.transcribe(audio, language=lang, vad_filter=True, beam_size=5)
    lines = ["WEBVTT", ""]
    for seg in segments:
        lines += [f"{_ts(seg.start)} --> {_ts(seg.end)}", seg.text.strip(), ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    log.info("  📝 %s (%ds)", out.name, time.time() - t0)
    return str(out)


def fetch_video_transcripts(cfg, vid: str, items: list[dict]) -> int:
    """Holt die Transkripte ALLER Dub-Sprachen eines Videos in einem einzigen Abruf
    (mit Pausen zwischen den Untertiteln, gegen YouTubes 429-Sperre) und legt sie
    als <stem>.vtt neben die jeweilige MP3."""
    todo = [m for m in items if not (m.get("transcript") and Path(m["transcript"]).exists())]
    if not todo:
        return 0
    base = Path(os.environ.get("DUB_DIR") or cfg["download_dir"])
    if not base.is_absolute():
        base = BASE / base
    tmp = base / "_transkripte" / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    codes = sorted({YT_CODES.get(base_lang(m["language"]), base_lang(m["language"])) for m in todo})
    opts = ydl_base_opts(cfg) | {
        "skip_download": True, "writeautomaticsub": True, "writesubtitles": True,
        "subtitleslangs": codes, "subtitlesformat": "vtt",
        "sleep_interval_subtitles": cfg.get("sleep_between_subtitles", 6),
        "outtmpl": str(tmp / f"{vid}.%(ext)s"),
        "ignoreerrors": True,
    }
    for attempt in range(3):
        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={vid}"])
        except Exception as e:
            log.warning("  Transkripte: %s", str(e).splitlines()[0])
        missing = [c for c in codes if not (tmp / f"{vid}.{c}.vtt").exists()]
        if not missing:
            break
        wait = 60 * (attempt + 1)
        log.info("  %d Transkripte fehlen noch (%s) – warte %ds", len(missing), ", ".join(missing), wait)
        time.sleep(wait)
        opts["subtitleslangs"] = missing
    n = 0
    for m in todo:
        code = YT_CODES.get(base_lang(m["language"]), base_lang(m["language"]))
        src = tmp / f"{vid}.{code}.vtt"
        if src.exists():
            f = Path(m["file"])
            dst = f.with_suffix(".vtt")
            dst.write_bytes(src.read_bytes())
            m["transcript"] = str(dst)
            f.with_suffix(".json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
            n += 1
    for c in codes:
        (tmp / f"{vid}.{c}.vtt").unlink(missing_ok=True)
    log.info("  📝 %d/%d Transkripte", n, len(todo))
    return n


def needs_check(entry: dict | None, cfg, full: bool, vid: str = "", state: dict | None = None) -> bool:
    if full or not entry:
        return True
    if state is not None and any(f"{vid}:{l}" not in state["downloads"] and resolve_show(l, cfg, [])
                                 for l in entry.get("dubs") or []):
        return True  # offene Dubs (z. B. fehlgeschlagener Upload) erneut versuchen
    last = dt.datetime.fromisoformat(entry["checked_at"])
    age_h = (dt.datetime.now(dt.timezone.utc) - last).total_seconds() / 3600
    up = entry.get("upload_date")
    recent = False
    if up:
        d = dt.datetime.strptime(up, "%Y%m%d").replace(tzinfo=dt.timezone.utc)
        recent = (dt.datetime.now(dt.timezone.utc) - d).days <= cfg.get("recheck_days", 45)
    # Neue Videos werden regelmäßig erneut geprüft, weil YouTube Dubs oft erst später ergänzt
    return recent and age_h >= cfg.get("recheck_interval_hours", 20)


def _delete_files(meta: dict) -> None:
    f = Path(meta["file"])
    for p in (f, f.with_suffix(".jpg"), f.with_suffix(".json")):
        try:
            p.unlink()
        except FileNotFoundError:
            pass


def cmd_download(cfg, state, args) -> int:
    cloud = cfg.get("cloud_mode") or os.environ.get("CLOUD_MODE") == "1"
    sp = shows = None
    if cloud and not args.dry_run:
        sp = spreaker_client(cfg)
        shows = load_shows(cfg, sp)
    videos = list_channel_videos(cfg, args.limit or cfg.get("max_videos_to_scan"))
    max_dl = cfg.get("max_downloads_per_run", 200)
    done = 0
    for i, v in enumerate(videos, 1):
        vid = v["id"]
        entry = state["videos"].get(vid)
        if not needs_check(entry, cfg, args.full_rescan, vid, state):
            continue
        try:
            info = video_info(cfg, vid)
        except Exception as e:
            log.warning("[%d/%d] %s übersprungen: %s", i, len(videos), vid, str(e).splitlines()[0])
            continue
        if info.get("live_status") in ("is_live", "is_upcoming"):
            continue
        dubs = find_dub_tracks(info, cfg)
        state["videos"][vid] = {
            "title": info.get("title"),
            "upload_date": info.get("upload_date"),
            "dubs": sorted(dubs),
            "checked_at": now_iso(),
        }
        missing = [l for l in sorted(dubs) if f"{vid}:{l}" not in state["downloads"]]
        if dubs:
            log.info("[%d/%d] %s – Dubs: %s | neu: %s", i, len(videos), info.get("title"),
                     ", ".join(sorted(dubs)), ", ".join(missing) or "–")
        for lang in missing:
            if cloud and sp is not None and not resolve_show(lang, cfg, shows):
                if cfg.get("create_missing_shows"):
                    if create_missing_show(lang, cfg, sp, False):
                        shows = load_shows(cfg, sp, refresh=True)
                if not resolve_show(lang, cfg, shows):
                    log.info("  [%s] keine Spreaker-Show – übersprungen", lang)
                    continue
            if done >= max_dl:
                log.info("Limit von %d Downloads pro Lauf erreicht.", max_dl)
                save_json(STATE_FILE, state)
                return done
            log.info("  ↓ lade %s ...", lang)
            try:
                meta = download_dub(cfg, info, lang, dubs[lang], args.dry_run)
            except Exception as e:
                log.error("  Download %s [%s] fehlgeschlagen: %s", vid, lang, str(e).splitlines()[0])
                continue
            if meta:
                key = f"{vid}:{lang}"
                state["downloads"][key] = meta | {"uploaded": None}
                done += 1
                log.info("  ✔ %s", Path(meta["file"]).name)
                if cloud and sp is not None:
                    sid = resolve_show(lang, cfg, shows)
                    try:
                        ep = sp.upload_episode(sid, episode_payload(meta, cfg), Path(meta["file"]),
                                               Path(meta["cover"]) if meta.get("cover") else None)
                        state["downloads"][key]["uploaded"] = {"show_id": sid, "episode_id": ep.get("episode_id"),
                                                               "at": now_iso()}
                        log.info("  ⬆ Show %s (Episode %s)", sid, ep.get("episode_id"))
                    except Exception as e:
                        log.error("  Upload fehlgeschlagen: %s", e)
                        del state["downloads"][key]  # beim nächsten Lauf neu versuchen
                    _delete_files(meta)
                    state["downloads"].get(key, {}).pop("description", None)
                save_json(STATE_FILE, state)
        if cfg.get("fetch_transcripts", True) and not args.dry_run:
            items = [m for k, m in state["downloads"].items() if k.startswith(vid + ":")]
            for m in items:
                if cfg.get("transcript_engine", "whisper") == "whisper_inline":
                    try:
                        t = whisper_transcribe(cfg, m)
                    except Exception as e:
                        log.error("  Whisper-Fehler (%s): %s", m["language"], e)
                        t = None
                    if t:
                        m["transcript"] = t
                        Path(m["file"]).with_suffix(".json").write_text(
                            json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
            if items and cfg.get("transcript_engine", "whisper") == "youtube":
                fetch_video_transcripts(cfg, vid, items)
        save_json(STATE_FILE, state)
    log.info("Download fertig: %d neue Dub-Dateien.", done)
    return done


# --------------------------------------------------------------------------- Spreaker
class Spreaker:
    def __init__(self, token: str, cfg: dict | None = None):
        self.cfg = cfg
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"

    def _req(self, method: str, path: str, **kw):
        url = path if path.startswith("http") else f"{API}{path}"
        timeout = kw.pop("timeout", 120)
        for attempt in range(5):
            r = self.s.request(method, url, timeout=timeout, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                wait = int(r.headers.get("Retry-After", 0)) or 10 * (attempt + 1)
                log.warning("Spreaker %s – warte %ds", r.status_code, wait)
                time.sleep(wait)
                continue
            if r.status_code == 401 and self.cfg and attempt == 0 and refresh_access_token(self.cfg):
                self.s.headers["Authorization"] = f"Bearer {self.cfg['spreaker_token']}"
                for f in (kw.get("files") or {}).values():
                    try:
                        f[1].seek(0)
                    except Exception:
                        pass
                continue
            if r.status_code >= 400:
                raise RuntimeError(f"Spreaker {method} {path}: {r.status_code} {r.text[:300]}")
            return r.json().get("response", {})
        raise RuntimeError(f"Spreaker {method} {path}: zu viele Fehlversuche")

    def me(self) -> dict:
        return self._req("GET", "/me")["user"]

    def user_shows(self, user_id) -> list[dict]:
        items, url = [], f"/users/{user_id}/shows?limit=100"
        while url:
            resp = self._req("GET", url)
            items += resp.get("items", [])
            url = resp.get("next_url")
        return items

    def show(self, show_id) -> dict:
        return self._req("GET", f"/shows/{show_id}")["show"]

    def create_show(self, data: dict) -> dict:
        return self._req("POST", "/shows", data=data)["show"]

    def update_show(self, show_id, data: dict) -> dict:
        return self._req("POST", f"/shows/{show_id}", data=data)["show"]

    def upload_episode(self, show_id, data: dict, media: Path, image: Path | None) -> dict:
        files = {"media_file": (media.name, media.open("rb"), "audio/mpeg")}
        if image and image.exists():
            files["image_file"] = (image.name, image.open("rb"), "image/jpeg")
        try:
            return self._req("POST", f"/shows/{show_id}/episodes", data=data, files=files,
                             timeout=1800)["episode"]
        finally:
            for f in files.values():
                f[1].close()


def spreaker_client(cfg) -> Spreaker:
    token = os.environ.get("SPREAKER_TOKEN") or cfg.get("spreaker_token")
    if not token or token.startswith("HIER"):
        log.error("Kein Spreaker-Token. Bitte 'run_dubs.bat login' ausfuehren.")
        raise SystemExit(2)
    return Spreaker(token, cfg)


def load_shows(cfg, sp: Spreaker, refresh: bool = False) -> list[dict]:
    cache = load_json(SHOWS_CACHE, {})
    if cache and not refresh:
        age = time.time() - SHOWS_CACHE.stat().st_mtime
        if age < 24 * 3600:
            return cache["shows"]
    owners = cfg.get("spreaker_user_ids") or [sp.me()["user_id"]]
    shows = []
    for uid in owners:
        for s in sp.user_shows(uid):
            try:
                full = sp.show(s["show_id"])
            except Exception:
                full = s
            shows.append({"show_id": full["show_id"], "title": full.get("title"),
                          "language": norm_lang(full.get("language"))})
    # zusätzlich manuell eingetragene Show-IDs (z. B. Netzwerk-Shows anderer Accounts)
    known = {s["show_id"] for s in shows}
    for lang, sid in (cfg.get("show_map") or {}).items():
        if sid and int(sid) not in known:
            try:
                full = sp.show(sid)
                shows.append({"show_id": full["show_id"], "title": full.get("title"),
                              "language": norm_lang(full.get("language"))})
            except Exception as e:
                log.warning("Show %s (%s) nicht lesbar: %s", sid, lang, e)
    save_json(SHOWS_CACHE, {"updated": now_iso(), "shows": shows})
    return shows


def resolve_show(lang: str, cfg, shows: list[dict]) -> int | None:
    m = {norm_lang(k): v for k, v in (cfg.get("show_map") or {}).items() if v}
    if lang in m:
        return int(m[lang])
    if base_lang(lang) in m:
        return int(m[base_lang(lang)])
    if not cfg.get("auto_map_by_language", False):
        return None  # nur feste Zuordnung aus show_map (verhindert Uploads in fremde Shows)
    exclude_ids = {int(x) for x in cfg.get("never_auto_map_show_ids", [])}
    cands = [s for s in shows if s["show_id"] not in exclude_ids and s.get("language")]
    for s in cands:
        if s["language"] == lang:
            return s["show_id"]
    for s in cands:
        if base_lang(s["language"]) == base_lang(lang):
            return s["show_id"]
    return None


def create_missing_show(lang: str, cfg, sp: Spreaker, dry: bool) -> int | None:
    seo = load_json(SEO_FILE, {})
    entry = seo.get(lang) or seo.get(base_lang(lang))
    if not entry:
        log.error("Keine SEO-Texte für '%s' in shows_seo.json – Show nicht angelegt.", lang)
        return None
    data = {"title": entry["title"], "description": entry["description"],
            "language": base_lang(lang), "explicit": "false"}
    if cfg.get("spreaker_category_id"):
        data["category_id"] = cfg["spreaker_category_id"]
    for k in ("website_url", "email"):
        if cfg.get("show_" + k):
            data[k] = cfg["show_" + k]
    if dry:
        log.info("[dry-run] würde Show anlegen: %s", entry["title"])
        return None
    show = sp.create_show(data)
    log.info("Neue Show angelegt: %s (ID %s)", show.get("title"), show["show_id"])
    cfg.setdefault("show_map", {})[base_lang(lang)] = show["show_id"]
    save_json(CONFIG_FILE, cfg)
    SHOWS_CACHE.unlink(missing_ok=True)
    return show["show_id"]


def episode_payload(meta: dict, cfg) -> dict:
    title = meta["title"][:140]
    desc = (meta.get("description") or "").strip()
    footer = cfg.get("episode_footer", "").format(youtube_url=meta["youtube_url"])
    body = (desc + "\n\n" + footer).strip() if footer else desc
    data = {
        "title": title,
        "description": body[:4000],
        "visibility": cfg.get("upload_visibility", "PRIVATE"),
        "download_enabled": "true",
    }
    tags = [t for t in meta.get("tags") or [] if len(t) <= 40][:10]
    if tags:
        data["tags"] = ",".join(tags)
    return data


EPISODES_BASE = "https://raw.githubusercontent.com/Mirko-Peters/m365-dub-downloader/main/episodes"
_TEXT_CACHE: dict = {}
_COVER_CACHE: dict = {}
_TITLES_CACHE: dict = {}


def episode_texts(vid: str) -> dict:
    """Übersetzte Titel/Beschreibungen/Transkript-Links aus dem GitHub-Repo (von Claude geschrieben)."""
    if vid not in _TEXT_CACHE:
        try:
            r = requests.get(f"{EPISODES_BASE}/{vid}.json", params={"t": int(time.time())}, timeout=30)
            _TEXT_CACHE[vid] = r.json() if r.status_code == 200 else {}
        except Exception:
            _TEXT_CACHE[vid] = {}
    return _TEXT_CACHE[vid]


def show_cover(sp: "Spreaker", show_id) -> Path | None:
    if show_id not in _COVER_CACHE:
        try:
            url = sp.show(show_id).get("image_original_url")
            f = BASE / "_runtime" / "covers" / f"{show_id}.jpg"
            f.parent.mkdir(parents=True, exist_ok=True)
            if not f.exists() and url:
                f.write_bytes(requests.get(url, timeout=60).content)
            _COVER_CACHE[show_id] = f if f.exists() else None
        except Exception as e:
            log.warning("Show-Cover %s nicht geladen: %s", show_id, e)
            _COVER_CACHE[show_id] = None
    return _COVER_CACHE[show_id]


def show_titles(sp: "Spreaker", show_id) -> set:
    if show_id not in _TITLES_CACHE:
        titles, url = set(), f"/shows/{show_id}/episodes?limit=100"
        try:
            while url:
                resp = sp._req("GET", url)
                titles |= {e.get("title", "").strip() for e in resp.get("items", [])}
                url = resp.get("next_url")
        except Exception as e:
            log.warning("Episodenliste %s nicht lesbar: %s", show_id, e)
        _TITLES_CACHE[show_id] = titles
    return _TITLES_CACHE[show_id]


def cmd_upload(cfg, state, args) -> int:
    if cfg.get("upload_mode", "texts") == "texts":
        return cmd_upload_texts(cfg, state, args)
    return cmd_upload_basic(cfg, state, args)


UPLOADED_FILE = BASE / "uploaded.json"


def cmd_upload_texts(cfg, state, args) -> int:
    """Upload mit Claudes übersetzten Texten aus dem Repo – nur Folgen, für die Texte existieren.
    Merkt sich Uploads in uploaded.json (unabhängig vom laufenden Download)."""
    sp = spreaker_client(cfg)
    done = load_json(UPLOADED_FILE, {})
    pending = [m for k, m in state["downloads"].items()
               if not m.get("uploaded") and f"{m['video_id']}:{m['language']}" not in done]
    n = skipped = 0
    for meta in sorted(pending, key=lambda m: (m.get("upload_date") or "", m["video_id"], m["language"])):
        lang = base_lang(meta["language"])
        t = episode_texts(meta["video_id"]).get(lang)
        if not t:
            skipped += 1
            continue
        sid = int(t.get("show") or resolve_show(meta["language"], cfg, []) or 0)
        if not sid:
            continue
        if t["title"].strip() in show_titles(sp, sid):
            done[f"{meta['video_id']}:{meta['language']}"] = {"show_id": sid, "episode_id": None, "at": now_iso(), "note": "bereits vorhanden"}
            save_json(UPLOADED_FILE, done)
            log.info("= schon online: %s", t["title"])
            continue
        media = Path(meta["file"])
        if not media.exists():
            log.warning("Datei fehlt: %s", media)
            continue
        data = {"title": t["title"][:140], "description": t["desc"], "visibility": "PUBLIC",
                "ai_generated": "true", "episode_link": cfg.get("show_website_url", "https://www.m365.fm"),
                "download_enabled": "true"}
        if t.get("tags"):
            data["tags"] = t["tags"]
        if t.get("tr"):
            data["transcript_url"] = t["tr"]
            data["transcript_type"] = "text/vtt"
        if args.dry_run:
            log.info("[dry-run] %s -> Show %s", t["title"], sid)
            continue
        try:
            ep = sp.upload_episode(sid, data, media, show_cover(sp, sid))
        except Exception as e:
            log.error("Upload fehlgeschlagen (%s): %s", media.name, e)
            continue
        eid = ep.get("episode_id")
        done[f"{meta['video_id']}:{meta['language']}"] = {"show_id": sid, "episode_id": eid, "at": now_iso(), "title": t["title"],
                                                          "transcript": t.get("tr") or None}
        show_titles(sp, sid).add(t["title"].strip())
        save_json(UPLOADED_FILE, done)
        n += 1
        log.info("⬆ %s -> Show %s (Episode %s)", t["title"], sid, eid)
        if t.get("tr") and eid:
            try:
                sp._req("POST", f"/episodes/{eid}", data={"transcript_url": t["tr"], "transcript_type": "text/vtt",
                                                          "ai_generated": "true"})
                e2 = sp._req("GET", f"/episodes/{eid}")["episode"]
                log.info("  Transkript %s, KI-Kennzeichnung %s",
                         "gesetzt" if e2.get("transcript_url") else "NICHT gesetzt", e2.get("ai_generated"))
            except Exception as e:
                log.warning("  Transkript-Update fehlgeschlagen: %s", e)
        if n >= cfg.get("max_uploads_per_run", 100):
            break
    # Transkripte nachreichen: veröffentlichte Folgen ohne Transkript, für die jetzt eins im Repo liegt
    fixed = 0
    for key, info in done.items():
        if info.get("transcript") or not info.get("episode_id") and info.get("note") != "bereits vorhanden":
            continue
        vid, lang = key.split(":", 1)
        t = episode_texts(vid).get(base_lang(lang)) or {}
        if not t.get("tr"):
            continue
        eid = info.get("episode_id")
        if not eid:  # per Chrome hochgeladen: Episode über den Titel finden
            try:
                items = sp._req("GET", f"/shows/{t['show']}/episodes?limit=100").get("items", [])
                eid = next((e["episode_id"] for e in items if e.get("title", "").strip() == t["title"].strip()), None)
            except Exception:
                eid = None
        if not eid or args.dry_run:
            continue
        try:
            cur = sp._req("GET", f"/episodes/{eid}")["episode"]
            if not cur.get("transcript_url"):
                sp._req("POST", f"/episodes/{eid}", data={"transcript_url": t["tr"], "transcript_type": "text/vtt"})
                fixed += 1
                log.info("📝 Transkript nachgereicht: %s", t["title"])
            info["episode_id"], info["transcript"] = eid, t["tr"]
            save_json(UPLOADED_FILE, done)
        except Exception as e:
            log.warning("Transkript-Nachtrag %s fehlgeschlagen: %s", key, e)
    log.info("Upload fertig: %d Episoden hochgeladen, %d Transkripte nachgereicht, %d warten noch auf Texte.",
             n, fixed, skipped)
    return n


def cmd_upload_basic(cfg, state, args) -> int:
    pending = {k: v for k, v in state["downloads"].items() if not v.get("uploaded")}
    if not pending:
        log.info("Nichts hochzuladen.")
        return 0
    sp = spreaker_client(cfg)
    shows = load_shows(cfg, sp)
    n, missing_langs = 0, set()
    for key, meta in sorted(pending.items(), key=lambda kv: kv[1].get("upload_date") or ""):
        lang = meta["language"]
        sid = resolve_show(lang, cfg, shows)
        if not sid and cfg.get("create_missing_shows"):
            sid = create_missing_show(lang, cfg, sp, args.dry_run)
            if sid:
                shows = load_shows(cfg, sp, refresh=True)
        if not sid:
            missing_langs.add(lang)
            continue
        media = Path(meta["file"])
        if not media.exists():
            log.warning("Datei fehlt: %s", media)
            continue
        if args.dry_run:
            log.info("[dry-run] %s -> Show %s", media.name, sid)
            continue
        try:
            ep = sp.upload_episode(sid, episode_payload(meta, cfg), media,
                                   Path(meta["cover"]) if meta.get("cover") else None)
        except Exception as e:
            log.error("Upload fehlgeschlagen (%s): %s", media.name, e)
            continue
        meta["uploaded"] = {"show_id": sid, "episode_id": ep.get("episode_id"), "at": now_iso()}
        save_json(STATE_FILE, state)
        n += 1
        log.info("⬆ %s -> Show %s (Episode %s)", media.name, sid, ep.get("episode_id"))
        if n >= cfg.get("max_uploads_per_run", 100):
            break
    if missing_langs:
        log.warning("Keine Spreaker-Show für: %s  ->  'shows --create-missing' ausführen oder show_map ergänzen.",
                    ", ".join(sorted(missing_langs)))
    log.info("Upload fertig: %d Episoden.", n)
    return n


def cmd_shows(cfg, state, args) -> None:
    sp = spreaker_client(cfg)
    shows = load_shows(cfg, sp, refresh=True)
    print(f"\n{'Show-ID':>10}  {'Sprache':<8} Titel")
    for s in sorted(shows, key=lambda s: (s.get("language") or "zz", s["title"] or "")):
        print(f"{s['show_id']:>10}  {s.get('language') or '?':<8} {s['title']}")
    langs = {m["language"] for m in state["downloads"].values()}
    if args.all_languages:
        langs |= set(load_json(SEO_FILE, {}).keys())
    excluded = {base_lang(x) for x in cfg.get("exclude_languages", [])}
    langs = {l for l in langs if base_lang(l) not in excluded}
    print("\nZuordnung Sprache -> Show:")
    missing = []
    for l in sorted(langs):
        sid = resolve_show(l, cfg, shows)
        print(f"  {l:<6} {LANG_NAMES.get(base_lang(l), ''):<15} -> {sid or 'FEHLT'}")
        if not sid:
            missing.append(l)
    if args.create_missing:
        for l in missing:
            create_missing_show(l, cfg, sp, args.dry_run)
    if args.apply_seo:
        seo = load_json(SEO_FILE, {})
        for l in sorted(langs):
            sid = resolve_show(l, cfg, shows)
            e = seo.get(base_lang(l))
            if sid and e and int(sid) not in {int(x) for x in cfg.get("never_auto_map_show_ids", [])}:
                if args.dry_run:
                    print(f"[dry-run] würde Show {sid} umbenennen in: {e['title']}")
                else:
                    sp.update_show(sid, {"title": e["title"], "description": e["description"]})
                    print(f"SEO-Titel/Beschreibung gesetzt: {sid} -> {e['title']}")


# --------------------------------------------------------------------------- Spreaker OAuth2 Login
OAUTH_AUTHORIZE = "https://www.spreaker.com/oauth2/authorize"
OAUTH_TOKEN = "https://api.spreaker.com/oauth2/token"


def _save_tokens(cfg, data: dict) -> None:
    cfg["spreaker_token"] = data["access_token"]
    if data.get("refresh_token"):
        cfg["spreaker_refresh_token"] = data["refresh_token"]
    save_json(CONFIG_FILE, cfg)


def refresh_access_token(cfg) -> bool:
    rt, cid, sec = cfg.get("spreaker_refresh_token"), cfg.get("spreaker_client_id"), cfg.get("spreaker_client_secret")
    if not (rt and cid and sec):
        return False
    r = requests.post(OAUTH_TOKEN, data={"grant_type": "refresh_token", "refresh_token": rt,
                                         "client_id": cid, "client_secret": sec}, timeout=60)
    if r.status_code != 200:
        log.error("Token-Erneuerung fehlgeschlagen: %s %s", r.status_code, r.text[:200])
        return False
    _save_tokens(cfg, r.json())
    log.info("Spreaker-Token erneuert.")
    return True


def cmd_login(cfg, state, args) -> None:
    import getpass, secrets, webbrowser, threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlencode, urlparse, parse_qs
    print("Spreaker-Anmeldung (Daten bleiben nur in deiner config.json auf diesem PC)\n")
    cid = input(f"OAuth2 Client Id [{cfg.get('spreaker_client_id') or ''}]: ").strip() or cfg.get("spreaker_client_id")
    sec = getpass.getpass("OAuth2 Client Secret (Eingabe unsichtbar, Enter = gespeichertes behalten): ").strip() \
        or cfg.get("spreaker_client_secret")
    redirect = cfg.get("spreaker_redirect_uri") or "http://localhost/callback"
    if "m365.fm" in redirect or ":8765" in redirect:
        redirect = "http://localhost/callback"
    if not cid or not sec:
        print("Client Id und Secret werden gebraucht."); return
    st = secrets.token_hex(8)
    got: dict = {}

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if "code" not in got and "error" not in got:
                got.clear()  # z. B. favicon-Abruf ignorieren
            msg = "Anmeldung erhalten – du kannst dieses Fenster schliessen." if "code" in got else "Kein Code erhalten."
            self.wfile.write(f"<html><body style='font-family:sans-serif;padding:40px'><h2>{msg}</h2></body></html>".encode())

        def log_message(self, *a):
            pass

    u = urlparse(redirect)
    try:
        srv = HTTPServer(("127.0.0.1", u.port or 80), H)
    except OSError as e:
        print(f"Port {u.port or 80} ist belegt ({e}). Bitte Programme schliessen, die Port 80 nutzen, und neu starten.")
        return
    def serve():
        import time as _t
        end = _t.time() + 300
        srv.timeout = 5
        while _t.time() < end and "code" not in got and "error" not in got:
            srv.handle_request()

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    url = OAUTH_AUTHORIZE + "?" + urlencode({"client_id": cid, "response_type": "code", "state": st,
                                             "scope": "basic", "redirect_uri": redirect})
    print(f"\nIm Browser oeffnet sich Spreaker. Bitte 'Erlauben' klicken.\n(Callback-URL in der App muss sein: {redirect})\n")
    webbrowser.open(url)
    t.join(timeout=310)
    srv.server_close()
    if "code" not in got:
        print("Kein Code empfangen:", got.get("error_description") or got.get("error") or "Zeitüberschreitung"); return
    if got.get("state") != st:
        print("Sicherheitsprüfung (state) fehlgeschlagen."); return
    r = requests.post(OAUTH_TOKEN, data={"grant_type": "authorization_code", "client_id": cid,
                                         "client_secret": sec, "redirect_uri": redirect, "code": got["code"]}, timeout=60)
    if r.status_code != 200:
        print("Fehler:", r.status_code, r.text[:300]); return
    cfg["spreaker_client_id"], cfg["spreaker_client_secret"], cfg["spreaker_redirect_uri"] = cid, sec, redirect
    _save_tokens(cfg, r.json())
    me = Spreaker(cfg["spreaker_token"]).me()
    print(f"\nFertig - verbunden als: {me.get('fullname')}.")
    input("Enter zum Schliessen")


def cmd_status(cfg, state, args) -> None:
    dls = state["downloads"].values()
    by_lang: dict[str, list[int]] = {}
    for m in dls:
        c = by_lang.setdefault(m["language"], [0, 0])
        c[0] += 1
        c[1] += 1 if m.get("uploaded") else 0
    print(f"Videos geprüft: {len(state['videos'])} | mit Dubs: "
          f"{sum(1 for v in state['videos'].values() if v.get('dubs'))}")
    print(f"{'Sprache':<8}{'geladen':>9}{'hochgeladen':>13}{'offen':>7}")
    for l, (a, b) in sorted(by_lang.items()):
        print(f"{l:<8}{a:>9}{b:>13}{a - b:>7}")


# --------------------------------------------------------------------------- main
def run_transcripts(cfg, state, limit: int | None = None) -> int:
    items = [m for m in state["downloads"].values()
             if not (m.get("transcript") and Path(m["transcript"]).exists())
             and not Path(m["file"]).with_suffix(".vtt").exists()
             and Path(m["file"]).exists()]
    weak = {"ml", "pa", "ta", "te", "bn"}
    items.sort(key=lambda m: (0 if base_lang(m["language"]) == "de" else
                              2 if base_lang(m["language"]) in weak else 1, m.get("upload_date") or ""))
    if limit:
        items = items[:limit]
    log.info("%d Folgen ohne Transkript", len(items))
    n = 0
    for i, m in enumerate(items, 1):
        log.info("[%d/%d] %s", i, len(items), Path(m["file"]).name)
        try:
            t = whisper_transcribe(cfg, m)
        except Exception as e:
            log.error("  Whisper-Fehler: %s", e)
            continue
        if t:
            m["transcript"] = t
            Path(m["file"]).with_suffix(".json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
            save_json(STATE_FILE, state)
            n += 1
    return n


def main() -> None:
    p = argparse.ArgumentParser(description="YouTube-Dubs herunterladen und zu Spreaker hochladen")
    p.add_argument("command", choices=["run", "download", "upload", "shows", "status", "login", "transcripts"])
    p.add_argument("--limit", type=int, help="max. Anzahl Kanal-Videos (neueste zuerst)")
    p.add_argument("--full-rescan", action="store_true", help="alle Videos erneut auf neue Dubs prüfen")
    p.add_argument("--dry-run", action="store_true", help="nur anzeigen, nichts laden/hochladen")
    p.add_argument("--create-missing", action="store_true", help="(shows) fehlende Sprach-Shows anlegen")
    p.add_argument("--all-languages", action="store_true", help="(shows) alle Sprachen aus shows_seo.json berücksichtigen")
    p.add_argument("--apply-seo", action="store_true", help="(shows) SEO-Titel/Beschreibung auch auf bestehende Sprach-Shows schreiben")
    args = p.parse_args()

    cfg = load_json(CONFIG_FILE, None)
    if cfg is None:
        print("config.json fehlt – bitte config.json neben das Script legen.")
        sys.exit(1)
    setup_logging(cfg)
    state = load_json(STATE_FILE, {"videos": {}, "downloads": {}})

    if args.command == "transcripts":
        run_transcripts(cfg, state)
        return
    if args.command == "login":
        return cmd_login(cfg, state, args)
    if args.command == "status":
        return cmd_status(cfg, state, args)
    if args.command == "shows":
        return cmd_shows(cfg, state, args)

    with RunLock("upload" if args.command == "upload" else "run"):
        if args.command in ("run", "download"):
            cmd_download(cfg, state, args)
        if args.command == "run" and cfg.get("transcript_engine", "whisper") == "whisper" and not args.dry_run:
            run_transcripts(cfg, state, limit=cfg.get("max_transcripts_per_run", 120))
        if args.command == "upload" or (args.command == "run" and
                                         (cfg.get("auto_upload") or cfg.get("upload_mode", "texts") == "texts")):
            if cfg.get("spreaker_token"):
                cmd_upload(cfg, state, args)
            else:
                log.warning("Kein Spreaker-Login – Upload übersprungen (spreaker_login.bat ausführen).")


if __name__ == "__main__":
    main()
