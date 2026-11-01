-- T15: Content-Pakete imports/blog/<sprache>/<slug>.md -> blog_posts. Der Seitenbau veroeffentlicht freigegebene Pakete als
-- SITE/blog-content/index.json (site_content_blog.py); Cron importContentBlog (worker/src/contentblog.js) uebernimmt sie.
CREATE TABLE IF NOT EXISTS content_import (
  k TEXT PRIMARY KEY,                          -- <sprache>/<slug>
  post_id INTEGER NOT NULL,                    -- blog_posts.id
  hash TEXT NOT NULL,                          -- Inhaltsstand des Pakets bei der letzten Uebernahme
  imported INTEGER NOT NULL                    -- Zeitpunkt der letzten Uebernahme; spaetere Aenderungen am Beitrag (updated) schuetzen ihn
);
