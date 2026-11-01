#!/usr/bin/env python3
"""T25: Freigegebene Shownotes per Spreaker-API in die Episodenbeschreibungen schreiben.

Quelle: shownotes/spreaker/<episode_id>.html (vom Shownotes-Generator). Freigabe-Gate: Datei shownotes/APPROVED (legt die QA an) als Hauptschalter,
geschrieben werden nur Folgen, die die QA in shownotes/QA.txt mit ok oder fixed fuehrt;
ohne sie nur Dry-Run (Diff nach shownotes/DRYRUN.md). shownotes/PAUSED haelt alles an. Je Lauf hoechstens --limit Folgen,
meistgehoerte zuerst (Spreaker-Statistik, Zwischenspeicher shownotes/plays.json). Protokoll je Folge in shownotes/APPLIED.txt
(Zeit, Episode, Status, Hash der HTML-Datei, Abrufe, Titel, Hinweis). Es wird nur die Beschreibung geschrieben; Titel, Status,
Audio und GUID bleiben unberuehrt. Vor dem Schreiben: <= 4.000 Zeichen, nur <p><strong><ul><li><a>, Links nur auf https://www.m365.fm.
Zugang wie sync_spreaker.py: Secret SPREAKER_TOKEN, sonst die OAuth-Verbindung (spreaker_auth.py); der Token wird nie ausgegeben.
Aufrufe: --check (nur Dateien pruefen, ohne API), --dry-run, --limit N, --dry-limit N, --ids 1,2,3."""
import argparse, difflib, hashlib, html, json, os, re, sys, time
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SN = Path(os.environ.get("SHOWNOTES_DIR") or (ROOT / "shownotes"))
SRC, APPLIED, DRY, PLAYS = SN / "spreaker", SN / "APPLIED.txt", SN / "DRYRUN.md", SN / "plays.json"
API = "https://api.spreaker.com/v2"
ALLOWED = {"p", "strong", "ul", "li", "a"}
MAXLEN = 4000
LINK_OK = re.compile(r"^https://www\.m365\.fm(/|$)")
MAX_TRIES = 3          # Fehlversuche je Datei-Fassung, danach wird die Folge bis zur naechsten Aenderung uebersprungen


# ---------------------------------------------------------------- Pruefung der HTML-Dateien (ohne API)
class _Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.errors, self.stack, self.links, self.text = [], [], 0, []
    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED:
            self.errors.append(f"Tag <{tag}> nicht erlaubt"); return
        for k, v in attrs:
            if tag == "a" and k == "href":
                if not LINK_OK.match(v or ""):
                    self.errors.append(f"Link nicht auf https://www.m365.fm: {(v or '')[:80]}")
                self.links += 1
            elif tag == "a" and k in ("rel", "target", "title"):
                pass
            else:
                self.errors.append(f"Attribut {k} an <{tag}> nicht erlaubt")
        self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag not in ALLOWED:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"Verschachtelung: </{tag}> passt nicht zu <{self.stack[-1] if self.stack else '-'}>")
        else:
            self.stack.pop()
    def handle_startendtag(self, tag, attrs):
        self.errors.append(f"Tag <{tag}/> nicht erlaubt")
    def handle_comment(self, data): self.errors.append("HTML-Kommentar nicht erlaubt")
    def handle_decl(self, data): self.errors.append("Deklaration nicht erlaubt")
    def handle_pi(self, data): self.errors.append("Verarbeitungsanweisung nicht erlaubt")
    def handle_data(self, data): self.text.append(data)


MIN_LINKS = 6   # Linkvorgabe fuer Spreaker-Shownotes (Mirko, 1.11.)


def check_html(raw):
    """Liste der Fehler (leer = in Ordnung)."""
    s = raw.strip()
    errs = []
    if not s:
        return ["leer"]
    if len(s) > MAXLEN:
        errs.append(f"{len(s)} Zeichen (> {MAXLEN})")
    if re.search(r"<\s*(script|style|iframe|img|object|embed)", s, flags=re.I):
        errs.append("Skript/Stil/Einbettung nicht erlaubt")
    p = _Check()
    try:
        p.feed(s); p.close()
    except Exception as e:   # pragma: no cover - HTMLParser wirft praktisch nie
        errs.append(f"nicht lesbar: {e}")
    if p.stack:
        errs.append("nicht geschlossen: " + ", ".join(f"<{t}>" for t in p.stack))
    if not "".join(p.text).strip():
        errs.append("kein Text")
    if re.search(r"utm_campaign=(None|null|undefined)?(&|&amp;|\"|$)", s):   # Generator ohne Folgen-Slug (QA, 1.11.)
        errs.append("utm_campaign leer oder None (Folgen-Slug fehlt)")
    _rf = ROOT / "data" / "slug_renames.json"   # T12: kein Link auf die alte Adresse einer umbenannten Folge
    for _old in ((json.loads(_rf.read_text("utf-8")).get("episodes") or {}) if _rf.exists() else {}):
        if re.search(r'href="[^"]*/show/episodes/' + re.escape(_old) + r'/', s): errs.append(f"Link auf alten Folgen-Slug {_old} (data/slug_renames.json)")
    n_links = len(re.findall(r"<a\s[^>]*href=", s, flags=re.I))
    if n_links < MIN_LINKS:   # Mirko, 1.11.: mindestens 6 Links (vorher 8-10, kurz 4); weniger -> nicht schreiben, Generator ergaenzt
        errs.append(f"{n_links} Links (mindestens {MIN_LINKS})")
    return errs + p.errors


