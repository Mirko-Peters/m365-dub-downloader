# AdSense: Schritte für den Umzug

Die Seite ist vorbereitet (`site_ads.py`, `data/adsense.json`); bis zur Freischaltung erscheint nichts (Meta-Tag, Skript, ads.txt und Anzeigenblöcke sind aus).

1. Domain umziehen: `domain.txt` auf `www.m365.fm` setzen (erzeugt auch `CNAME`), DNS bei der Domain, Worker-CORS/Login-Weiterleitungen und Search Console auf die neue Domain prüfen, alte Domain per 301 weiterleiten.
2. In AdSense (adsense.google.com) die Website `www.m365.fm` hinzufügen und die Prüfung abwarten.
3. In AdSense unter **Datenschutz und Mitteilungen** die EU-Einwilligungsnachricht (zertifizierte CMP) erstellen und veröffentlichen. Pflicht für Besucher aus EWR/UK/CH, die eigene Clarity-Abfrage reicht dafür nicht.
4. `data/adsense.json`: `publisher` (`pub-…`) und unter `slots` die Anzeigenblock-IDs `mid` und `end` eintragen, committen. Danach erscheinen `ads.txt`, Meta-Tag, Skript und die Blöcke automatisch (nur auf Inhaltsseiten mit mindestens 2500 Zeichen, nie auf Community-, Rechts-, Live- und noindex-Seiten).
5. Nach dem Build prüfen: `https://www.m365.fm/ads.txt` erreichbar, im Build-Log steht `AdSense: {... "active": true}`.
