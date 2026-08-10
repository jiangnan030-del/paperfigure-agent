# Scientific semantics and data-fidelity contract

PaperFigure Agent treats plotting as a compilation step, not as permission to reinterpret evidence.

## Mark contracts

| Mark | Required semantics | Guardrail |
| --- | --- | --- |
| `bar` | one value per x/series coordinate | duplicate coordinates rejected; optional errors must be non-negative; zero baseline enforced when requested |
| `line` | one value per x/series coordinate | duplicate coordinates rejected; numeric x values sorted deterministically |
| `scatter` | numeric x and y | non-finite values rejected; optional marker-area normalization is disclosed in the audit |
| `heatmap` | one numeric value per x/y cell | duplicate cells rejected; missing cells remain visually missing rather than silently imputed |
| `box` / `violin` | repeated numeric observations per category | raw observations are required; the renderer does not synthesize samples |
| `interval` | estimate with lower and upper bounds | every row must satisfy `lower <= estimate <= upper` |

## Prohibited silent behavior

The runtime must not silently:

- overwrite duplicate coordinates;
- coerce non-numeric strings into zero;
- replace missing values with group means;
- clip negative error magnitudes;
- choose a statistical interval or significance test;
- add a zero or null reference line whose meaning was not declared;
- change data to make a claim look stronger.

## Interpretation boundary

A successful render means the declared data and FigureSpec passed implemented structural checks. It does not establish that:

- the scientific claim is true;
- the chosen statistical method is valid;
- a confidence interval has the intended coverage;
- the data collection process is unbiased;
- the figure satisfies every current venue requirement.

Those decisions remain with the authors and reviewers and must be documented in the manuscript or figure legend.