def to_text(h):
    """HTML -> Zeilen (fuer Diff und Vergleich)."""
    t = re.sub(r"(?i)</(p|li|ul)>", "\n", h or "")
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    return [html.unescape(x).strip() for x in t.split("\n") if html.unescape(x).strip()]


def norm(h):
    return re.sub(r"\s+", " ", (h or "")).strip()


def text_key(h):
    """Textinhalt ohne Tags und Leerraum. Spreaker gibt in 'description' nur Text zurueck (Tags entfernt, Listenpunkte ohne
    Trenner), das gesendete HTML ist laenger - verglichen wird deshalb der Inhalt, nicht die Zeichenzahl."""
    return re.sub(r"\s+", "", html.unescape(re.sub(r"<[^>]+>", "", h or "")))


def same_on_spreaker(ep, raw):
    """True, wenn Spreaker die Fassung raw gespeichert hat: HTML-Feld (falls geliefert) gleich, sonst Textinhalt gleich."""
    h = ep.get("description_html")
    if h:
        return norm(h) == norm(raw) or text_key(h) == text_key(raw)
    return text_key(ep.get("description") or "") == text_key(raw)


def sha(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------- Protokoll
def read_applied():
    """episode_id -> Liste der Protokollzeilen (dict)."""
    out = {}
    if not APPLIED.exists():
        return out
    for line in APPLIED.read_text("utf-8").splitlines():
        f = line.split("\t")
        if len(f) < 4 or not f[1].isdigit():
            continue
        out.setdefault(int(f[1]), []).append({"at": f[0], "status": f[2], "hash": f[3], "msg": f[-1]})
    return out


def log_applied(eid, status, h, plays, title, msg=""):
    APPLIED.parent.mkdir(parents=True, exist_ok=True)
    with APPLIED.open("a", encoding="utf-8") as f:
        f.write("\t".join([now(), str(eid), status, h, str(plays), (title or "")[:60].replace("\t", " "), msg.replace("\t", " ").replace("\n", " ")[:200]]) + "\n")
    print(f"{eid}\t{status}\t{msg[:120]}", flush=True)


# ---------------------------------------------------------------- Spreaker-Zugang (Token wird nie ausgegeben)
class Spreaker:
    def __init__(self):
        import requests
        self.s = requests.Session()
        self.tok = ""

    def _me(self):
        r = self.s.get(API + "/me", timeout=30)
        return r.status_code

    def login(self):
        tok = os.environ.get("SPREAKER_TOKEN", "").strip()
        if tok:
            self.s.headers["Authorization"] = f"Bearer {tok}"
            if self._me() == 200:
                self.tok = tok; print("Zugang: SPREAKER_TOKEN"); return True
            print("SPREAKER_TOKEN ungueltig - versuche OAuth-Verbindung")
        if os.environ.get("SPREAKER_CLIENT_SECRET"):
            sys.path.insert(0, str(ROOT))
            import spreaker_auth
            d = spreaker_auth.load()
            if d:
                tok = d["access_token"]
                self.s.headers["Authorization"] = f"Bearer {tok}"
                if self._me() == 401:
                    tok = spreaker_auth.refresh(); self.s.headers["Authorization"] = f"Bearer {tok}"
                if self._me() == 200:
                    self.tok = tok; print("Zugang: OAuth-Verbindung"); return True
            else:
                print("Keine lesbare data/spreaker_auth.enc")
        print("::error::Kein Spreaker-Zugang (SPREAKER_TOKEN bzw. 'Spreaker verbinden')")
        return False

    def req(self, method, path, **kw):
        url = path if path.startswith("http") else API + path
        for a in range(5):
            r = self.s.request(method, url, timeout=kw.pop("timeout", 60), **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(int(r.headers.get("Retry-After", 0)) or 8 * (a + 1)); continue
            if r.status_code == 401:
                raise PermissionError("Spreaker 401: Token ungueltig/abgelaufen")
            if r.status_code >= 400:
                raise RuntimeError(f"Spreaker {method} {path}: {r.status_code} {r.text[:200]}")
            return r.json().get("response", {})
        raise RuntimeError(f"Spreaker {method} {path}: zu viele Fehlversuche")

    def paged(self, path):
        items, url = [], path
        while url:
            resp = self.req("GET", url); items += resp.get("items", []); url = resp.get("next_url")
        return items

    def episodes(self):
        """Alle Folgen der eigenen Shows: episode_id -> {show_id, title, plays}."""
        uid = self.req("GET", "/me")["user"]["user_id"]
        out = {}
        for sh in self.paged(f"/users/{uid}/shows?limit=100"):
            sid = sh["show_id"]
            for e in self.paged(f"/shows/{sid}/episodes?limit=100"):
                out[int(e["episode_id"])] = {"show_id": sid, "title": e.get("title", ""), "plays": int(e.get("plays_count") or e.get("downloads_count") or 0)}
        return out

    def plays(self, show_ids, days=730, step=90):
        """Abrufe je Folge der letzten zwei Jahre (Statistik-API in 90-Tage-Fenstern summiert; ein Zeitraum ab 2015 lehnt
        Spreaker mit 400 ab). Fenster, die scheitern, werden uebersprungen; leer, wenn die Statistik gar nicht lesbar ist."""
        out, fails = {}, 0
        for sid in show_ids:
            to = date.today()
            while (date.today() - to).days < days:
                frm = to - timedelta(days=step - 1)
                try:
                    for it in self.paged(f"/shows/{sid}/episodes/statistics/plays/totals?from={frm}&to={to}&limit=20"):
                        eid = it.get("episode_id") or (it.get("episode") or {}).get("episode_id")
                        nums = {k: v for k, v in it.items() if isinstance(v, (int, float)) and not isinstance(v, bool) and k not in ("episode_id", "show_id")}
                        pl = sum(v for k, v in nums.items() if "play" in k.lower()) or sum(v for k, v in nums.items() if "download" in k.lower())
                        if eid:
                            out[int(eid)] = out.get(int(eid), 0) + int(pl)
                except Exception as e:
                    fails += 1
                    if fails <= 3: print(f"Statistik Show {sid} {frm}..{to} nicht lesbar: {str(e)[:120]}")
                to = frm - timedelta(days=1)
        if not out:   # Rueckfall: Wochen-Top der Seite (sync_spreaker.py, gleicher Endpunkt mit 7 Tagen)
            try:
                t = json.loads((ROOT / "data" / "top.json").read_text("utf-8"))
                for l in (t.get("langs") or {}).values():
                    for r in l: out[int(r["episode_id"])] = int(r.get("score") or 0)
            except (OSError, ValueError, KeyError):
                pass
        return out


# ---------------------------------------------------------------- Ablauf
def qa_ok(path=None):
    """episode_ids (str) mit QA-Status ok oder fixed in shownotes/QA.txt (Format episode_id;status;Datum, letzter Eintrag zaehlt)."""
    st, f = {}, path or (SN / "QA.txt")
    if f.exists():
        for line in f.read_text("utf-8").splitlines():
            x = [y.strip() for y in line.split(";")]
            if len(x) >= 2 and x[0].isdigit(): st[x[0]] = x[1].lower()
    return {k for k, v in st.items() if v in ("ok", "fixed")}


def _git(*args):
    import subprocess
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=300).stdout
    except Exception:
        return ""


def qa_times(path=None):
    """episode_id -> Commit-Zeit (Unix) seines letzten Eintrags in shownotes/QA.txt (git blame; letzter Eintrag zaehlt)."""
    f = path or (SN / "QA.txt"); out, cur = {}, None
    if not f.exists():
        return out
    for line in _git("blame", "--line-porcelain", "--", str(f.relative_to(ROOT))).splitlines():
        if line.startswith("committer-time "):
            cur = int(line.split()[1])
        elif line.startswith("\t") and cur:
            x = line[1:].split(";")
            if len(x) >= 2 and x[0].strip().isdigit():
                out[x[0].strip()] = cur
    return out


def file_times(folder=None):
    """Dateiname -> Commit-Zeit (Unix) der letzten Aenderung unter shownotes/spreaker/."""
    out, cur = {}, None
    for line in _git("log", "--format=@%ct", "--name-only", "--", str((folder or SRC).relative_to(ROOT))).splitlines():
        if line.startswith("@"):
            cur = int(line[1:])
        elif line.strip() and cur:
            out.setdefault(Path(line.strip()).name, cur)   # git log beginnt mit dem neuesten Commit
    return out


def qa_current(ids):
    """T25: Freigabe gilt fuer die gepruefte Fassung. Wurde die Datei nach dem QA-Eintrag der Folge geaendert (z. B. Links
    nachgetragen), wartet sie auf eine neue QA-Zeile. Ohne volle git-Historie ist das nicht pruefbar -> alles wartet (sicher)."""
    if _git("rev-parse", "--is-shallow-repository").strip() != "false":
        return set(), {str(i): "git-Historie fehlt (checkout mit fetch-depth: 0 noetig)" for i in ids}
    qt, ft, ok, why = qa_times(), file_times(), set(), {}
    for i in ids:
        q, t = qt.get(str(i)), ft.get(f"{i}.html")
        if q is None or t is None:
            why[str(i)] = "Zeitpunkt nicht lesbar"
        elif t > q:
            why[str(i)] = "nach der QA geaendert"
        else:
            ok.add(str(i))
    return ok, why


def pending(applied, ids=None, with_invalid=False):
    """[(episode_id, html, hash, errors)] aller Dateien, die noch nicht mit dieser Fassung geschrieben sind (ungueltige nur einmal je Fassung protokolliert)."""
    out = []
    for f in sorted(SRC.glob("*.html")):
        if not f.stem.isdigit():
            continue
        eid = int(f.stem)
        if ids and eid not in ids:
            continue
        raw = f.read_text("utf-8").strip(); h = sha(raw)
        hist = [x for x in applied.get(eid, []) if x["hash"] == h]
        if any(x["status"] in ("ok", "unchanged") or (x["status"] == "invalid" and not with_invalid) for x in hist):
            continue
        if len([x for x in hist if x["status"] in ("error", "mismatch", "invalid")]) >= MAX_TRIES:
            continue
        out.append((eid, raw, h, check_html(raw)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=150); ap.add_argument("--dry-limit", type=int, default=10)
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--ids", default="")
    a = ap.parse_args()
    ids = {int(x) for x in re.findall(r"\d+", a.ids)} or None
    if not SRC.exists():
        print("Kein shownotes/spreaker/ - nichts zu tun"); return 0
    applied = read_applied()
    todo = pending(applied, ids, with_invalid=a.check)
    bad = [(e, errs) for e, _, _, errs in todo if errs]
    print(f"{len(todo)} Folgen offen, davon {len(bad)} ungueltig")
    for e, errs in bad:
        print(f"  {e}: " + "; ".join(errs))
    if a.check:
        return 1 if bad else 0
    if (SN / "PAUSED").exists():
        print("shownotes/PAUSED vorhanden - Lauf uebersprungen"); return 0
    dry = a.dry_run or not (SN / "APPROVED").exists()
    if dry:
        print("Dry-Run (keine Datei shownotes/APPROVED bzw. --dry-run)")
    else:   # Schreiben nur fuer Folgen, die die QA einzeln freigegeben hat (shownotes/QA.txt: ok oder fixed); APPROVED ist der Hauptschalter
        ok = qa_ok()
        held = [t for t in todo if str(t[0]) not in ok]
        todo = [t for t in todo if str(t[0]) in ok]
        cur, why = qa_current([t[0] for t in todo])   # T25: nur die Fassung, die die QA geprueft hat
        stale = [t for t in todo if str(t[0]) not in cur]
        todo = [t for t in todo if str(t[0]) in cur]
        print(f"QA-Freigabe je Folge: {len(todo)} freigegeben, {len(held)} warten auf die QA, {len(stale)} seit der QA geaendert (warten auf neue Pruefung)")
        for e, *_ in stale[:30]:
            print(f"  {e}: {why.get(str(e), '')}")
    sp = Spreaker()
    if not sp.login():
        return 1
    # Reihenfolge: meistgehoerte zuerst (Statistik, 24 h zwischengespeichert), dann neueste
    eps = sp.episodes()
    pl = {}
    try:
        if PLAYS.exists() and time.time() - PLAYS.stat().st_mtime < 86400:
            pl = {int(k): v for k, v in json.loads(PLAYS.read_text("utf-8")).items()}
        else:
            pl = sp.plays(sorted({v["show_id"] for v in eps.values()}))
            if pl:
                PLAYS.parent.mkdir(parents=True, exist_ok=True); PLAYS.write_text(json.dumps(pl, sort_keys=True), "utf-8")
    except Exception as e:
        print("Abrufe nicht lesbar:", str(e)[:120])
    plays = lambda e: pl.get(e) or eps.get(e, {}).get("plays", 0)
    valid = [t for t in todo if not t[3]]
    valid.sort(key=lambda t: (-plays(t[0]), -t[0]))
    unknown = [t for t in valid if t[0] not in eps]
    valid = [t for t in valid if t[0] in eps]
    if not dry:
        for e, _, h, errs in [t for t in todo if t[3]]:
            log_applied(e, "invalid", h, plays(e), eps.get(e, {}).get("title", ""), "; ".join(errs))
        for e, _, h, _ in unknown:
            log_applied(e, "error", h, 0, "", "Folge gehoert zu keiner eigenen Show")
    batch = valid[: (a.dry_limit if dry else a.limit)]
    print(f"{len(batch)} Folgen in diesem Lauf" + (" (Dry-Run)" if dry else ""))
    rows, written, errors = [], 0, 0
    for eid, raw, h, _ in batch:
        title = eps[eid]["title"]
        try:
            cur = sp.req("GET", f"/episodes/{eid}")["episode"]
            old = cur.get("description") or ""
            if dry:
                diff = "\n".join(difflib.unified_diff(to_text(old), to_text(raw), "aktuell", "neu", lineterm="", n=1))
                rows.append(f"## {html.escape(cur.get('title') or title)} ({eid}, {plays(eid)} Abrufe, {len(raw)} Zeichen)\n\n```diff\n{diff or '(kein Unterschied)'}\n```\n\n<details><summary>Neue Beschreibung (HTML)</summary>\n\n```html\n{raw}\n```\n\n</details>\n")
                continue
            if same_on_spreaker(cur, raw):
                log_applied(eid, "unchanged", h, plays(eid), title, "Beschreibung ist schon aktuell"); continue
            bk = SN / "spreaker_backup" / f"{eid}.json"   # alte Fassung sichern, bevor sie ueberschrieben wird (nichts loeschen)
            if not bk.exists():
                bk.parent.mkdir(parents=True, exist_ok=True)
                bk.write_text(json.dumps({"episode_id": eid, "saved": now(), "title": cur.get("title") or "", "description": old,
                                          "description_html": cur.get("description_html") or ""}, ensure_ascii=False, indent=1) + "\n", "utf-8")
            sp.req("POST", f"/episodes/{eid}", data={"description": raw})
            after = sp.req("GET", f"/episodes/{eid}")["episode"]
            if (after.get("title") or "") != (cur.get("title") or ""):
                log_applied(eid, "mismatch", h, plays(eid), title, "Titel hat sich geaendert - bitte pruefen"); errors += 1; continue
            if same_on_spreaker(after, raw):
                log_applied(eid, "ok", h, plays(eid), title, f"geschrieben und geprueft ({len(raw)} Zeichen)"); written += 1
            else:
                log_applied(eid, "mismatch", h, plays(eid), title, f"Spreaker hat {len(after.get('description') or '')} Zeichen gespeichert, erwartet {len(raw)}"); errors += 1
            time.sleep(0.5)
        except PermissionError as e:
            print(f"::error::{e}"); log_applied(eid, "error", h, plays(eid), title, str(e)); return 1
        except Exception as e:
            errors += 1
            if dry:
                rows.append(f"## {eid}\n\nFehler: {html.escape(str(e)[:200])}\n")
            else:
                log_applied(eid, "error", h, plays(eid), title, str(e)[:200])
    if dry:
        head = (f"# Dry-Run Shownotes -> Spreaker\n\n{now()} · {len(todo)} Folgen offen, {len(bad)} ungueltig, {len(unknown)} unbekannt, {len(batch)} im Diff (meistgehoerte zuerst). "
                f"Schreiben erst mit Datei shownotes/APPROVED.\n\n")
        if bad:
            head += "## Ungueltige Dateien\n\n" + "".join(f"- {e}: {'; '.join(errs)}\n" for e, errs in bad) + "\n"
        if unknown:
            head += "## Nicht in den eigenen Shows\n\n" + "".join(f"- {t[0]}\n" for t in unknown) + "\n"
        DRY.parent.mkdir(parents=True, exist_ok=True); DRY.write_text(head + "\n".join(rows), "utf-8")
        print(f"Diff fuer {len(rows)} Folgen in {DRY.relative_to(ROOT) if DRY.is_relative_to(ROOT) else DRY}")
        return 0
    print(f"Fertig: {written} geschrieben, {errors} Fehler, {len(valid) - len(batch)} verbleiben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
