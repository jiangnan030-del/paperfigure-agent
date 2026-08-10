# Contributing

## Required provenance gate

Every pull request that adds a rule, profile, example, benchmark, image, dataset, or substantial algorithm must include:

1. the origin and stable URL/DOI;
2. the license or permission status;
3. whether any code, text, data, or pixels were copied;
4. what was independently reimplemented;
5. tests or evidence that the contribution does not distort scientific meaning.

If the license is unknown, the material may be cited as conceptual prior art but must not be copied or redistributed.

## Clean-room declaration

Contributors working on an independently reimplemented component must avoid consulting unlicensed source code while implementing it. Record design inputs in `THIRD_PARTY.yml` and architecture decisions under `docs/decisions/`.

## Scientific integrity

Do not:

- fabricate or alter data to improve a visual result;
- suppress inconvenient observations without explicit, reviewable transforms;
- imitate a published figure so closely that authorship or origin could be confused;
- remove attribution, watermarks, copyright notices, or provenance;
- present automated QA as peer review or statistical validation.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```
