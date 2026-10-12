# How-To: Integrate OSCAL4Rail into AI Agents and Skills

This guide shows how to use OSCAL4Rail catalogs in AI agents (Kiro, Claude, GPT-4, etc.) and custom skills to enable regulation-aware reasoning and compliance verification.

## Concept

An OSCAL4Rail catalog is a structured YAML file. AI agents can:
1. **Query** regulations: "Which rules apply to my use case?"
2. **Verify** implementations: "Does this system comply with the relevant rules?"
3. **Track changes**: "What changed in the latest version of BS-KI?"

## Option 1: Load catalog as context (simple)

For simple queries, load the YAML directly into the agent context:

```python
import yaml

with open("catalogs/bs-ki/de/bs-ki-de.yaml") as f:
    catalog = yaml.safe_load(f)

# Pass to LLM as context
context = yaml.dump(catalog, allow_unicode=True)
prompt = f"""
You are a railway compliance expert. Use the following OSCAL4Rail catalog to answer questions.

CATALOG:
{context}

QUESTION: Which rules apply for displaying the line number on the vehicle exterior?
"""
```

## Option 2: Targeted retrieval by control ID

When you know the relevant control:

```python
def get_control(catalog, control_id):
    for group in catalog['catalog'].get('groups', []):
        for control in group.get('controls', []):
            if control['id'] == control_id:
                return control
        for subgroup in group.get('groups', []):
            for control in subgroup.get('controls', []):
                if control['id'] == control_id:
                    return control
    return None

control = get_control(catalog, 'bs-ki-3.6-fahrt')
statement = next(p['prose'] for p in control['parts'] if p['name'] == 'statement')
```

## Option 3: Kiro Skill Integration

Create a Kiro skill that loads OSCAL4Rail catalogs as domain knowledge:

```markdown
# OSCAL4Rail Skill

## Loaded Catalogs
- BS-KI DE v1.0: `catalogs/bs-ki/de/bs-ki-de.yaml` (42 controls)

## Query Patterns

### Find applicable rules
"Which OSCAL4Rail rules apply to [channel] [transport-mode]?"
→ Filter controls where props[applicability][class] matches the channel.transport-mode

### Verify compliance
"Does [system description] comply with [control-id]?"
→ Read control statement, compare with system description

### Show changes
"What changed in BS-KI between v1.0 and v2.0?"
→ Run diff.py and present results
```

## Option 4: Agent tool for regulation lookup

Implement as an MCP tool or function:

```python
@tool
def lookup_regulation(control_id: str, language: str = "de") -> dict:
    """
    Look up an OSCAL4Rail control by ID.
    Returns verbatim rule text, applicability, and source reference.
    """
    catalog_path = f"catalogs/bs-ki/{language}/bs-ki-{language}.yaml"
    with open(catalog_path) as f:
        catalog = yaml.safe_load(f)
    
    control = get_control(catalog, control_id)
    if not control:
        return {"error": f"Control {control_id} not found"}
    
    statement = next(
        (p['prose'] for p in control['parts'] if p['name'] == 'statement'), None
    )
    applicability = [
        p for p in control.get('props', []) if p['name'] == 'applicability'
    ]
    source_chapter = next(
        (p['value'] for p in control.get('props', []) if p['name'] == 'source-chapter'), None
    )
    
    return {
        "id": control['id'],
        "title": control['title'],
        "statement": statement,
        "applicability": applicability,
        "source_chapter": source_chapter,
    }
```

## Option 5: Verify your IT system against a catalog

Given a system description (e.g. a passenger information display system), check compliance:

```python
def verify_system(system_description: str, catalog: dict, channel: str, transport: str) -> list:
    """
    Find all controls applicable to a channel/transport combination
    and check if the system description addresses them.
    """
    applicable_controls = []
    
    for group in walk_groups(catalog):
        for control in group.get('controls', []):
            props = control.get('props', [])
            match = any(
                p['name'] == 'applicability'
                and p['value'] == 'verbindlich'
                and p.get('class', '') == f"{channel}.{transport}"
                for p in props
            )
            if match:
                applicable_controls.append(control)
    
    # Pass applicable controls to LLM for compliance check
    results = []
    for control in applicable_controls:
        statement = next(p['prose'] for p in control['parts'] if p['name'] == 'statement')
        # LLM call: does system_description satisfy statement?
        compliant = llm_check(system_description, statement)
        results.append({
            "control_id": control['id'],
            "title": control['title'],
            "compliant": compliant,
            "rule": statement[:200] + "..."
        })
    
    return results
```

## Example: Compliance check for a station display system

```python
system = """
The station display system at Zurich HB shows:
- Current time (digital, synchronized via NTP)
- Station name on all platforms
- Departure board with line number, destination, and scheduled time
- Real-time delay information
"""

results = verify_system(
    system_description=system,
    catalog=catalog,
    channel="haltestelle",
    transport="bahn"
)

for r in results:
    status = "✅" if r['compliant'] else "❌"
    print(f"{status} {r['control_id']}: {r['title']}")
```

Output:
```
✅ bs-ki-2.1: Aktuelle Uhrzeit
✅ bs-ki-2.2: Name der Haltestelle
✅ bs-ki-3.4-uebersicht: Fahrplanzeit (Übersicht aller Fahrten)
✅ bs-ki-3.6-uebersicht: Liniennummer (Übersicht aller Fahrten)
❌ bs-ki-2.3: Beschriftung Haltekante (not mentioned in system description)
```
