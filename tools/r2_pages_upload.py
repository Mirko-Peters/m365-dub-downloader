"""Seiten aus r2out/ (Seitenbau) in den R2-Bucket laden: Schluessel pages/<pfad>, Content-Type text/html, nur geaenderte Dateien (MD5-Manifest in data/cache).
Es wird nichts geloescht. Zugang ueber R2_ACCOUNT_ID, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY (GitHub-Secrets). Aufruf: python tools/r2_pages_upload.py [r2out]"""
import hashlib, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "r2out"
MAN = ROOT / "data" / "cache" / "r2_pages.json"


def main():
    if not SRC.exists():
        print("r2out/ fehlt - nichts zu laden"); return 0
    for k in ("R2_ACCOUNT_ID", "R2_BUCKET", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"):
        if not os.environ.get(k):
            print(f"{k} fehlt - R2-Upload uebersprungen (Seiten bleiben nur erreichbar, wenn sie schon im Bucket liegen)"); return 0
    import boto3
    s3 = boto3.client("s3", endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com", aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"], aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")
    bucket = os.environ["R2_BUCKET"]
    try: man = json.loads(MAN.read_text("utf-8")) if MAN.exists() else {}
    except Exception: man = {}
    files = [f for f in SRC.rglob("*") if f.is_file()]
    todo = []
    for f in files:
        key = "pages/" + f.relative_to(SRC).as_posix(); data = f.read_bytes(); h = hashlib.md5(data).hexdigest()
        if man.get(key) != h: todo.append((key, data, h))
    print(f"{len(files)} Seiten, {len(todo)} neu oder geaendert")
    ok = err = 0
    def put(item):
        key, data, h = item
        ct = "text/html; charset=utf-8" if key.endswith(".html") else "application/octet-stream"
        try: s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=ct, CacheControl="public, max-age=600"); return key, h, None
        except Exception as e: return key, h, str(e)[:120]
    with ThreadPoolExecutor(16) as ex:
        for key, h, e in ex.map(put, todo):
            if e:
                err += 1
                if err <= 5: print("Fehler", key, e)
            else:
                ok += 1; man[key] = h
    MAN.parent.mkdir(parents=True, exist_ok=True); MAN.write_text(json.dumps(man, sort_keys=True), encoding="utf-8")
    # T41: geaenderte Seiten fuer den Purge nach dem Deploy (der Site-Worker haelt R2-Seiten 4 h im Kanten-Cache)
    changed = sorted("/" + k[len("pages/"):-len("index.html")] for k, _d, _h in todo if k.endswith("/index.html") and man.get(k) == _h)
    Path(os.environ.get("R2_CHANGED_OUT", "r2-changed.json")).write_text(json.dumps(changed), encoding="utf-8")
    print(f"fuer den Purge vorgemerkt: {len(changed)} Seiten")
    print(f"hochgeladen: {ok}, Fehler: {err}, im Manifest: {len(man)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
