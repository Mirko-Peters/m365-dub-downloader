CREATE TABLE IF NOT EXISTS search_doc (
  id TEXT PRIMARY KEY,
  url TEXT NOT NULL,
  lang TEXT NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  keywords TEXT NOT NULL,
  entities TEXT NOT NULL,
  date TEXT NOT NULL,
  image TEXT NOT NULL,
  h TEXT NOT NULL,
  gone INTEGER NOT NULL DEFAULT 0,
  updated INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_search_doc_facets ON search_doc(gone,lang,type,date);
