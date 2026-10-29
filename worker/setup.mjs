// Einrichtung/Deploy des Community-Workers (laeuft im GitHub-Workflow). Erzeugt fehlende Schluessel selbst, schreibt nie Secrets ins Log.
import { execFileSync, spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { webcrypto as crypto } from "node:crypto";

const run = (args, input) => { const r = spawnSync("npx", ["wrangler", ...args], { input, encoding: "utf8" }); return r; };
const fail = (m) => { console.error("::error::" + String(m).replace(/\r?\n/g, " | ").slice(0, 900)); process.exit(1); };
const b64u = (b) => Buffer.from(b).toString("base64url");


// 0) Vorab-Prüfung: Zone m365.fm sichtbar? workers.dev-Subdomain vorhanden (sonst anlegen)?
{
  const H = { Authorization: "Bearer " + process.env.CLOUDFLARE_API_TOKEN, "content-type": "application/json" }, A = process.env.CLOUDFLARE_ACCOUNT_ID;
  const cf = async (p, o) => { try { const r = await fetch("https://api.cloudflare.com/client/v4" + p, { headers: H, ...o }); return await r.json(); } catch (e) { return { success: false, errors: [{ message: String(e) }] }; } };
  const z = await cf("/zones?name=m365.fm");
  console.log("Zone m365.fm:", z.success && z.result?.length ? "gefunden (" + z.result[0].id + ")" : "NICHT sichtbar " + JSON.stringify(z.errors || []));
  if (!(z.success && z.result?.length)) fail("Zone m365.fm nicht sichtbar: dem Token fehlt 'Zone > Zone > Read' fuer m365.fm (oder die Domain liegt in einem anderen Konto).");
  const za = z.result[0].account?.id || "";
  console.log("Konto der Zone:", za.slice(0, 6) + "…", "| gesetzte CLOUDFLARE_ACCOUNT_ID:", A.slice(0, 6) + "…");
  if (za && za !== A) fail(`Die Zone m365.fm gehoert zum Cloudflare-Konto ${za.slice(0, 6)}…, die Secret CLOUDFLARE_ACCOUNT_ID beginnt aber mit ${A.slice(0, 6)}… – bitte die Konto-ID des Kontos eintragen, in dem m365.fm liegt (steht in der Adresszeile: dash.cloudflare.com/<ID>/m365.fm).`);
  const sd = await cf(`/accounts/${A}/workers/subdomain`);
  if (!(sd.success && sd.result?.subdomain)) {
    const put = await cf(`/accounts/${A}/workers/subdomain`, { method: "PUT", body: JSON.stringify({ subdomain: "m365fm-" + A.slice(0, 6) }) });
    console.log("workers.dev-Subdomain anlegen:", put.success ? "ok" : JSON.stringify(put.errors || []));
  } else console.log("workers.dev-Subdomain:", sd.result.subdomain);
}

// 1) D1-Datenbank finden oder anlegen, ID in wrangler.toml eintragen
let list = run(["d1", "list", "--json"]);
let dbs = []; try { dbs = JSON.parse(list.stdout); } catch { fail("d1 list: " + (list.stderr || list.stdout)); }
let db = dbs.find((d) => d.name === "m365-dub");
if (!db) { const c = run(["d1", "create", "m365-dub"]); console.log(c.stdout.split("\n").slice(0, 3).join("\n")); dbs = JSON.parse(run(["d1", "list", "--json"]).stdout); db = dbs.find((d) => d.name === "m365-dub"); }
if (!db) { fail("D1 konnte nicht angelegt werden"); }
const id = db.uuid || db.id;
let toml = readFileSync("wrangler.toml", "utf8").replace(/database_id = "[^"]*"/, `database_id = "${id}"`);
writeFileSync("wrangler.toml", toml);
console.log("D1:", db.name);

// 2) Schema anwenden (idempotent)
const sch = run(["d1", "execute", "m365-dub", "--remote", "--file=schema.sql"]);
if (sch.status !== 0) fail("Schema: " + sch.stderr);
console.log("Schema ok");

// 3) Erstmal deployen (damit Secrets einen Worker haben), dann Secrets
const dep = run(["deploy"]);
console.log(dep.stdout.split("\n").slice(-6).join("\n")); if (dep.status !== 0) fail("Deploy: " + dep.stderr);

let have = [];
try { have = JSON.parse(run(["secret", "list", "--format", "json"]).stdout).map((s) => s.name); } catch {}
const put = (k, v) => { const r = run(["secret", "put", k], v); console.log(k, r.status === 0 ? "gesetzt" : "FEHLER " + r.stderr.slice(0, 200)); };

const gen = {
  SESSION_SECRET: () => b64u(crypto.getRandomValues(new Uint8Array(32))),
  CRON_KEY: () => b64u(crypto.getRandomValues(new Uint8Array(24))),
};
for (const [k, f] of Object.entries(gen)) if (!have.includes(k)) put(k, f());

if (!have.includes("VAPID_PRIVATE_JWK") || !have.includes("VAPID_PUBLIC")) {
  const kp = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign"]);
  const jwk = await crypto.subtle.exportKey("jwk", kp.privateKey);
  const pub = b64u(await crypto.subtle.exportKey("raw", kp.publicKey));
  put("VAPID_PRIVATE_JWK", JSON.stringify(jwk)); put("VAPID_PUBLIC", pub);
}
// Vom Betreiber gelieferte Secrets (GitHub-Secrets -> Umgebung); nur setzen, wenn vorhanden
for (const k of ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "MS_CLIENT_ID", "MS_CLIENT_SECRET", "RESEND_API_KEY", "ADMIN_SUBS"]) if (process.env[k]) put(k, process.env[k]);
console.log("Fertig. Worker: https://api-dub.m365.fm");
// Nachpruefung: Custom Domain und DNS-Eintrag
{
  const H = { Authorization: "Bearer " + process.env.CLOUDFLARE_API_TOKEN }, A = process.env.CLOUDFLARE_ACCOUNT_ID;
  const g = async (p) => { try { return await (await fetch("https://api.cloudflare.com/client/v4" + p, { headers: H })).json(); } catch (e) { return { success: false, errors: [String(e)] }; } };
  const d = await g(`/accounts/${A}/workers/domains`);
  console.log("::notice::Worker-Domains:", JSON.stringify((d.result || []).map((x) => x.hostname + "->" + x.service)), d.success ? "" : JSON.stringify(d.errors));
  const z = await g("/zones?name=m365.fm"); const zid = z.result?.[0]?.id;
  const r = await g(`/zones/${zid}/dns_records?per_page=100`);
  console.log("::notice::DNS (dub/api):", JSON.stringify((r.result || []).filter((x) => /dub|api/.test(x.name)).map((x) => `${x.type} ${x.name} -> ${String(x.content).slice(0, 40)}`)), r.success ? "" : JSON.stringify(r.errors));
  try { const t = await fetch("https://api-dub.m365.fm/api/health"); console.log("::notice::Test api-dub.m365.fm:", t.status, (await t.text()).slice(0, 80)); } catch (e) { console.log("Test api-dub.m365.fm: nicht erreichbar", String(e.cause?.code || e)); }
}
