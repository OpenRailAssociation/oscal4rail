# ADR-006: OSCAL4Rail und Rulemapping – Komplementarität oder Konkurrenz?

**Status:** Accepted
**Date:** 2026-06-25
**Deciders:** Jens Grote, Arpad Vasarhelyi
**Technical Story:** Evaluation des Rulemapping-Builder-Exports (Pilot BS-KI 2.1, 2026-06-25)

---

## Kontext und Problemstellung

Im Rahmen der SPRIND-Initiative „Law as Code" hat sich Rulemapping als zentrale Methodik für maschinenlesbare Gesetzgebung etabliert. OSCAL4Rail verfolgt mit NIST OSCAL einen anderen Ansatz für dasselbe Grundproblem: Regulatorik maschinenlesbar machen.

**Die zentrale Frage:** Sind OSCAL4Rail und Rulemapping konkurrierende Ansätze – oder ergänzende Werkzeuge, die durch Integration ihre jeweiligen Stärken ausspielen?

### Auslöser

- SPRIND-Initiative „Law as Code" mit Rulemapping als Kernmethodik
- Pilot-Test des Rulemapping Builders mit BS-KI 2.1 (erfolgreich, 2026-06-25)
- Bahnen unterliegen einer tiefen Regulierungskaskade (EU → National → Branche → Konzern → Tochtergesellschaft)
- Bedarf an Klarheit für die OpenRail-Incubation und Stakeholder-Kommunikation

### Die Regulierungskaskade

Eisenbahnregulierung ist kein flaches Regelwerk, sondern eine Vererbungshierarchie mit konformer Spezialisierung:

```
EU-Richtlinie / TSI (abstrakt)
  "Systeme müssen gegen bekannte Schwachstellen geschützt werden"
    │
    ▼ nationale Umsetzung
BSI IT-Grundschutz / BSKG / EBO
  "Patches müssen nach Risikobewertung eingespielt werden"
    │
    ▼ Konzernregel
DB Richtlinie
  "Du musst nach BSI Grundschutz patchen"
    │
    ├─▼ DB Systel                          ├─▼ DB InfraGO
    │  "CVSS Score bestimmt Frist:         │  "Nur KRITIS-Systeme,
    │   Critical ≤72h, High ≤7d..."        │   nach Methode XYZ"
    │                                       │
    └── beide KONFORM zur DB-Richtlinie ───┘
```

Jede Ebene **spezialisiert** die darüber liegende – sie darf konkretisieren, aber nicht widersprechen. Unterschiedliche Tochtergesellschaften dürfen die gleiche Oberregel unterschiedlich, aber jeweils konform umsetzen.

---

## Entscheidungstreiber (Decision Drivers)

1. **Regelinhalt** – Was steht in der Regel? Verbatim, auditierbar.
2. **Anwendbarkeit** – Für wen gilt es? (Kanal, Verkehrsträger, Obligation)
3. **Entscheidungslogik** – Unter welchen Bedingungen gilt es? (Schwellenwerte, Ausnahmen)
4. **Change Tracking** – Was hat sich geändert? Neu, weggefallen, verschärft, gelockert, ersetzt?
5. **Konsistenz & Redundanz** – Gibt es Doppelungen, Widersprüche, Ergänzungen über Regelwerke und Ebenen hinweg?
6. **Kaskade & Vererbung** – Kann die Hierarchie EU → National → Konzern → Tochter abgebildet werden?
7. **Konformitätsprüfung** – Ist eine Spezialisierung noch konform zur Oberregel?
8. **Schema-Validierbarkeit** – CI-fähige Validierung gegen ein formales Schema?
9. **Stabile Identifikatoren** – Für Versionsdiff und systemübergreifende Referenzierung?
10. **Offenheit** – Kein Vendor-Lock-in, Open Source, offene Standards?
11. **Unabhängigkeit** – Jeder Ansatz funktioniert auch allein?

---

## Analyse: Stärken und Schwächen

### OSCAL4Rail

| Dimension | Stärke | Schwäche |
|-----------|--------|----------|
| Regelinhalt | Verbatim-Zitate, auditierbar, keine Interpretation | – |
| Anwendbarkeit | Matrix-Modell (Kanal × Verkehrsträger → Obligation) | Statisch, keine Bedingungslogik |
| Entscheidungslogik | – | Nicht modellierbar. Schwellenwerte nur als Freitext |
| Change Tracking | Semantischer Diff auf Control-Ebene: neu, geändert, entfallen | – |
| Konsistenz & Redundanz | Vergleich zwischen Katalogen (Diff/Alignment) | Widerspruchserkennung noch nicht implementiert |
| Kaskade & Vererbung | ✅ OSCAL-Schichtenmodell: Catalog → Profile → Component Definition | – |
| Konformitätsprüfung | Architektonisch möglich (Profile-Vererbung), noch nicht gebaut | – |
| Schema-Validierung | ✅ NIST JSON Schema, CI-fähig | – |
| Stabile IDs | ✅ Kapitel-basiert, semantisch | – |
| Offenheit | ✅ Apache 2.0, OSCAL selbst CC0, bestehendes Tooling-Ökosystem | – |

