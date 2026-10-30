"""Google AdSense-Vorbereitung. Alles ist abgeschaltet, bis data/adsense.json eine Publisher-ID enthaelt und die Seite
unter der eingetragenen Domain (www.m365.fm) ausgeliefert wird. Dann:
- ads.txt im Wurzelverzeichnis, <meta name="google-adsense-account">, adsbygoogle.js im <head>
- feste Anzeigenbloecke (mit reserviertem Platz, Kennzeichnung "Anzeige") nur auf ausreichend langen Inhaltsseiten,
  nie auf Community-, Rechts-, Login- oder noindex-Seiten, nie ueber dem ersten Textabschnitt
- Einwilligung fuer EWR/UK/CH: laeuft ueber die in AdSense eingerichtete Google-Nachricht (zertifizierte CMP, "Datenschutz und Mitteilungen")."""
import json, re
from html import escape
from pathlib import Path

CFG_FILE = Path(__file__).parent / "data" / "adsense.json"
LABEL = {"de": "Anzeige", "en": "Advertisement", "es": "Publicidad", "fr": "Publicité", "it": "Pubblicità", "pt": "Publicidade", "nl": "Advertentie", "pl": "Reklama"}
CSS = ".ad{margin:28px 0;text-align:center;min-height:280px;clear:both}.ad small{display:block;font-size:.72rem;opacity:.65;margin-bottom:4px;letter-spacing:.04em;text-transform:uppercase}.ad ins{display:block}"


def cfg():
    try:
        return json.loads(CFG_FILE.read_text("utf-8"))
    except Exception:
        return {}


def active(base):
    c = cfg()
    pub = (c.get("publisher") or "").strip()
    host = base.split("//")[-1].strip("/")
    return bool(re.fullmatch(r"pub-\d{10,20}", pub)) and host == (c.get("domain") or "")


def status(base):
    c = cfg(); pub = (c.get("publisher") or "").strip(); host = base.split("//")[-1].strip("/")
    return {"publisher_set": bool(pub), "publisher_valid": bool(re.fullmatch(r"pub-\d{10,20}", pub)), "domain": c.get("domain"), "serving_host": host, "active": active(base)}


def ads_txt(base):
    if not active(base):
        return None
    pub = cfg()["publisher"].replace("pub-", "")
    return f"google.com, pub-{pub}, DIRECT, f08c47fec0942fa0\n"


def eligible(base, body, canonical, noindex=False):
    """Seite darf Werbung zeigen: indexierbar, keine Community-/Rechts-/Live-Seite, genug Text. Die Startseite zaehlt mit (AdSense prueft dort die Website)."""
    if not active(base) or noindex:
        return False
    c = cfg(); path = canonical.replace(base, "") or "/"
    if path in ("/", ""):
        return True
    if any(s in path for s in c.get("skip_paths", [])):
        return False
    return len(re.sub(r"<[^>]+>", "", body)) >= int(c.get("min_chars", 2500))


def head(base, body="", canonical="", noindex=False):
    """Meta-Tag (immer, fuer die AdSense-Pruefung) und Skript (nur auf Seiten, die Werbung zeigen duerfen; wichtig fuer Auto-Anzeigen)."""
    if not active(base):
        return ""
    pub = cfg()["publisher"]
    out = f'<meta name="google-adsense-account" content="ca-{pub}">'
    if eligible(base, body, canonical, noindex):
        out += f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-{pub}" crossorigin="anonymous"></script>'
    return out


def _block(lang, slot, pub):
    return (f'<aside class="ad" aria-label="{escape(LABEL.get(lang, LABEL["en"]))}"><small>{escape(LABEL.get(lang, LABEL["en"]))}</small>'
            f'<ins class="adsbygoogle" data-ad-client="ca-{pub}" data-ad-slot="{escape(slot)}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
            '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></aside>')


def inject(base, body, lang, canonical, noindex=False):
    """Fuegt hoechstens zwei Bloecke ein: einen nach dem 2. Abschnitt (<h2>), einen vor dem Footer."""
    if not active(base) or noindex:
        return body
    c = cfg()
    path = canonical.replace(base, "") or "/"
    if path in ("/", "") or not eligible(base, body, canonical, noindex):
        return body
    pub, slots = c["publisher"], c.get("slots", {})
    if slots.get("mid"):
        parts = re.split(r"(?=<h2\b)", body)
        if len(parts) > 3:   # Einleitung + mindestens zwei Abschnitte davor
            parts.insert(3, _block(lang, slots["mid"], pub))
            body = "".join(parts)
    if slots.get("end") and "<footer>" in body:
        body = body.replace("<footer>", _block(lang, slots["end"], pub) + "<footer>", 1)
    return body
