"""Sprachen der Community-Seiten: en/de sind vollständig gepflegt, die weiteren (fr, es, it, nl, pt, pl) übersetzen die Oberfläche
(data/ui_i18n.json); Inhalte ohne Übersetzung fallen auf Englisch zurück. Seiten der weiteren Sprachen sind noindex."""
import json
from pathlib import Path

COMM_LANGS = ("en", "de", "fr", "es", "it", "nl", "pt", "pl")
_P = Path(__file__).parent / "data" / "ui_i18n.json"
_D = json.loads(_P.read_text("utf-8")) if _P.exists() else {}


def pfx(lang):
    """URL-Präfix mit führendem Schrägstrich: '' (en) oder '/de'."""
    return "" if lang == "en" else "/" + lang


def pfx2(lang):
    """Präfix ohne führenden Schrägstrich: '' oder 'de/'."""
    return "" if lang == "en" else lang + "/"


def overlay(name, S):
    """Ergänzt S um die weiteren Sprachen (Englisch als Grundlage, Übersetzungen darübergelegt)."""
    for lg in COMM_LANGS[2:]:
        S[lg] = {**S["en"], **_D.get(lg, {}).get(name, {})}
    return S


UI_JS_LANGS = COMM_LANGS[2:]
_JS = Path(__file__).parent / "data" / "ui_js_i18n.json"


def write_ui_js(out):
    """Schreibt assets/ui-<sprache>.js: Übersetzungen der Oberflächen-Skripte (assets/*.js) und die Hilfsfunktion M365L (Englisch als Rückfall)."""
    tr = json.loads(_JS.read_text("utf-8")) if _JS.exists() else {}
    try:   # Übersetzungen aus der Community-API (Worker übersetzt mit Haiku) ergänzen
        import urllib.request, os
        api = os.environ.get("COMMUNITY_API", "https://api-dub.m365.fm")
        with urllib.request.urlopen(api + "/api/ui-i18n", timeout=20) as r:
            for lg, d in json.load(r).items():
                for k, kk in d.items():
                    tr.setdefault(lg, {}).setdefault(k, {}).update(kk)
    except Exception:
        pass
    for lg in UI_JS_LANGS:
        js = ("window.M365T=" + json.dumps(tr.get(lg, {}), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";"
              "window.M365L=function(de,k,a,b){if(de)return a;var t=window.M365T[k];if(!t)return b;var o={},x;for(x in b)o[x]=b[x];for(x in t)o[x]=t[x];return o};")
        (out / "assets" / f"ui-{lg}.js").write_text(js, "utf-8")