### Rulemapping

| Dimension | Stärke | Schwäche |
|-----------|--------|----------|
| Regelinhalt | – | Kein Verbatim-Modell. Regeltext nur als Freitext in `alttext` |
| Anwendbarkeit | – | Kein Applicability-Modell |
| Entscheidungslogik | ✅ Boolesche Operatoren (OR, AND, XOR, NAND, NOR), Negation, Baumstruktur | Schwellenwerte nur als Freitext im Knotentitel |
| Change Tracking | – | Keine Versionierung im Format, kein Diff-Tooling |
| Konsistenz & Redundanz | – | Kein Vergleich zwischen Rulemaps vorgesehen |
| Kaskade & Vererbung | – | Kein Schichtenmodell, keine Hierarchie zwischen Regelebenen |
| Konformitätsprüfung | – | Nicht vorgesehen |
| Schema-Validierung | – | Kein publiziertes Schema (XSD/JSON Schema) |
| Stabile IDs | – | Numerisch (auto-increment), nicht semantisch |
| Offenheit | RUML als offener Standard angekündigt. Builder kostenlos nutzbar | Stand heute: proprietäres Format, nicht schema-validierbar |

---

## Kernbefund

**OSCAL4Rail und Rulemapping lösen fundamental verschiedene Probleme.**

### Unterschiedliche Einsatzzwecke

| Dimension | Rulemapping | OSCAL4Rail |
|-----------|-------------|------------|
| **Zielgruppe** | Bürger, Sachbearbeiter, Juristen, Gesetzgeber | IT-Architekten, Compliance-Teams, Normungsgremien |
| **Kernfrage** | „Trifft diese Regel auf *meinen Einzelfall* zu?" | „Wie verwalte ich *10.000 Regeln* über 5 Ebenen mit Änderungsverfolgung?" |
| **Interaktion** | Mensch geht interaktiv durch Entscheidungsbaum | Maschine prüft automatisiert gegen Katalog |
| **Ergebnis** | Ein Ja/Nein für einen konkreten Fall | Compliance-Report über alle Systeme und Regeln |
| **Skala** | Ein Gesetz, ein Fall | Hunderte Regelwerke, tausende Controls, über Jahre |
| **Analogie** | Berater am Schalter / Self-Service-Webseite | Wirtschaftsprüfer mit Checkliste |

### Rulemapping: Bürger-Staat-Dialog

Typische Rulemapping-Use-Cases:
- „Brauche ich für meinen Anbau eine Baugenehmigung?" → Grundfläche? Höhe? Bebauungsplan? → Ja/Nein
- „Brauche ich ein Visum für Thailand?" → Aufenthaltsdauer? Zweck? Nationalität? → Ja, Typ X / Nein
- „Welche Steuerformulare muss ich ausfüllen?" → Selbständig? Kinder? Einkommen? → Anlage N + KAP

Das ist ein **interaktiver Einzelfall-Entscheidungsbaum** – ein Mensch geht den Baum durch und bekommt eine Antwort.

### OSCAL4Rail: Regulierungs-Management über Ebenen und Zeit

Typische OSCAL4Rail-Use-Cases:
- „Wir betreiben 4.700 Haltestellen und 12 IT-Systeme. Welche 42 Regeln gelten jeweils?"
- „Was hat sich seit letztem Jahr geändert? Welche Regeln sind verschärft, gelockert, neu, weggefallen?"
- „Ist unsere Umsetzung (DB Systel: CVSS-basiert) noch konform zur Oberregel (DB Richtlinie: BSI Grundschutz)?"
- „Die TSI wurde aktualisiert – welche unserer Systeme sind betroffen?"

Das ist **automatisierte Massenprüfung mit Versionsverwaltung** – kein Mensch geht interaktiv durch einen Baum.

### Keine Konkurrenz – verschiedene Welten

Die beiden Ansätze *können* sich an einer Schnittstelle berühren: Wenn ein Gesetzgeber per Rulemapping ein Gesetz modelliert, *könnte* das Ergebnis als Input in einen OSCAL-Katalog einfließen. Aber das ist eine **Übergabe**, keine Integration im Sinne von „beide arbeiten am selben Artefakt".

