"""Offline-Regression: python3 tools/test_fetch_en_episodes.py."""
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import fetch_en_episodes as F
with patch("site_fetch.fetch", return_value={}):
    import site_podpage as P


def feed(*records):
    root = ET.Element("rss")
    channel = ET.SubElement(root, "channel")
    for rec in records:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = rec["title"]
        ET.SubElement(item, "guid").text = f"https://api.spreaker.com/episode/{rec['id']}"
        ET.SubElement(item, "pubDate").text = rec.get("pub", "Sat, 31 Oct 2026 18:00:00 +0000")
        ET.SubElement(item, "enclosure", url=f"https://api.spreaker.com/download/episode/{rec['id']}/audio.mp3")
    return ET.tostring(root, encoding="unicode")


class EpisodeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.file = self.data / "en_episodes.json"

    def fetch(self, xml):
        with patch.object(F, "ROOT", self.root), patch.object(F, "get", return_value=xml):
            F.main()
        return json.loads(self.file.read_text("utf-8"))

    def test_same_title_and_repeated_feed(self):
        first = {"title": "Gleicher Titel", "id": "73025082", "pub": "Fri, 17 Jul 2026 18:00:02 +0000"}
        second = {"title": "Gleicher Titel", "id": "75941556"}
        result = self.fetch(feed(first, second, second))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[F.norm(first["title"])]["spreaker_id"], first["id"])
        self.assertEqual(result[F.norm(first["title"]) + " " + second["id"]]["spreaker_id"], second["id"])
        with patch.object(P, "D", self.data), patch.object(P, "_SIDS", {}):
            self.assertEqual(P.spreaker_id({"name": first["title"]}), first["id"])
            self.assertEqual({sid for _, sid in P._EN_SID()["pub"]}, {first["id"], second["id"]})
            self.assertEqual(P.spreaker_id({"name": "Unbekannter Titel", "published": "2026-10-31T18:00:00+00:00"}), second["id"])
        self.assertEqual(self.fetch(feed(second, first)), result)
        renamed = dict(second, title="Neuer Titel")
        updated = self.fetch(feed(renamed))
        self.assertEqual(len(updated), 2)
        self.assertEqual(updated[F.norm(first["title"]) + " " + second["id"]]["title"], renamed["title"])
        with patch.object(P, "D", self.data), patch.object(P, "_SIDS", {}):
            self.assertEqual(P.spreaker_id({"name": renamed["title"]}), second["id"])

    def test_suffix_collision(self):
        first = {"title": "Gleicher Titel", "id": "73025082"}
        occupied = {"title": "Gleicher Titel 75941556", "id": "73025384"}
        second = {"title": "Gleicher Titel", "id": "75941556"}
        result = self.fetch(feed(first, occupied, second))
        self.assertEqual(len(result), 3)
        self.assertEqual(result[F.norm(occupied["title"])]["spreaker_id"], occupied["id"])
        self.assertEqual(self.fetch(feed(second, occupied, first)), result)

    def test_real_data_and_site_readers(self):
        old = json.loads((ROOT / "data/en_episodes.json").read_text("utf-8"))
        notes = json.loads((ROOT / "data/show_notes/en.json").read_text("utf-8"))
        episodes = notes["episodes"]
        records = episodes.values() if isinstance(episodes, dict) else episodes
        new = next(r for r in records if str(r["id"]) == "75941556")
        title_key = F.norm(new["title"])
        self.file.write_text(json.dumps(old), encoding="utf-8")
        transcript = self.data / "en_transcripts" / f"{old[title_key]['transcript']}.txt"
        transcript.parent.mkdir()
        transcript.write_text("Vorhandenes Transkript bleibt unverändert.", encoding="utf-8")
        result = self.fetch(feed(new))
        self.assertEqual({k: result[k] for k in old}, old)
        self.assertEqual(sum(v["spreaker_id"] == "75941556" for v in result.values()), 1)
        self.assertEqual(result[title_key]["spreaker_id"], "73025082")
        self.assertEqual(transcript.read_text("utf-8"), "Vorhandenes Transkript bleibt unverändert.")
        self.assertEqual(self.fetch(feed(new)), result)
        self.fetch(feed(dict(new, id="73025082", pub=old[title_key]["pub"])))
        self.assertEqual(json.loads(self.file.read_text("utf-8"))[title_key]["transcript"], old[title_key]["transcript"])
        notes_dir = self.data / "show_notes"
        notes_dir.mkdir()
        (notes_dir / "en.json").write_text(json.dumps(notes), encoding="utf-8")
        podpage = [{"name": new["title"], "slug": "azure-virtual-desktop-simply-explained",
                    "published": "2026-07-17T18:00:02+00:00", "create_time": "2026-07-17T18:00:02+00:00"},
                   {"name": "Podpage-Stichtag", "slug": "podpage-stichtag",
                    "published": "2026-10-30T23:59:59+00:00", "create_time": "2026-10-30T23:59:59+00:00"}]
        with patch.object(P, "D", self.data), patch.object(P, "_SIDS", {}), patch.object(P, "_EXTRA", []), patch.object(P, "_SLUGS_F", self.data / "episode_slugs.json"):
            self.assertEqual(P.spreaker_id(podpage[0]), "73025082")
            self.assertIn("75941556", {sid for _, sid in P._EN_SID()["pub"]})
            extra = P.spreaker_extra(podpage)
            added = [e for e in extra if e["spreaker_id"] == "75941556"]
            self.assertEqual(len(added), 1)
            self.assertNotEqual(added[0]["slug"], podpage[0]["slug"])
            self.assertEqual(P.spreaker_id(added[0]), "75941556")
        print("Echtdaten: 75941556 genau einmal vorhanden; 73025082 bleibt Titeltreffer; neue Seite erkannt.")


if __name__ == "__main__":
    unittest.main()
