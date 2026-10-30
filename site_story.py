"""Je Blogbeitrag waehlt ein kleines Skript ein kreatives Bewegungsrezept (GSAP, assets/story.js) anhand des Inhalts.
Gilt fuer neue und bearbeitete Beitraege automatisch, weil die Seite bei jedem Bau daraus entsteht. Ohne Zufall: gleicher Beitrag, gleiches Rezept."""
import hashlib
import re

RECIPES = ("ink", "focus", "marker", "parallax", "chapters", "spark")


def recipe_for(slug, html):
    h = html or ""
    words = len(re.sub(r"<[^>]+>", " ", h).split())
    n_img = len(re.findall(r"<img\b", h)); n_h2 = len(re.findall(r"<h2\b", h)); n_em = len(re.findall(r"<(?:strong|mark|b)\b", h))
    if n_img >= 2: return "parallax"        # Bilder driften beim Lesen
    if n_h2 >= 5: return "chapters"         # Kapitelleiste mit Fortschritt je Abschnitt
    if n_em >= 6: return "marker"           # Hervorhebungen werden beim Lesen "markiert"
    if words >= 1800: return "focus"        # langer Text: Leselicht auf dem aktuellen Absatz
    if re.search(r"<(?:table|pre|code)\b", h): return "ink"   # Technik-Inhalt: Ueberschriften wischen ein
    return RECIPES[int(hashlib.md5((slug or "").encode()).hexdigest()[:4], 16) % len(RECIPES)]
