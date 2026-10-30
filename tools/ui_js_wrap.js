// Einmalig: ersetzt "NAME = de ? {DE} : {EN}" in assets/*.js durch "NAME = M365L(de, "datei.NAME", {DE}, {EN})"
// und schreibt die englischen Texte nach data/ui_js_en.json. Idempotent (bereits umgestellte Stellen werden uebersprungen).
const fs = require("fs"), vm = require("vm");
const files = ["events", "profile", "entity", "messages", "wiki", "pfpub"], en = {};
function lit(s, i) {   // Objektliteral ab s[i] == "{" bis zur passenden Klammer
  let d = 0, q = null;
  for (let j = i; j < s.length; j++) {
    const c = s[j];
    if (q) { if (c === "\\") j++; else if (c === q) q = null; continue; }
    if (c === '"' || c === "'" || c === "`") { q = c; continue; }
    if (c === "{") d++; else if (c === "}") { d--; if (d === 0) return j + 1; }
  }
  return -1;
}
for (const f of files) {
  const p = `assets/${f}.js`; let s = fs.readFileSync(p, "utf8"), out = "", pos = 0, n = 0;
  const re = /(\w+) = de \? \{/g; let m;
  while ((m = re.exec(s))) {
    const a = m.index + m[0].length - 1, e1 = lit(s, a); if (e1 < 0) continue;
    const mm = /^\s*:\s*\{/.exec(s.slice(e1)); if (!mm) continue;
    const b = e1 + mm[0].length - 1, e2 = lit(s, b); if (e2 < 0) continue;
    let obj; try { obj = vm.runInNewContext("(" + s.slice(b, e2) + ")"); } catch (e) { console.log("uebersprungen", f, m[1], e.message); continue; }
    const key = `${f}.${m[1]}`; en[key] = obj;
    out += s.slice(pos, m.index) + `${m[1]} = M365L(de, "${key}", ${s.slice(a, e1)}, ${s.slice(b, e2)})`; pos = e2; re.lastIndex = e2; n++;
  }
  out += s.slice(pos);
  if (n && !/var M365L = /.test(out)) out = out.replace("(function () {", "(function () {\n  var M365L = window.M365L || function (de, k, a, b) { return de ? a : b; };");
  fs.writeFileSync(p, out); console.log(f, n, "Woerterbuecher");
}
const old = fs.existsSync("data/ui_js_en.json") ? JSON.parse(fs.readFileSync("data/ui_js_en.json", "utf8")) : {};
fs.writeFileSync("data/ui_js_en.json", JSON.stringify({ ...old, ...en }, null, 1));
console.log("Schluessel:", Object.keys({ ...old, ...en }).length, "Texte:", Object.values({ ...old, ...en }).reduce((a, o) => a + Object.keys(o).length, 0));
