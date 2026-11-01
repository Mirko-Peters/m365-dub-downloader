import { rateLimit, sha256hex } from "./util.js";

const TYPES = new Set(["episode", "dub_episode", "entity", "person", "glossary", "blog", "event", "show", "page"]);
const now = () => Math.floor(Date.now() / 1000);
const hash = (value) => {
  let h = 5381;
  for (const c of String(value)) h = ((h << 5) + h + c.charCodeAt(0)) | 0;
  return (h >>> 0).toString(16);
};
const meta = (db, key) => db.prepare("SELECT v FROM meta WHERE k=?").bind(key).first();
const setMeta = (db, key, value) => db.prepare(
  "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v WHERE meta.v<>excluded.v",
).bind(key, String(value)).run();

async function ensureSearchFts(db) {
  const saved = await meta(db, "search_fts_tokenizer");
  if (saved?.v === "unicode61") {
    await db.prepare("CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(title,keywords,summary,tokenize='unicode61')").run();
    return "unicode61";
  }
  if (saved?.v === "trigram") {
    await db.prepare("CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(title,keywords,summary,tokenize='trigram')").run();
    return "trigram";
  }
  try {
    await db.prepare("CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(title,keywords,summary,tokenize='trigram')").run();
    await setMeta(db, "search_fts_tokenizer", "trigram");
    return "trigram";
  } catch {
    await db.prepare("CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(title,keywords,summary,tokenize='unicode61')").run();
    await setMeta(db, "search_fts_tokenizer", "unicode61");
    return "unicode61";
  }
}

