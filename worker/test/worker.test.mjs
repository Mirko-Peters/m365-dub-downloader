// Tests vor dem Deploy (node --test test/): reine Funktionen des Workers und die Schema-Disziplin (Migrationen).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { cleanText, cleanName, esc, isLang, LANGS, b64u, sign, verify } from "../src/util.js";
import { sanitize } from "../src/wiki.js";
import { parseFeed } from "../src/feeds.js";

test("util: Texte bereinigen und escapen", () => {
  assert.equal(cleanText("  a<b>c  ", 3), "a<b");
  assert.equal(cleanName("<x> Name  Y"), "x Name Y");
  assert.equal(esc('<a&"'), "&lt;a&amp;&quot;");
  assert.equal(isLang("de"), true);
  assert.equal(isLang("hi"), false, "entfernte Sprache darf nicht mehr gelten");
  assert.equal(LANGS.length, 14);
  assert.equal(b64u.enc(new Uint8Array([1, 2, 3])), "AQID");
});

test("util: HMAC-Signatur ist pruefbar und faelschungssicher", async () => {
  const s = await sign("geheim", "42");
  assert.equal(await verify("geheim", "42", s), true);
  assert.equal(await verify("geheim", "43", s), false);
  assert.equal(await verify("anders", "42", s), false);
});

test("wiki: sanitize entfernt Skripte, laesst Markup und viz nur mit Option", () => {
  const a = sanitize("Hallo **fett** <script>alert(1)</script> [[power-automate]] {{viz|bars|Titel|a~1;b~2}}", { viz: true });
  assert.equal(a.err, null);
  assert.ok(!a.body.includes("<script"), "kein Script-Tag");
  assert.ok(a.body.includes("[[power-automate]]"), "Wiki-Link bleibt");
  assert.ok(a.body.includes("{{viz|bars|Titel|a~1;b~2}}"), "Infografik bleibt mit viz-Option");
  const b = sanitize("{{viz|bars|Titel|a~1;b~2}}");
  assert.equal(b.body, "", "ohne viz-Option faellt die Infografik weg");
});

test("feeds: parseFeed nimmt nur https-Links und liest Titel, Datum, Beschreibung", () => {
  const rss = `<rss><channel>
    <item><title>T1 &amp; mehr</title><link>https://example.com/1</link><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate><description>&lt;p&gt;Hallo https://example.com/x Welt&lt;/p&gt;</description></item>
    <item><title>Unsicher</title><link>http://example.com/2</link></item>
    <entry><title>Atom</title><link rel="alternate" href="https://example.com/3"/><updated>2024-02-01T00:00:00Z</updated></entry>
  </channel></rss>`;
  const out = parseFeed(rss);
  assert.equal(out.length, 2);
  assert.equal(out[0].title, "T1 & mehr");
  assert.equal(out[0].url, "https://example.com/1");
  assert.equal(out[0].t, Date.parse("Mon, 01 Jan 2024 00:00:00 GMT") / 1000);
  assert.equal(out[0].desc, "Hallo Welt");
  assert.equal(out[1].url, "https://example.com/3");
});

test("schema: Migrationen sind idempotent und enthalten jede zur Laufzeit angelegte Tabelle", () => {
  const dir = new URL("../migrations/", import.meta.url);
  const files = readdirSync(dir).filter((f) => f.endsWith(".sql")).sort();
  assert.ok(files.length >= 1 && files[0] === "0001_baseline.sql");
  const sql = files.map((f) => readFileSync(new URL(f, dir), "utf-8")).join("\n");
  const stmts = sql.replace(/--[^\n]*/g, "").split(";").map((s) => s.trim()).filter(Boolean);
  for (const s of stmts) assert.match(s, /^CREATE (TABLE|INDEX|UNIQUE INDEX) IF NOT EXISTS /i, "nur idempotente Anweisungen: " + s.slice(0, 60));
  const inMig = new Set([...sql.matchAll(/CREATE (?:TABLE|UNIQUE INDEX|INDEX) IF NOT EXISTS (\w+)/gi)].map((m) => m[1]));
  const src = new URL("../src/", import.meta.url);
  for (const f of readdirSync(src).filter((f) => f.endsWith(".js"))) {
    const js = readFileSync(new URL(f, src), "utf-8");
    for (const m of js.matchAll(/CREATE (?:TABLE|UNIQUE INDEX|INDEX) IF NOT EXISTS (\w+)/gi)) assert.ok(inMig.has(m[1]), `${m[1]} (aus ${f}) fehlt in migrations/`);
  }
});
