# How-To: Verify Your IT Systems Against OSCAL4Rail Catalogs

This guide describes how to perform a structured compliance check of your IT systems against an OSCAL4Rail regulation catalog.

## What "verification" means in OSCAL4Rail

Verification answers the question: **Does our system implement all applicable regulations correctly?**

This is not a formal audit — it is a structured, repeatable self-assessment using machine-readable rules.

## Verification Levels

| Level | Method | Automation |
|-------|--------|-----------|
| L1 – Scope | Which rules apply to my system? | Automatic (filter by channel/transport-mode) |
| L2 – Coverage | Does my system address all applicable rules? | Semi-automatic (LLM + human review) |
| L3 – Correctness | Does my implementation match the rule text? | Human review with AI support |
| L4 – Change | What changed in the last regulation update? | Automatic (diff tool) |

## Step 1: Define your system scope

Answer these questions:

```yaml
# system-scope.yaml
system:
  name: "Zurich HB Departure Boards"
  operator: "SBB"
  channels:
    - haltestelle
    - daten.einlieferung
  transport_modes:
    - bahn
    - bus-tram-metro
  regulation_catalogs:
    - bs-ki-de.yaml
```

## Step 2: Filter applicable controls

```bash
python3 tools/filter.py \
  --catalog catalogs/bs-ki/de/bs-ki-de.yaml \
  --channel haltestelle \
  --transport bahn \
  --obligation verbindlich
```

Output: list of controls that are **mandatory** for your scope.

## Step 3: Self-assessment checklist

For each applicable control, the system generates a checklist:

```markdown
## Compliance Checklist – BS-KI haltestelle × bahn

### bs-ki-2.1 – Aktuelle Uhrzeit
**Rule:** «Bei Haltestellen mit weniger als 800 Ein- und Aussteigern pro Tag kann auf die
Angabe der Uhrzeit verzichtet werden. Die aktuelle Uhrzeit ist für die Kundschaft ein
zentrales Element zur Orientierung.»

- [ ] System displays current time at this station
- [ ] Exception applied if <800 daily passengers (document the threshold)

### bs-ki-2.2 – Name der Haltestelle
**Rule:** «Die Beschriftung der Haltestelle mit ihrem Namen (gemäss Abschnitt 6.4) ist das
Grundelement der räumlichen Orientierung.»

- [ ] Station name is displayed at station entrance
- [ ] Station name is visible from the vehicle
```

## Step 4: Track compliance status

Use a simple YAML evidence file:

```yaml
# compliance/zurich-hb-2026.yaml
assessment:
  system: "Zurich HB Departure Boards"
  date: "2026-06-24"
  catalog: "bs-ki-de v1.0"
  assessor: "jens.grote@deutschebahn.com"

controls:
  bs-ki-2.1:
    status: compliant
    evidence: "NTP-synchronized clock displayed on all main boards"
    assessed: "2026-06-24"
  bs-ki-2.2:
    status: compliant
    evidence: "Station name on all 12 platforms"
    assessed: "2026-06-24"
  bs-ki-2.3:
    status: non-compliant
    gap: "Platform numbering not consistent with regulation 3.10"
    remediation: "Update platform signs Q3 2026"
    assessed: "2026-06-24"
```

## Step 5: Re-assess after regulation update

When a new catalog version is released:

```bash
# 1. Get the diff
python3 tools/diff.py \
  catalogs/history/bs-ki-de_v1.0.yaml \
  catalogs/bs-ki/de/bs-ki-de.yaml \
  --output diff-v1.0-v2.0.yaml

# 2. Filter: which changed controls affect my system?
python3 tools/filter-diff.py \
  --diff diff-v1.0-v2.0.yaml \
  --scope system-scope.yaml

# Output:
# CHANGED: bs-ki-2.1 (threshold changed: 800 → 500 passengers)
# NEW: bs-ki-2.10 (new rule added in v2.0)
```

Only re-assess the controls that actually changed — not the full catalog.

## Integration with CI/CD

Add an OSCAL4Rail compliance gate to your deployment pipeline:

```yaml
# .github/workflows/compliance-check.yml
- name: Check OSCAL4Rail compliance
  run: |
    python3 tools/verify.py \
      --catalog catalogs/bs-ki/de/bs-ki-de.yaml \
      --evidence compliance/zurich-hb-2026.yaml \
      --fail-on non-compliant
```

This blocks deployment if any mandatory rule is marked `non-compliant` without a documented remediation date.