async function getJson(env, path) {
  try {
    const response = await fetch(env.SITE + path, { cf: { cacheTtl: 600 } });
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

function normalizeDoc(doc) {
  if (!doc || typeof doc.id !== "string" || !doc.id || typeof doc.title !== "string" || !doc.title ||
      typeof doc.url !== "string" || typeof doc.lang !== "string" || !TYPES.has(doc.type)) return null;
  try {
    if (new URL(doc.url).protocol !== "https:") return null;
  } catch {
    return null;
  }
  const entities = Array.isArray(doc.entities) ? doc.entities.slice(0, 10).map((id) => String(id).trim()).filter(Boolean) : [];
  return {
    id: doc.id,
    url: doc.url,
    lang: doc.lang,
    type: doc.type,
    title: doc.title.slice(0, 500),
    summary: String(doc.summary || "").slice(0, 300),
    keywords: String(doc.keywords || "").slice(0, 500),
    entities: entities.join(","),
    date: /^\d{4}-\d{2}-\d{2}$/.test(doc.date || "") ? doc.date : "",
    image: String(doc.image || "").slice(0, 2000),
  };
}

async function currentRows(db, ids) {
  const rows = new Map();
  for (let i = 0; i < ids.length; i += 500) {
    const part = ids.slice(i, i + 500);
    if (!part.length) continue;
    const found = await db.prepare(`SELECT id,h,gone FROM search_doc WHERE id IN (${part.map(() => "?").join(",")})`).bind(...part).all();
    for (const row of found.results || []) rows.set(row.id, row);
  }
  return rows;
}

export async function importSearchIndex(env) {
  const db = env.DB;
  const manifest = await getJson(env, "/search/manifest.json");
  if (!manifest || !/^\d{4}-\d{2}-\d{2}$/.test(manifest.generated || "") ||
      !Number.isInteger(manifest.parts) || manifest.parts < 1 || manifest.parts > 1000) {
    return { skipped: "Suchmanifest nicht erreichbar oder ungueltig" };
  }
  const tokenizer = await ensureSearchFts(db);
  const cycle = `${manifest.generated}_${manifest.parts}`;
  const oldCycle = (await meta(db, "search_import_cycle"))?.v;
  const previous = oldCycle === cycle ? +(await meta(db, "search_import_part"))?.v || 0 : 0;
  const part = previous % manifest.parts + 1;
  const json = await getJson(env, `/search/part-${part}.json`);
  if (!json || json.part !== part || !Array.isArray(json.docs) || json.docs.length > 2000) {
    return { skipped: `Suchindex-Teil ${part} nicht erreichbar oder ungueltig` };
  }

  const docs = json.docs.map(normalizeDoc).filter(Boolean);
  const existing = await currentRows(db, docs.map((doc) => doc.id));
  const statements = [];
  const timestamp = now();
  let changed = 0;
  for (const doc of docs) {
    const h = hash(JSON.stringify(doc));
    const old = existing.get(doc.id);
    if (old?.h === h && !old.gone) continue;
    statements.push(db.prepare(
      "INSERT INTO search_doc(id,url,lang,type,title,summary,keywords,entities,date,image,h,gone,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,0,?) " +
      "ON CONFLICT(id) DO UPDATE SET url=excluded.url,lang=excluded.lang,type=excluded.type,title=excluded.title,summary=excluded.summary,keywords=excluded.keywords,entities=excluded.entities,date=excluded.date,image=excluded.image,h=excluded.h,gone=0,updated=excluded.updated " +
      "WHERE search_doc.h<>excluded.h OR search_doc.gone=1",
    ).bind(doc.id, doc.url, doc.lang, doc.type, doc.title, doc.summary, doc.keywords, doc.entities, doc.date, doc.image, h, timestamp));
    statements.push(db.prepare("DELETE FROM search_fts WHERE rowid=(SELECT rowid FROM search_doc WHERE id=?)").bind(doc.id));
    statements.push(db.prepare("INSERT INTO search_fts(rowid,title,keywords,summary) SELECT rowid,?,?,? FROM search_doc WHERE id=?").bind(doc.title, doc.keywords, doc.summary, doc.id));
    changed++;
  }
  for (let i = 0; i < statements.length; i += 100) await db.batch(statements.slice(i, i + 100));

  const ids = [...new Set(docs.map((doc) => doc.id))];
  await setMeta(db, `search_ids_part_${part}`, JSON.stringify({ cycle, ids }));
  await setMeta(db, "search_import_cycle", cycle);
  await setMeta(db, "search_import_part", part);

  if (part === manifest.parts && (await meta(db, "search_complete_cycle"))?.v !== cycle) {
    const seen = new Set();
    for (let i = 1; i <= manifest.parts; i++) {
      const source = await meta(db, `search_ids_part_${i}`);
      const snapshot = source ? JSON.parse(source.v) : null;
      if (snapshot?.cycle !== cycle || !Array.isArray(snapshot.ids)) return { part, changed, tokenizer, skipped: "Suchindex-Durchlauf unvollstaendig" };
      for (const id of snapshot.ids) seen.add(id);
    }
    const indexed = (await db.prepare("SELECT id FROM search_doc WHERE gone=0").all()).results || [];
    const missing = indexed.filter((row) => !seen.has(row.id)).map((row) => row.id);
    const gone = missing.map((id) => db.prepare("UPDATE search_doc SET gone=1 WHERE id=? AND gone=0").bind(id));
    for (let i = 0; i < gone.length; i += 100) await db.batch(gone.slice(i, i + 100));
    await setMeta(db, "search_complete_cycle", cycle);
    return { part, changed, gone: missing.length, tokenizer };
  }
  return { part, changed, tokenizer };
}

function trigramQuery(query) {
  const chars = Array.from(query.toLocaleLowerCase());
  const grams = new Set();
  for (let i = 0; i <= chars.length - 3; i++) grams.add(chars.slice(i, i + 3).join(""));
  return [...grams].map((gram) => `"${gram.replaceAll('"', '""')}"`).join(" OR ");
}

function escapeLike(query) {
  return query.replace(/[\\%_]/g, "\\$&");
}

function filtersSql(filters) {
  const clauses = [], values = [];
  if (filters.lang) { clauses.push("d.lang=?"); values.push(filters.lang); }
  if (filters.type) { clauses.push("d.type=?"); values.push(filters.type); }
  if (filters.entity) { clauses.push("instr(','||d.entities||',', ','||?||',')>0"); values.push(filters.entity); }
  if (filters.year) { clauses.push("substr(d.date,1,4)=?"); values.push(filters.year); }
  return { sql: clauses.length ? ` AND ${clauses.join(" AND ")}` : "", values };
}

const FACETS = ["main", "type", "lang", "entity", "year"];
function filtersForFacet(filters, facet) {
  return { ...filters, ...(facet === "main" ? {} : { [facet]: "" }) };
}

function candidateQuery(tokenizer, query, filters) {
  const short = Array.from(query).length < 3;
  const params = [];
  const escaped = escapeLike(query);
  const exactLike = `%${escaped}%`;
  const prefixLike = `${escaped}%`;
  const expression = tokenizer === "trigram"
    ? trigramQuery(query)
    : query.split(/\s+/).filter(Boolean).map((term) => `"${term.replaceAll('"', '""')}"`).join(" OR ");
  const ctes = [];
  if (!short) {
    ctes.push("matched AS MATERIALIZED (SELECT rowid,bm25(search_fts,10,5,1) score FROM search_fts WHERE search_fts MATCH ?)");
    params.push(expression);
  }
  const contexts = [];
  for (const [index, facet] of FACETS.entries()) {
    const contextFilters = filtersForFacet(filters, facet);
    const key = JSON.stringify(contextFilters);
    const existing = contexts.find((context) => context.key === key);
    if (existing) existing.mask |= 1 << index;
    else contexts.push({ key, filters: contextFilters, mask: 1 << index });
  }
  const branches = [];
  for (const context of contexts) {
    const filter = filtersSql(context.filters);
    const source = short
      ? "FROM search_doc d"
      : tokenizer === "unicode61"
        ? "FROM search_doc d LEFT JOIN matched m ON m.rowid=d.rowid"
        : "FROM matched m INNER JOIN search_doc d ON d.rowid=m.rowid";
    const matched = short
      ? "d.title LIKE ? ESCAPE '\\' COLLATE NOCASE"
      : tokenizer === "unicode61"
        ? "(m.rowid IS NOT NULL OR d.title LIKE ? ESCAPE '\\' COLLATE NOCASE)"
        : "1=1";
    const score = short ? "0" : "COALESCE(m.score,0)";
    branches.push(
      `SELECT * FROM (SELECT d.rowid,${score} score,CASE WHEN d.title LIKE ? ESCAPE '\\' COLLATE NOCASE THEN 1 ELSE 0 END exact,${context.mask} scope ` +
      `${source} WHERE d.gone=0 AND ${matched}${filter.sql} ORDER BY exact DESC,score ASC LIMIT 1000)`,
    );
    params.push(exactLike);
    if (short) params.push(prefixLike);
    else if (tokenizer === "unicode61") params.push(exactLike);
    params.push(...filter.values);
  }
  ctes.push(`eligible AS (${branches.join(" UNION ALL ")})`);
  ctes.push(
    "ranked AS (SELECT rowid,MIN(score) score,MAX(exact) exact," +
    FACETS.map((facet, index) => `MAX(scope & ${1 << index}) ${facet}`).join(",") +
    " FROM eligible GROUP BY rowid ORDER BY main DESC,exact DESC,score ASC LIMIT 1000)",
  );
  const sql = `WITH ${ctes.join(",")} SELECT d.id,d.url,d.lang,d.type,d.title,d.summary,d.date,d.image,d.entities,r.score,r.main AS in_main,r.type AS in_type,r.lang AS in_lang,r.entity AS in_entity,r.year AS in_year FROM ranked r INNER JOIN search_doc d ON d.rowid=r.rowid`;
  return { sql, params };
}

function normalizeWord(word) {
  return word.toLocaleLowerCase().replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .normalize("NFD").replace(/\p{M}/gu, "");
}

function trigrams(value) {
  const chars = Array.from(`^${normalizeWord(value)}$`);
  const out = new Set();
  for (let i = 0; i < chars.length - 2; i++) out.add(chars.slice(i, i + 3).join(""));
  return out;
}

function dice(a, b) {
  if (a === b) return 1;
  const left = trigrams(a), right = trigrams(b);
  let common = 0;
  for (const gram of left) if (right.has(gram)) common++;
  return left.size + right.size ? 2 * common / (left.size + right.size) : 0;
}

function titleSimilarity(query, title) {
  const q = normalizeWord(query), titleText = normalizeWord(title);
  const queryWords = q.match(/[\p{L}\p{N}]+/gu) || [q];
  const titleWords = titleText.match(/[\p{L}\p{N}]+/gu) || [titleText];
  const best = queryWords.map((word) => Math.max(...titleWords.map((candidate) => dice(word, candidate))));
  return best.reduce((sum, score) => sum + score, 0) / Math.max(1, best.length);
}

function resultPath(row) {
  let path;
  try { path = new URL(row.url).pathname; } catch { path = row.url; }
  const prefix = `/${row.lang}`;
  if (path === prefix || path === `${prefix}/`) path = "/";
  else if (path.startsWith(`${prefix}/`)) path = path.slice(prefix.length);
  return path.replace(/\/+$/, "") || "/";
}

function rankCandidates(rows, query, pref) {
  const scores = rows.map((row) => Number(row.score) || 0);
  const min = Math.min(...scores, 0), max = Math.max(...scores, 0);
  for (const row of rows) {
    const similarity = titleSimilarity(query, row.title);
    const bm25 = max === min ? 1 : (max - Number(row.score || 0)) / (max - min);
    row.rank = similarity * 100 + bm25 * 10 +
      (similarity >= 0.4 && ["person", "entity"].includes(row.type) ? 16 : 0) +
      (pref && row.lang === pref ? 12 : 0);
  }
  rows.sort((a, b) => b.rank - a.rank || a.title.localeCompare(b.title));
  return rows;
}

function dedupeLanguages(rows, pref) {
  const byPath = new Map();
  for (const row of rows) {
    const path = resultPath(row), previous = byPath.get(path);
    const priority = (item) => item.lang === pref && pref ? 2 : item.lang === "en" ? 1 : 0;
    if (!previous || priority(row) > priority(previous) ||
        (priority(row) === priority(previous) && row.rank > previous.rank)) byPath.set(path, row);
  }
  return [...byPath.values()].sort((a, b) => b.rank - a.rank || a.title.localeCompare(b.title));
}

function countFacet(rows, scope, field) {
  const counts = {};
  for (const row of rows) {
    if (!row[`in_${scope}`]) continue;
    const value = field === "year" ? row.date?.slice(0, 4) : row[field];
    if (value) counts[value] = (counts[value] || 0) + 1;
  }
  return counts;
}

function countEntityFacet(rows) {
  const counts = {};
  for (const row of rows) {
    if (!row.in_entity) continue;
    for (const entity of new Set((row.entities || "").split(",").filter(Boolean))) counts[entity] = (counts[entity] || 0) + 1;
  }
  return Object.fromEntries(Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 15));
}

export async function handleSearch(env, request, url, J) {
  if (request.method !== "GET") return J({ error: "bad_request" }, 405);
  const q = (url.searchParams.get("q") || "").trim().replace(/\s+/g, " ");
  const qLength = Array.from(q).length;
  if (qLength < 2 || qLength > 100) return J({ error: "bad_request" }, 400);
  const rawPage = url.searchParams.get("page"), rawSize = url.searchParams.get("size");
  const page = rawPage === null ? 1 : Number(rawPage), size = rawSize === null ? 20 : Number(rawSize);
  if (!Number.isSafeInteger(page) || page < 1 || page > 100000 || !Number.isInteger(size) || size < 1 || size > 50) return J({ error: "bad_request" }, 400);
  const year = url.searchParams.get("year") || "";
  if (year && !/^\d{4}$/.test(year)) return J({ error: "bad_request" }, 400);
  const filters = {
    lang: url.searchParams.get("lang") || "",
    type: url.searchParams.get("type") || "",
    entity: url.searchParams.get("entity") || "",
    year,
  };
  const pref = url.searchParams.get("pref") || "";
  const day = new Date().toISOString().slice(0, 10);
  const ipHash = await sha256hex(`${request.headers.get("cf-connecting-ip") || ""}|${day}|${env.RL_SALT || ""}`);
  if (!(await rateLimit(env.DB, `search:${ipHash}`, 60, 60))) return J({ error: "rate_limit" }, 429);

  const tokenizer = await ensureSearchFts(env.DB);
  const candidates = candidateQuery(tokenizer, q, filters);
  const rawRows = (await env.DB.prepare(candidates.sql).bind(...candidates.params).all()).results || [];
  const ranked = rankCandidates(rawRows, q, pref);
  const resultRows = filters.lang ? ranked.filter((row) => row.in_main) : dedupeLanguages(ranked.filter((row) => row.in_main), pref);
  const results = resultRows.slice((page - 1) * size, page * size).map(({ url, title, summary, type, lang, date, image }) => ({ url, title, summary, type, lang, date, image }));
  return J({
    q, total: resultRows.length, page,
    results,
    facets: {
      type: countFacet(ranked, "type", "type"),
      lang: countFacet(ranked, "lang", "lang"),
      entity: countEntityFacet(ranked),
      year: countFacet(ranked, "year", "year"),
    },
  }, 200, { "cache-control": "public, max-age=300" });
}
