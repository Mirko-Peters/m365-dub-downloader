# AdSense: feste Anzeigenblöcke

Die Seite nutzt **feste Anzeigenblöcke** statt Auto-Anzeigen. Das Skript lädt nur auf Seiten, auf denen wir einen Block gesetzt haben; Googles Auto-Formate (z. B. das Popup „Discover more“ über dem Header) erscheinen dadurch nicht. Das Meta-Tag `google-adsense-account` und `ads.txt` bleiben für die Prüfung.

## Was du in AdSense tun musst
1. **Zwei Anzeigenblöcke anlegen:** Anzeigen → *Nach Anzeigenblock* → *Display-Anzeigen*, Typ **Responsiv**.
   - `m365-mitte` (steht im Text nach dem zweiten Abschnitt)
   - `m365-ende` (steht vor dem Footer)
   Im Codefenster steht je `data-ad-slot="1234567890"`: diese Zahl ist die Block-ID. Den Rest des Codes brauchst du nicht.
2. **IDs eintragen:** in `data/adsense.json` bei `slots` für `mid` und `end` (oder die Zahlen an Claude schicken).
3. **Auto-Anzeigen ausschalten:** Anzeigen → *Nach Website* → `www.m365.fm` → Stift bei *Auto-Anzeigen* → ausschalten. Sonst platziert Google zusätzlich selbst.
4. **EU-Einwilligungsnachricht** (Datenschutz und Mitteilungen) bleibt Pflicht für Besucher aus EWR/UK/CH.

## Wo Blöcke stehen
Nur auf indexierbaren Inhaltsseiten mit mindestens 2500 Zeichen; nie auf Startseite, Community-, Rechts-, Live- und noindex-Seiten, nie in Sidebar oder Header. Leere Blöcke werden ausgeblendet.

## Umschalten
`"auto_ads": true` in `data/adsense.json` lädt das Skript wieder auf allen geeigneten Seiten (Google entscheidet dann über die Platzierung).
