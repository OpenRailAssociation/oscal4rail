# Rulemapping Builder – Export-Analyse

> **Datum:** 2026-06-25
> **Tool:** [builder.rulemapping.org](https://builder.rulemapping.org)
> **Testfall:** BS-KI 2.1 – Aktuelle Uhrzeit

---

## Dateien in diesem Verzeichnis

| Datei | Beschreibung |
|-------|-------------|
| `export_01_basic_virtual.xml` | Grundstruktur, alle Knoten `logic="virtual"` |
| `export_02_logic_or_and.xml` | Logik-Operatoren gesetzt: `or` und `and` |
| `export_03_invertlogic.xml` | Knoten auf „rot/inaktiv" gesetzt → `invertlogic="yes"` |
| `BS-KI_2.1_Aktuelle_Uhrzeit_import.xml` | Vollständige Rulemap zum Re-Import |

---

## Erkenntnisse aus den Exporten

### 1. XML-Grundstruktur

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rulemap title="..." application="query-action-ai">
  <node id="..." title="..." alttext="..." logic="...">
    <!-- Kindknoten = Verzweigungen -->
  </node>
</rulemap>
```

- **Wurzelelement:** `<rulemap>` mit `title` und `application`
- **Knoten:** `<node>` verschachtelt (Baum-Struktur)
- **Kein separates Kanten-Element** – die Beziehung ist implizit durch Verschachtelung

### 2. Attribute pro Knoten

| Attribut | Pflicht | Werte | Bedeutung |
|----------|---------|-------|-----------|
| `id` | ja | numerisch (auto-increment) | Eindeutiger Identifier |
| `title` | ja | Freitext | Knotenbeschriftung (Bedingung oder Ergebnis) |
| `alttext` | ja | Freitext (kann leer sein) | Zusatzinformation / Tooltip |
| `logic` | ja | `virtual`, `or`, `and`, `xor`, `nand`, `nor`, `n-xor` | Verknüpfung der Kindknoten |
| `invertlogic` | nein | `yes` (oder Attribut fehlt) | Negation der Logik |

### 3. Logik-Operatoren (gelernt aus Export 1 → 2)

Der `logic`-Wert bestimmt, wie die **Kindknoten** eines Knotens verknüpft werden:

| Operator | Semantik | Beispiel |
|----------|----------|---------|
| `virtual` | Unbestimmt / strukturell | Noch keine Logik zugewiesen |
| `or` | Mindestens ein Kind wahr | „Gilt WENN Bedingung A ODER B" |
| `and` | Alle Kinder wahr | „Gilt WENN Bedingung A UND B" |
| `xor` | Genau ein Kind wahr | „Entweder A oder B, nicht beides" |
| `nand` | Nicht alle gleichzeitig wahr | „Gilt NICHT wenn A und B beide zutreffen" |
| `nor` | Kein Kind wahr | „Gilt wenn weder A noch B" |
| `n-xor` | Genau N Kinder wahr | Erweiterte XOR-Variante |

### 4. Farblogik / invertlogic (gelernt aus Export 2 → 3)

| Farbe im Builder | XML-Repräsentation | Semantik |
|------------------|-------------------|----------|
| **Rot** (inaktiv) | `invertlogic="yes"` | Explizit negiert – „gilt NICHT" |
| **Grün** (aktiv) | kein extra Attribut | Abgeleitet im UI: übergeordnete Knoten eines roten Knotens werden automatisch grün |
| **Neutral/farblos** | kein extra Attribut | Noch nicht bewertet |

**Wichtig:** Grün ist **kein eigenes Attribut** im Export – es ist eine UI-Ableitung. Das XML kennt nur den Unterschied „negiert" vs. „nicht negiert".

### 5. Was das Format NICHT enthält

- **Keine Kanten-Labels** (ja/nein-Beschriftungen auf Pfeilen)
- **Keine Datentypen** (Schwellenwerte sind nur Text im `title`)
- **Keine Ergebnis-Typen** (verbindlich/empfohlen nur als Text)
- **Keine Quellreferenzen** (kein Link zu Paragraph/Dokument)
- **Keine semantischen IDs** (nur auto-increment Zahlen)
- **Keine Versionierung** im Format selbst

### 6. Bewertung für OSCAL4Rail-Integration

| Aspekt | Eignung | Kommentar |
|--------|---------|-----------|
| Maschinenlesbar | ✅ | XML + boolesche Logik = traversierbar |
| Entscheidungslogik abbildbar | ✅ | OR/AND/XOR reichen für Eisenbahn-Regulatorik |
| Schwellenwerte | ⚠️ | Nur als Freitext im `title`, nicht als Wert |
| Referenz zu Quellparagraph | ⚠️ | Nur über `alttext` möglich (Freitext) |
| Stabile IDs für Verknüpfung | ❌ | Numerisch, nicht semantisch |
| Integration in OSCAL4Rail | ✅ | Als `back-matter`-Ressource oder `link` referenzierbar |

---

## Fazit

Das Rulemap-XML-Format ist ein **leichtgewichtiger Entscheidungsbaum mit boolescher Logik**. Es ergänzt OSCAL4Rail's Applicability-Modell um die Frage „WANN gilt eine Regel?", während OSCAL4Rail die Frage „WAS gilt?" beantwortet.

**Mögliches Integrationsmuster:**

```yaml
# In OSCAL4Rail Catalog
controls:
  - id: bs-ki-2.1
    title: "Aktuelle Uhrzeit"
    links:
      - href: "rulemaps/bs-ki-2.1.xml"
        rel: "decision-logic"
        text: "Entscheidungsbaum für Anwendbarkeit"
```
