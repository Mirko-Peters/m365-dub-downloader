"""Show Notes der Spreaker-Folgen auf den Seiten: Spreaker-Text (data/show_notes/<sprache>.json) oder die im Editor bearbeitete Fassung (Worker /api/notes/export).
Kernpunkte, Show Notes und FAQ kommen als getrennte Bloecke; die FAQ erzeugt zusaetzlich FAQPage-Schema."""
import json
import re
import shutil
from pathlib import Path

import show_notes as SN
from site_learn import esc, _fetch_json

ROOT = Path(__file__).parent
NOTES, OVER = {}, {}   # Sprache -> {Folgen-ID: Datensatz} bzw. {Folgen-ID: Bearbeitung}
L = {"en": ("Key points", "Show notes", "FAQ", "Chapters", "Guests"), "de": ("Kernpunkte", "Show Notes", "FAQ", "Kapitel", "Gäste"),
     "es": ("Puntos clave", "Notas del programa", "Preguntas frecuentes", "Capítulos", "Invitados"), "fr": ("Points clés", "Notes de l'épisode", "FAQ", "Chapitres", "Invités"),
     "it": ("Punti chiave", "Note dell'episodio", "FAQ", "Capitoli", "Ospiti"), "pt": ("Pontos-chave", "Notas do episódio", "Perguntas frequentes", "Capítulos", "Convidados"),
     "nl": ("Kernpunten", "Shownotes", "Veelgestelde vragen", "Hoofdstukken", "Gasten")}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def load(api):
    d = ROOT / "data" / "show_notes"
    for f in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            NOTES[f.stem] = json.loads(f.read_text("utf-8")).get("episodes", {})
        except Exception as e:
            print("Show Notes", f.name, e)
    try:
        OVER.update((_fetch_json(f"{api}/api/notes/export") or {}).get("notes", {}))
    except Exception as e:
        print("Show-Notes-Bearbeitungen nicht abrufbar:", str(e)[:100])


def publish(write_dir):
    """Rohdaten fuer den Editor (Worker liest /show-notes/<sprache>.json)."""
    out = Path(write_dir) / "show-notes"
    out.mkdir(parents=True, exist_ok=True)
    for f in (ROOT / "data" / "show_notes").glob("*.json"):
        shutil.copyfile(f, out / f.name)


def get(lang, ep_id=None, title=None):
    """Datensatz einer Folge: Spreaker-Daten, mit Bearbeitung ueberlagert. None, wenn es keine Show Notes gibt."""
    eps = NOTES.get(lang) or {}
    rec = eps.get(str(ep_id)) if ep_id else None
    if not rec and title:
        k = norm(title)
        rec = next((r for r in eps.values() if r.get("key") == k), None)
    if not rec:
        return None
    ov = (OVER.get(lang) or {}).get(rec["id"])
    out = dict(rec)
    out["edited"] = bool(ov)
    if ov:
        out["markup"], out["keypoints"], out["faq"] = ov.get("body", ""), ov.get("keypoints", []), ov.get("faq", [])
    return out


def sections(keypoints, faq, lang):
    """Kernpunkte-Kasten und FAQ-Bereich (mit FAQPage-Schema) aus den getrennten Feldern -> (kp_html, faq_html, jsonld_liste)."""
    t = L.get(lang, L["en"])
    kp = (f'<aside class="kp" aria-label="{esc(t[0])}"><h2>{esc(t[0])}</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in (keypoints or [])) + "</ul></aside>") if keypoints else ""
    faq_html = (f'<section class="faq"><h2>{esc(t[2])}</h2>' + "".join(f"<details><summary>{esc(x['q'])}</summary><p>{esc(x['a'])}</p></details>" for x in faq) + "</section>") if faq else ""
    ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": x["q"], "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in faq]}] if faq else []
    return kp, faq_html, ld


def blocks(rec, lang, edited_only=False):
    """-> (Kernpunkte-HTML, Show-Notes-HTML, FAQ-HTML, JSON-LD-Liste). Leere Strings, wenn nichts da ist."""
    if not rec or (edited_only and not rec.get("edited")):
        return "", "", "", []
    t = L.get(lang, L["en"])
    kp, faq_html, ld = sections(rec.get("keypoints"), rec.get("faq"), lang)
    notes = SN.render_html(rec.get("markup", ""))
    gs = [p for p in rec.get("persons", []) if p.get("role") in ("guest", "") and p.get("name")]
    guests = (f'<p class="mut">{esc(t[4])}: ' + ", ".join((f'<a href="{esc(p["href"])}" rel="nofollow ugc noopener" target="_blank">{esc(p["name"])}</a>' if str(p.get("href", "")).startswith("https://") else esc(p["name"])) for p in gs) + "</p>") if gs else ""
    notes_html = f'<section class="shownotes"><h2>{esc(t[1])}</h2>{notes}{guests}</section>' if (notes or guests) else ""
    return kp, notes_html, faq_html, ld


CSS = '<style>.kp{border:1px solid var(--bd);border-inline-start:4px solid var(--ac,#0a5);border-radius:.4em;padding:.4em 1em;margin:1em 0}.kp h2{margin:.3em 0;font-size:1.1rem}.kp ul{margin:.3em 0;padding-inline-start:1.2em}.shownotes img{max-width:100%;height:auto}</style>'
