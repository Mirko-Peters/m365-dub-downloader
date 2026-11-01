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

function filtersSql(filters) {
  const clauses = [], values = [];
  if (filters.lang) { clauses.push("d.lang=?"); values.push(filters.lang); }
  if (filters.type) { clauses.push("d.type=?"); values.push(filters.type); }
  if (filters.entity) { clauses.push("instr(','||d.entities||',', ','||?||',')>0"); values.push(filters.entity); }
  if (filters.year) { clauses.push("substr(d.date,1,4)=?"); values.push(filters.year); }
  return { sql: clauses.length ? ` AND ${clauses.join(" AND ")}` : "", values };
}

function searchSql(tokenizer, query, filters, pref) {
  const short = Array.from(query).length < 3;
  const params = [];
  let cte = "", matchSql, join = "";
  if (short) {
    matchSql = "d.title LIKE ? ESCAPE '\\' COLLATE NOCASE";
    params.push(`${query.replace(/[\\%_]/g, "\\$&")}%`);
  } else {
    const expression = tokenizer === "trigram"
      ? trigramQuery(query)
      : query.split(/\s+/).filter(Boolean).map((term) => `"${term.replaceAll('"', '""')}"`).join(" OR ");
    cte = "WITH matched AS (SELECT rowid,bm25(search_fts,10,5,1) score FROM search_fts WHERE search_fts MATCH ?) ";
    params.push(expression);
    join = "LEFT JOIN matched m ON m.rowid=d.rowid";
    if (tokenizer === "unicode61") {
      matchSql = "(m.rowid IS NOT NULL OR d.title LIKE ? ESCAPE '\\' COLLATE NOCASE)";
      params.push(`%${query.replace(/[\\%_]/g, "\\$&")}%`);
    } else matchSql = "m.rowid IS NOT NULL";
  }
  const filter = filtersSql(filters);
  params.push(...filter.values);
  let order;
  if (!short) {
    order = "COALESCE(m.score,1)-CASE WHEN d.lang=? THEN 0.000001 ELSE 0 END";
  } else {
    order = "CASE WHEN d.lang=? THEN 0 ELSE 1 END,d.title COLLATE NOCASE";
  }
  return {
    cte,
    from: `FROM search_doc d ${join} WHERE d.gone=0 AND ${matchSql}${filter.sql}`,
    params,
    orderParams: [pref],
    order,
  };
}

async function facetCounts(db, tokenizer, query, filters, pref, expression) {
  const sql = searchSql(tokenizer, query, filters, pref);
  const rows = (await db.prepare(`${sql.cte}SELECT ${expression} value,COUNT(*) n ${sql.from} GROUP BY value`).bind(...sql.params).all()).results || [];
  return Object.fromEntries(rows.filter((row) => row.value).map((row) => [row.value, row.n]));
}

async function entityFacetCounts(db, tokenizer, query, filters, pref) {
  const sql = searchSql(tokenizer, query, filters, pref);
  const cte = `WITH RECURSIVE ${sql.cte ? `${sql.cte.slice(5)},` : ""}filtered(id,rest) AS (SELECT d.rowid,d.entities||',' ${sql.from}),` +
    "split(id,rest,entity) AS (SELECT id,rest,'' FROM filtered UNION ALL SELECT id,substr(rest,instr(rest,',')+1),substr(rest,1,instr(rest,',')-1) FROM split WHERE rest<>'') ";
  const rows = (await db.prepare(`${cte}SELECT entity value,COUNT(DISTINCT id) n FROM split WHERE entity<>'' GROUP BY entity ORDER BY n DESC,value LIMIT 15`).bind(...sql.params).all()).results || [];
  return Object.fromEntries(rows.map((row) => [row.value, row.n]));
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
  const ipHash = await sha256hex(request.headers.get("cf-connecting-ip") || "");
  if (!(await rateLimit(env.DB, `search:${ipHash}`, 60, 60))) return J({ error: "rate_limit" }, 429);

  const tokenizer = await ensureSearchFts(env.DB);
  const selected = searchSql(tokenizer, q, filters, pref);
  const count = await env.DB.prepare(`${selected.cte}SELECT COUNT(*) n ${selected.from}`).bind(...selected.params).first();
  const resultsQuery = searchSql(tokenizer, q, filters, pref);
  const rows = (await env.DB.prepare(
    `${resultsQuery.cte}SELECT d.url,d.title,d.summary,d.type,d.lang,d.date,d.image ${resultsQuery.from} ORDER BY ${resultsQuery.order} LIMIT ? OFFSET ?`,
  ).bind(...resultsQuery.params, ...resultsQuery.orderParams, size, (page - 1) * size).all()).results || [];
  const [typeCounts, langCounts, entityFacet, yearCounts] = await Promise.all([
    facetCounts(env.DB, tokenizer, q, { ...filters, type: "" }, pref, "d.type"),
    facetCounts(env.DB, tokenizer, q, { ...filters, lang: "" }, pref, "d.lang"),
    entityFacetCounts(env.DB, tokenizer, q, { ...filters, entity: "" }, pref),
    facetCounts(env.DB, tokenizer, q, { ...filters, year: "" }, pref, "substr(d.date,1,4)"),
  ]);
  return J({
    q, total: count?.n || 0, page,
    results: rows,
    facets: { type: typeCounts, lang: langCounts, entity: entityFacet, year: yearCounts },
  }, 200, { "cache-control": "public, max-age=300" });
}
