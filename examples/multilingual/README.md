<!--
SPDX-FileCopyrightText: 2026 DB Systel GmbH
SPDX-License-Identifier: Apache-2.0
-->

# Multilingual model: worked example

Synthetic, illustrative example for the multilingual model specified in
[`docs/reference/catalog-format.md` §8](../../docs/reference/catalog-format.md).
The regulation `example` is invented; all prose is placeholder filler, not a quoted
requirement and not a machine translation (Framework ≠ Content,
[ADR-007](../../docs/adr/ADR-007-tooling-foundation.md)).

## The governing invariant

Multiple language versions are the **same** requirement, expressed in different
languages, never an additional requirement. Identity lives in the stable,
chapter-based control ID, not in the text. The author decides which languages exist
(any [ISO 639](https://www.iso.org/iso-639-language-code) code), and the governance
owner verifies that each language version faithfully expresses the same rule
(Meaningful Human Control). The framework only provides the option and keeps the
sameness verifiable.

## Files

| File | Pattern | Shows |
|---|---|---|
| `example-de.yaml` | A: one file per language | German file; `language=de`; `links rel=alternate` to the French sibling |
| `example-fr.yaml` | A: one file per language | French file; **same** control ID `example-1.1`; back-link to German |
| `example-multilingual-parts.yaml` | B: one file, per-language parts | one control, one ID, one `statement` part per language tagged with a `language` prop |
| `example-de-to-fr.mapping.yaml` | edge case | NIST Control Mapping (`relationship: equivalent`) for the exception where a language version numbers chapters differently |

Both patterns are valid NIST OSCAL. A catalog picks one and applies it
consistently; the choice belongs to the owner.

## Verification (official OSCAL toolset)

Validated and round-tripped with [compliance-trestle](https://github.com/oscal-compass/compliance-trestle)
against the pinned NIST OSCAL 1.2.3 model:

```bash
. .venv/bin/activate
pip install compliance-trestle
python - <<'PY'
from trestle.oscal.catalog import Catalog
from trestle.oscal.mapping import MappingCollection
from pathlib import Path
import yaml, tempfile

def roundtrip(model, path, root):
    obj = model.model_validate(yaml.safe_load(open(path))[root])
    with tempfile.TemporaryDirectory() as d:
        for suffix in ('.json', '.yaml'):
            p = Path(d) / f'x{suffix}'
            obj.oscal_write(p)
            assert obj == model.oscal_read(p), f'lossy at {suffix}'
    return 'valid + lossless (yaml<->json)'

print(roundtrip(Catalog, 'example-de.yaml', 'catalog'))
print(roundtrip(Catalog, 'example-fr.yaml', 'catalog'))
print(roundtrip(Catalog, 'example-multilingual-parts.yaml', 'catalog'))
print(roundtrip(MappingCollection, 'example-de-to-fr.mapping.yaml', 'mapping-collection'))
PY
```

The language carrier is `prop[name="language"]`, which exists identically in the
XML, JSON, and YAML serializations, so it survives format conversion. YAML is the
leading format; YAML to JSON and back is lossless with the official toolset. XML
output, when needed, is produced from the JSON model with NIST’s own XML/JSON
converter.
