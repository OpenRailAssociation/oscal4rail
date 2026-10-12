# OSCAL4Rail Use Case Scenarios

## Scenario 1: New passenger information system procurement

**Who:** IT architect at a railway company (SBB, DB, ÖBB)
**Situation:** Procuring a new departure board system. Need to specify which regulation requirements the system must meet.

**How OSCAL4Rail helps:**

```bash
# Generate a compliance specification document from the catalog
python3 tools/filter.py \
  --catalog catalogs/bs-ki/de/bs-ki-de.yaml \
  --channel haltestelle \
  --transport bahn \
  --obligation verbindlich \
  --format markdown > RFP-compliance-requirements.md
```

Result: A ready-to-use compliance requirements section for the RFP — every requirement verbatim from the regulation, with stable IDs that the vendor can reference in their offer.

---

## Scenario 2: Cross-border passenger information

**Who:** Cross-border project team (e.g. DB + SBB cooperation on Rhine Valley corridor)
**Situation:** Operating trains across the CH/DE border. Which regulations apply where?

**How OSCAL4Rail helps:**

```bash
# Compare two national catalogs
python3 tools/diff.py \
  catalogs/bs-ki/de/bs-ki-de.yaml \
  catalogs/ril-420/de/ril-420-de.yaml \
  --mode alignment
```

Result: Shows which rules exist in both (aligned), which differ (gap), and which are unique to one standard. Enables joint compliance planning.

---

## Scenario 3: Regulation update impact assessment

**Who:** Compliance manager at SBB
**Situation:** KKI publishes BS-KI v2.0. Which of our 47 stations and 12 vehicle types are affected?

**How OSCAL4Rail helps:**

```bash
# 1. Get semantic diff between versions
python3 tools/diff.py \
  catalogs/history/bs-ki-de_v1.0.yaml \
  catalogs/bs-ki/de/bs-ki-de.yaml

# Output:
# CHANGED: bs-ki-2.1 – threshold reduced 800 → 500 passengers
# CHANGED: bs-ki-2.5 – Seilbahn now verbindlich (was empfohlen)
# NEW: bs-ki-2.10 – new rule for on-demand services

# 2. Filter affected assets from your asset register
python3 tools/impact-analysis.py \
  --diff diff-v1.0-v2.0.yaml \
  --assets your-asset-register.yaml
```

Result: Targeted list of affected stations and vehicles — not "re-read the full 64-page document again."

---

## Scenario 4: AI agent for regulation queries

**Who:** Engineer implementing a passenger information system
**Situation:** "What exactly do I need to show on the exterior front of a bus?"

**How OSCAL4Rail helps:**

```
User: What must be displayed on the exterior front of a bus?

Agent (using OSCAL4Rail MCP tool):
→ filter_controls(channel="fahrzeug-aussen.front", transport="bus-tram-metro", obligation="verbindlich")
→ Returns: bs-ki-3.6-fahrt (Liniennummer), bs-ki-3.7-fahrt (Ziel)

Answer:
On the exterior front of a bus, the following are mandatory:
• Line number (bs-ki-3.6): «Die Liniennummer ist die gegenüber der Kundschaft angezeigte Identifikation einer Linie...»
• Destination (bs-ki-3.7): «Das Ziel einer Fahrt ist grundsätzlich die effektive letzte Haltestelle der Fahrt...»
```

---

## Scenario 5: Standards body publishing a new regulation

**Who:** KKI (Nationale Kommission Kundeninformation)
**Situation:** Publishing BS-KI v2.0. Instead of a PDF only, publish the machine-readable version simultaneously.

**How OSCAL4Rail helps:**

1. Author the regulation with chapter numbers (as always)
2. Run the extraction pipeline → generates `bs-ki-de_v2.0.yaml`
3. Submit a PR to the OSCAL4Rail repository
4. CI validates automatically
5. Tag: `bs-ki/v2.0`
6. All downstream systems receive a structured update notification

Result: "Regulation as code" — the machine-readable version is the primary artifact, the PDF is generated from it.

---

## Scenario 6: Vendor self-certification

**Who:** Passenger information system vendor
**Situation:** Needs to demonstrate BS-KI compliance to multiple railway operators.

**How OSCAL4Rail helps:**

Vendor creates a compliance evidence file (`compliance-evidence.yaml`) referencing specific control IDs and their implementation. This can be:
- Automatically validated against the catalog
- Compared across vendors using the same control IDs
- Re-used across SBB, DB, ÖBB (all using the same catalog)

One compliance artifact — valid for all operators using OSCAL4Rail.
