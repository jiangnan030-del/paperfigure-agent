# Paper Figure Skill

Use the stable CLI rather than generating ad hoc plotting code.

1. Gather the scientific claim, local dataset, target venue, and required outputs.
2. Create or edit a declarative FigureSpec.
3. Run `paperfig validate`.
4. Run `paperfig render` in a bounded local environment.
5. Inspect `figure.audit.json`, the figure, and the underlying data.
6. Require human approval for statistical, semantic, or rights-sensitive choices.
7. Deliver the spec, data citation, vector/raster outputs, audit, and provenance together.

Never copy an unlicensed reference figure or claim that automated QA replaces scientific review.
