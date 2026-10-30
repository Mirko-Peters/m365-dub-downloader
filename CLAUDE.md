# Projektregeln

## Bilder
- Alle Bilder des Projekts werden in Zukunft im eigenen Cloudflare-R2-Bucket `m365-fm` gespeichert und über `https://img.m365.fm/…` ausgeliefert, nicht bei fremden Hosts (Podpage, Amazon, S3 usw.).
- Fremde Bilder kopiert der manuelle Workflow `r2-images.yml` (`tools/r2_upload.py`) in den Bucket und trägt sie in `data/r2_map.json` ein. `site_r2.py` schreibt die URLs beim Seitenbau um.
- Neue Bilder (Blog, Gäste, Entitäten, Community) gehören ebenfalls dorthin. Die Zugangsdaten liegen nur als GitHub-Secrets (`R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`), nie im Code oder Chat.
- Ausnahme: Folgenbilder von Spreaker (CloudFront) bleiben vorerst dort.
