// Getrennte Textbausteine neben dem Haupttext: Kernpunkte (Key points) und FAQ. Eigene Felder statt Fliesstext, damit die Seiten sie als
// Zusammenfassung-Box bzw. FAQ-Bereich mit FAQPage-Schema ausgeben und der SEO-Check sie einzeln bewertet.
const clean = (s, n) => String(s || "").replace(/[<>{}]/g, "").replace(/https?:\/\/\S+/gi, "").replace(/www\.\S+/gi, "").replace(/\s+/g, " ").trim().slice(0, n);
export const MAX_KEYPOINTS = 8, MAX_FAQ = 10;

// Text -> Liste: eine Zeile je Punkt, Aufzaehlungszeichen werden entfernt
export function parseKeypointsText(t) { return String(t || "").split(/\r?\n/).map((l) => l.replace(/^\s*(?:[-*•]|\d+[.)])\s*/, "").trim()).filter(Boolean); }
// Text -> Liste: Bloecke durch Leerzeile getrennt, erste Zeile = Frage, Rest = Antwort ("Q:"/"A:" oder "F:"/"A:" Praefixe erlaubt)
export function parseFaqText(t) {
  const out = [];
  for (const blk of String(t || "").replace(/\r/g, "").split(/\n\s*\n/)) {
    const ls = blk.split("\n").map((l) => l.trim()).filter(Boolean); if (!ls.length) continue;
    const q = ls[0].replace(/^(?:q|f|frage|question)\s*[:.)-]\s*/i, ""), a = ls.slice(1).join(" ").replace(/^(?:a|antwort|answer)\s*[:.)-]\s*/i, "");
    out.push({ q, a });
  }
  return out;
}
// Eingabe pruefen: Array oder Text. Rueckgabe { list } oder { err }
export function cleanKeypoints(raw) {
  const src = Array.isArray(raw) ? raw : parseKeypointsText(raw), list = [];
  for (const x of src) { const p = clean(typeof x === "string" ? x : x?.text, 200); if (!p) continue; if (p.length < 10) return { err: "bad_keypoints" }; list.push(p); }
  return list.length > MAX_KEYPOINTS ? { err: "too_many_keypoints" } : { list };
}
export function cleanFaq(raw) {
  const src = Array.isArray(raw) ? raw : parseFaqText(raw), list = [];
  for (const x of src) {
    if (!x || (!x.q && !x.a)) continue;
    const q = clean(x.q, 200), a = clean(x.a, 600);
    if (q.length < 10 || a.length < 20) return { err: "bad_faq" };
    list.push({ q, a });
  }
  return list.length > MAX_FAQ ? { err: "too_many_faq" } : { list };
}
export const jsonList = (s) => { try { const v = JSON.parse(s || "[]"); return Array.isArray(v) ? v : []; } catch { return []; } };

// Spalten nachziehen (D1 kennt kein IF NOT EXISTS fuer ADD COLUMN): einmal je Isolate
let ok = false;
export async function ensureSectionCols(db) {
  if (ok) return;
  for (const t of ["blog_posts", "feed_items"]) {
    try { await db.prepare(`SELECT keypoints,faq FROM ${t} LIMIT 1`).first(); } catch {
      for (const c of ["keypoints TEXT NOT NULL DEFAULT '[]'", "faq TEXT NOT NULL DEFAULT '[]'"]) { try { await db.prepare(`ALTER TABLE ${t} ADD COLUMN ${c}`).run(); } catch { /* Tabelle fehlt oder Spalte vorhanden */ } }
    }
  }
  ok = true;
}
