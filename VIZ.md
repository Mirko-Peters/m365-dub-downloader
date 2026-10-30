# Interaktive Infografiken in Beiträgen

Im Editor (Blog, Bibliothek) gibt es den Knopf 📊. Er öffnet einen Baukasten mit Live-Vorschau. Im Text steht danach ein Baustein:

```
{{viz|typ|Titel|Zeile~Wert;Zeile~Wert}}
```

| Typ | Zeilen | Beispiel |
|---|---|---|
| `bars` | Name~Zahl | `{{viz|bars|Nutzung|Q1~12;Q2~28;Q3~55}}` |
| `stats` | Name~Zahl (zählt hoch) | `{{viz|stats|Zahlen|Folgen~1119;Sprachen~19}}` |
| `steps` | Schritt~Beschreibung | `{{viz|steps|Einführung|Plan~Umfang klären;Pilot~20 Nutzer}}` |
| `timeline` | Jahr~Ereignis | `{{viz|timeline|Verlauf|2024~Start;2025~GA}}` |
| `compare` | erste Zeile: Name links~Name rechts, dann Name~Wert links~Wert rechts | `{{viz|compare|Governance|Vorher~Nachher;Vorfälle~42~9}}` |

Regeln: höchstens 3 Grafiken pro Beitrag, 12 Zeilen, nur Text und Zahlen (kein HTML, keine Skripte, keine Links). Die Seite baut daraus `<figure class="viz">` mit einer Liste (barrierefrei, ohne JavaScript sichtbar); `assets/viz.js` macht die interaktive Grafik daraus (GSAP, wenn vorhanden, sonst CSS). Neue Typen: eine Funktion in `assets/viz.js` unter `T`, den Typ in `worker/src/wiki.js` (`COLS`), `site_learn.py` (`_VIZ`) und `assets/editor.js` (`VCOLS`) eintragen.