| | Rulemapping-Welt | Übergabe | OSCAL4Rail-Welt |
|---|-----------------|----------|-----------------|
| Akteur | Gesetzgeber/Jurist | → publiziert → | Compliance-Team/IT-Architekt |
| Artefakt | Entscheidungsbaum (Rulemap) | → wird zu → | Control im Katalog (OSCAL) |
| Zweck | „So entscheidest du" | | „Das musst du einhalten" |

### Nicht jede Regel braucht einen Entscheidungsbaum

Viele Regeln sind einfache, binäre Aussagen ohne jede Entscheidungslogik:
- „Code muss in Git öffentlich lesbar abgelegt werden."
- „Architekturentscheidungen müssen dokumentiert und veröffentlicht sein."
- „Systeme müssen gepatcht werden."

Hier gibt es nichts zu „entscheiden" – es gilt, Punkt. Kein Schwellenwert, keine Ausnahme, kein Baum. Das ist die Mehrheit aller Regeln.

Der BS-KI 2.1 Pilot-Test (mit Schwellenwert ≥800 Fahrgäste und mehrdimensionaler Applicability) ist ein *ungewöhnlich komplexer* Fall – kein Regelfall.

---

## Entscheidung

**OSCAL4Rail und Rulemapping lösen verschiedene Probleme für verschiedene Zielgruppen. Sie sind weder Konkurrenten noch zwingend zu integrieren.**

- **OSCAL4Rail** ist das Werkzeug für **Regulierungs-Management**: Kataloge verwalten, Versionen tracken, Kaskaden abbilden, Compliance maschinell prüfen.
- **Rulemapping** ist das Werkzeug für **Einzelfall-Entscheidungen**: Bürger-Self-Service, Sachbearbeiter-Unterstützung, interaktive Prüfung.

### Möglicher Berührungspunkt

Dort wo ein Regelwerk tatsächlich komplexe Bedingungslogik enthält (Schwellenwerte, Ausnahmen, kontextabhängige Anwendbarkeit), *könnte* ein Rulemapping-Entscheidungsbaum als ergänzendes Artefakt neben dem OSCAL4Rail-Control existieren. Das ist aber die Ausnahme, nicht die Regel.

```yaml
# Nur bei komplexer Bedingungslogik – nicht der Standard
controls:
  - id: bs-ki-2.1
    title: "Aktuelle Uhrzeit"
    parts:
      - name: statement
        prose: "Bei Haltestellen mit weniger als 800 Ein- und Aussteigern..."
    links:
      - href: "rulemaps/bs-ki-2.1.xml"
        rel: "decision-logic"
        text: "Entscheidungsbaum: Anwendbarkeitsbedingungen"
```

### Was OSCAL4Rail NICHT von Rulemapping übernimmt

- Kein interaktiver Bürger-Dialog
- Kein Einzelfall-Entscheidungsbaum als Kernkonzept
- Keine Übernahme des Rulemapping-Formats als primäres Datenmodell

### Was OSCAL4Rail allein leistet (und Rulemapping nicht kann)

- Regulierungskaskade (EU → National → Konzern → Tochter)
- Semantischer Diff über Versionen
- Konformitätsprüfung zwischen Ebenen
- Schema-validierte Kataloge mit stabilen Identifikatoren
- Change Tracking: was ist neu, weggefallen, verschärft, gelockert

---

### Ergänzung auf Prozessebene – nicht auf Datenebene

