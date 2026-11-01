"""Textreparatur (Ticket T5): UTF-8, das einmal als CP850 (Windows-Konsole: "ÔÇÖ") oder CP1252 ("â€™", "Ã¼") gelesen wurde, zurueckwandeln.
demojibake(s) versucht erst den exakten Rueckweg (encode cp850/cp1252 -> decode utf-8); bleibt ein Rest (z. B. ein verlorenes Byte als U+FFFD),
greift die Tabelle der haeufigen Zeichen. Texte ohne Verdachtsmuster kommen unveraendert zurueck."""
import re

_SUSPECT = re.compile("ÔÇ|â€|Ã[\u0080-ÿ]|Â[ -¿]")
_MAP = {"ÔÇÖ": "’", "ÔÇÿ": "‘", "ÔÇö": "—", "ÔÇô": "–", "ÔÇæ": "‑", "ÔÇ£": "“", "ÔÇ¥": "”", "ÔÇª": "…", "ÔÇó": "•", "ÔÇ�": "–",
        "â€™": "’", "â€˜": "‘", "â€“": "–", "â€”": "—", "â€œ": "“", "â€\u009d": "”", "â€": "”", "â€¦": "…", "â€¢": "•",
        "Ã¼": "ü", "Ã¶": "ö", "Ã¤": "ä", "ÃŸ": "ß", "Ã„": "Ä", "Ã–": "Ö", "Ãœ": "Ü", "Ã©": "é", "Ã¨": "è", "Ã¡": "á", "Ã ": "à", "Ã³": "ó", "Ã­": "í", "Ãº": "ú", "Ã±": "ñ", "Ã§": "ç", "Ã£": "ã", "Ãµ": "õ", "Ã¢": "â", "Ãª": "ê", "Ã´": "ô", "Ã¯": "ï", "Ã«": "ë", "Â ": " ", "Â·": "·", "Â©": "©", "Â®": "®"}


def demojibake(s):
    if not isinstance(s, str) or not _SUSPECT.search(s):
        return s
    for enc in (("cp850",) if "ÔÇ" in s else ("cp1252",)):   # Signatur entscheidet: "ÔÇ" = CP850 (Windows-Konsole), sonst CP1252
        try:
            t = s.encode(enc).decode("utf-8")
            if not _SUSPECT.search(t) and "�" not in t:
                return t
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    def _chunk(m, enc):   # gemischte Texte (richtiges Unicode neben Mojibake): jede Sequenz einzeln zurueckwandeln
        try:
            t = m.group(0).encode(enc).decode("utf-8")
            return t if "\ufffd" not in t else m.group(0)
        except (UnicodeEncodeError, UnicodeDecodeError):
            return m.group(0)
    s = re.sub("ÔÇ.", lambda m: _chunk(m, "cp850"), s)
    s = re.sub("â€.", lambda m: _chunk(m, "cp1252"), s)
    for k in sorted(_MAP, key=len, reverse=True):
        s = s.replace(k, _MAP[k])
    return s


def fix_tree(o):
    """Alle Strings in verschachtelten dicts/lists reparieren (fuer geladene JSON-Daten)."""
    if isinstance(o, str): return demojibake(o)
    if isinstance(o, list): return [fix_tree(x) for x in o]
    if isinstance(o, dict): return {k: fix_tree(v) for k, v in o.items()}
    return o


def bad(s):
    """True, wenn ein Text Mojibake oder das Ersatzzeichen U+FFFD enthaelt (z. B. zur Pruefung von Uebersetzungen)."""
    return isinstance(s, str) and bool(_SUSPECT.search(s) or "�" in s)
