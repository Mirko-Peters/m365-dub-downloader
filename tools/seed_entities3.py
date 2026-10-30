#!/usr/bin/env python3
"""Dritter Seed: RPA, Process Mining und Microsoft Flow (veraltet, ersetzt durch Power Automate). Idempotent."""
import json
P = "data/entities.json"
D = json.load(open(P)); M = {e["id"]: e for e in D}
MT = "microsoft-tool"
NEW = [
    {"id": "rpa", "type": "concept", "name": "Robotic Process Automation", "aliases": ["RPA", "Robotic Process Automation (RPA)", "Desktop-Automatisierung"],
     "desc": {"en": "Software robots that mimic clicks and keystrokes to automate repetitive tasks in applications that offer no API. In Microsoft's world this is Power Automate for desktop.",
              "de": "Software-Roboter, die Klicks und Tastatureingaben nachahmen, um wiederkehrende Aufgaben in Anwendungen ohne Schnittstelle zu automatisieren. Bei Microsoft ist das Power Automate für Desktop."},
     "long": {"en": "Robotic Process Automation (RPA) lets software robots operate user interfaces the way a person does: open applications, copy data between screens, fill forms and trigger follow-up steps. It is the right tool when a system has no API or connector. In the Microsoft ecosystem, attended and unattended RPA is done with desktop flows in Power Automate for desktop, often combined with cloud flows that start the robot and with AI steps for documents. Because UI-based automation breaks when screens change, APIs and connectors should be preferred where they exist.",
              "de": "Robotic Process Automation (RPA) lässt Software-Roboter Benutzeroberflächen bedienen wie ein Mensch: Anwendungen öffnen, Daten zwischen Masken kopieren, Formulare ausfüllen und Folgeschritte auslösen. Das passt, wenn ein System keine Schnittstelle oder keinen Connector hat. Im Microsoft-Umfeld läuft RPA mit Desktop-Flows in Power Automate für Desktop, beaufsichtigt oder unbeaufsichtigt, oft kombiniert mit Cloud-Flows, die den Roboter starten, und KI-Schritten für Dokumente. Da oberflächenbasierte Automatisierung bei geänderten Masken bricht, sind Schnittstellen und Connectoren vorzuziehen, wo es sie gibt."},
     "web": "", "wikidata": "", "wikipedia": "https://en.wikipedia.org/wiki/Robotic_process_automation", "docs": "https://learn.microsoft.com/power-automate/desktop-flows/introduction",
     "rel": [["related_to", "power-automate-desktop"], ["related_to", "power-automate"], ["related_to", "automation"], ["related_to", "low-code-tool"]]},
    {"id": "process-mining", "type": "concept", "name": "Process Mining", "aliases": ["Prozess Mining", "Prozessanalyse", "Process Advisor", "Process mining in Power Automate"],
     "desc": {"en": "Analysing event logs from business systems to reconstruct how processes really run, where they stall and where automation pays off. Microsoft offers it in Power Automate as process mining.",
              "de": "Analyse von Ereignisprotokollen aus Geschäftssystemen, um zu rekonstruieren, wie Prozesse tatsächlich ablaufen, wo sie stocken und wo sich Automatisierung lohnt. Microsoft bietet das in Power Automate als Process Mining an."},
     "long": {"en": "Process mining reads the timestamps and activities that business systems already record and rebuilds the real process as a map: the common paths, the rare detours, waiting times and rework loops. It answers where a process is slow or inconsistent before anyone automates it. In Power Automate, process mining (formerly Process Advisor) visualises such maps and points to candidates for automation with cloud and desktop flows, while task mining captures how people work on screen.",
              "de": "Process Mining liest die Zeitstempel und Aktivitäten, die Geschäftssysteme ohnehin protokollieren, und baut daraus den tatsächlichen Prozess als Karte nach: die häufigen Pfade, seltene Umwege, Wartezeiten und Schleifen durch Nacharbeit. So zeigt sich, wo ein Prozess langsam oder uneinheitlich ist, bevor jemand automatisiert. In Power Automate visualisiert Process Mining (früher Process Advisor) solche Karten und weist auf Kandidaten für die Automatisierung mit Cloud- und Desktop-Flows hin; Task Mining erfasst dazu, wie Menschen am Bildschirm arbeiten."},
     "web": "", "wikidata": "", "wikipedia": "https://en.wikipedia.org/wiki/Process_mining", "docs": "https://learn.microsoft.com/power-automate/process-mining/overview",
     "rel": [["related_to", "power-automate"], ["related_to", "automation"], ["related_to", "rpa"]]},
    {"id": "microsoft-flow", "type": "product", "name": "Microsoft Flow", "aliases": ["Flow", "MS Flow", "Microsoft Flow (Power Automate)"],
     "desc": {"en": "Former name of Power Automate. Microsoft renamed the workflow service in November 2019; the product continues as Power Automate.",
              "de": "Früherer Name von Power Automate. Microsoft hat den Workflow-Dienst im November 2019 umbenannt; das Produkt wird als Power Automate fortgeführt."},
     "web": "", "wikidata": "", "wikipedia": "https://en.wikipedia.org/wiki/Power_Automate", "docs": "https://learn.microsoft.com/power-automate/",
     "rel": [["developed_by", "microsoft"], ["instance_of", MT], ["related_to", "power-automate"]],
     "outdated": True, "replaced_by": "power-automate", "start": "2016-11", "end": "2019-11"},
]
ch = 0
for n in NEW:
    if n["id"] not in M:
        D.append(n); M[n["id"]] = n; ch += 1
ids = set(M)
bad = [(e["id"], r) for e in D for r in e.get("rel", []) if r[1] not in ids]
longd = [e["id"] for e in D if len(e["desc"]["en"]) > 300 or len(e["desc"]["de"]) > 300]
assert not bad and not longd, (bad, longd)
pa = M["power-automate"]
for r in (["related_to", "rpa"], ["related_to", "process-mining"], ["related_to", "microsoft-flow"]):
    if r not in pa["rel"]:
        pa["rel"].append(r)
json.dump(D, open(P, "w"), ensure_ascii=False, indent=1)
print("neu", ch, "gesamt", len(D))