Die Ergänzung von Rulemapping und OSCAL4Rail liegt nicht darin, beide Formate zusammenzuschalten, sondern darin, dass sie **verschiedene Phasen im Lebenszyklus einer Regel** bedienen:

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Regel erstellen (Regelschreiber)                   │
│                                                              │
│  Gesetzgeber / Normungsgremium / Fachexperte                 │
│  ├── schreibt Gesetz/Vorschrift                              │
│  └── modelliert Entscheidungslogik im Rulemap Builder        │
│       → „Wann gilt was? Welche Bedingungen? Ausnahmen?"      │
│                                                              │
│  Werkzeug: Rulemapping                                       │
│  Artefakt: Entscheidungsbaum (Rulemap)                       │
└──────────────────────────────┬──────────────────────────────┘
                               │ publiziert Regeltext
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Regel verwalten (Compliance-Team)                  │
│                                                              │
│  OSCAL4Rail liest den publizierten Regeltext                 │
│  ├── extrahiert verbatim Controls                            │
│  ├── ordnet Applicability zu                                 │
│  ├── bildet Kaskade ab (EU → National → Konzern → Tochter)  │
│  └── trackt Änderungen über Versionen                        │
│                                                              │
│  Werkzeug: OSCAL4Rail                                        │
│  Artefakt: Katalog mit Controls                              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Katalog bereitgestellt
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: Regel prüfen (IT-Architekten / AI-Agents)          │
│                                                              │
│  Automatisierte Compliance-Prüfung:                          │
│  ├── Welche Controls gelten für mein System?                 │
│  ├── Ist meine Umsetzung konform?                            │
│  └── Was hat sich seit letzter Prüfung geändert?             │
│                                                              │
│  Werkzeug: MCP-Agents / Compliance-Tooling                   │
│  Artefakt: Compliance-Report                                 │
└─────────────────────────────────────────────────────────────┘
```

**Zwei Werkzeuge, zwei Phasen:**
- Rulemapping hilft dem **Ersteller** der Regel, sie präzise und widerspruchsfrei zu formulieren
- OSCAL4Rail hilft dem **Anwender** der Regel, sie maschinell zu verwalten und zu prüfen

---

## Konsequenzen

### Positiv

- Klare Positionierung: OSCAL4Rail muss sich nicht an Rulemapping messen lassen – anderer Zweck
- OSCAL4Rail bleibt schlank und fokussiert auf Regulierungs-Management
- Kein Druck, Rulemapping-Integration als Feature zu bauen
- Gegenüber SPRIND/OpenRail klar kommunizierbar: „Verschiedene Werkzeuge, verschiedene Probleme, möglicher Berührungspunkt an der Schnittstelle Gesetzgeber → Compliance-Team"
- Die Regulierungskaskade und Change Tracking sind USPs von OSCAL4Rail, die Rulemapping nicht adressiert

### Negativ / Risiken

- Rulemapping könnte fälschlicherweise als Konkurrent wahrgenommen werden → Mitigation: dieser ADR als klare Kommunikationsgrundlage
- Bei SPRIND-Kontaktaufnahme muss die Differenzierung sauber erklärt werden, um nicht in einen „wer ist besser"-Vergleich zu geraten

### Offen / noch zu klären

- Ist eine Übergabe-Schnittstelle (Rulemapping → OSCAL4Rail) in der Praxis relevant oder rein theoretisch?
- Wird RUML als offener Standard publiziert? (Monitoring, aber keine Abhängigkeit)
- Gibt es Regelwerke mit so viel Bedingungslogik, dass eine systematische Verknüpfung sinnvoll wird?

---

## Betrachtete Alternativen

### Alternative 1: Nur OSCAL4Rail (kein Rulemapping)

- (+) Einfacher, keine externe Abhängigkeit
- (-) Entscheidungslogik und Bedingungen nicht modellierbar
- (-) Agent muss Freitext interpretieren für „Gilt diese Regel für mich?"
- **Bewertung:** Für die Mehrheit der Regeln ausreichend. Für komplexe Regeln fehlt die Logik-Schicht.

### Alternative 2: Entscheidungslogik direkt in OSCAL4Rail modellieren

- (+) Alles in einem Format
- (-) NIST OSCAL Catalog hat kein Logik-Modell (erfordert Custom-Extensions)
- (-) Breaking Change zum OSCAL-Standard
- (-) Vermischung von Daten und Logik (verletzt IOSP-Prinzip)
- **Verworfen:** Widerspricht der OSCAL-Philosophie und dem Prinzip der Verantwortungstrennung.

### Alternative 3: DMN (Decision Model and Notation, OMG/ISO 19510)

- (+) Offener Standard, etabliertes Tooling (Camunda, Drools)
- (+) Formale Entscheidungstabellen mit Datentypen
- (-) Komplex, schwergewichtig
- (-) Kein Bezug zu Law-as-Code/SPRIND-Ökosystem
- **Vorgemerkt als Fallback** falls Rulemapping-Format dauerhaft proprietär bleibt.

### Alternative 4: Catala (funktionale Rechtssprache, INRIA)

- (+) Open Source, akademisch fundiert, formale Semantik
- (-) Programmiersprache → Juristen/Fachexperten können nicht damit arbeiten
- (-) Andere Zielgruppe, kein SPRIND-Bezug
- **Vorgemerkt als technische Alternative** für Zukunft.

---

## Validierung

Pilot-Test durchgeführt am 2026-06-25:
- BS-KI 2.1 „Aktuelle Uhrzeit" als Rulemap modelliert (komplexer Fall mit Schwellenwert)
- Import/Export im Builder erfolgreich
- Boolesche Logik (OR/AND) + Negation (`invertlogic`) funktional
- Ergebnisse dokumentiert in `docs/experiments/rulemapping/`

---

## Links

- [ADR-005: Relationship to Law-as-Code Initiatives](ADR-005-law-as-code-relationship.md)
- [Experiment: Rulemapping Builder Pilot](../experiments/rulemapping-pilot.md)
- [Experiment: Export-Analyse](../experiments/rulemapping/README.md)
- [SPRIND Law-as-Code](https://sprind.org/en/actions/strategic-projects/law-as-code)
- [Rulemapping Builder](https://builder.rulemapping.org)
- [NIST OSCAL](https://pages.nist.gov/OSCAL/)
