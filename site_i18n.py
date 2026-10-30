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
