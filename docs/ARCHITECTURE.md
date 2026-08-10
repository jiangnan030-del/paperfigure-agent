# Architecture

## MVP path

```text
FigureSpec -> local data loader -> venue profile -> renderer
           -> static/scientific audit -> artifacts + provenance
```

The MVP deliberately has no arbitrary-code execution and no model dependency.

## Planned layers

1. **Prompt** — task templates and output protocol.
2. **Context** — claim, data profile, venue rules, prior audit, licensed references.
3. **Harness** — tools, sandbox, permissions, state, logs, budgets, recovery.
4. **Loop** — plan, execute, verify, minimally repair, stop.
5. **Graph** — typed nodes, fan-out, merge, checkpoint, and human gates.
6. **Evolver** — offline trace mining, benchmark replay, versioned promotion, rollback.

## Trust boundaries

- Data inputs are untrusted and remain local by default.
- A FigureSpec is declarative; it must not embed executable code.
- Renderers receive validated records, not arbitrary Python expressions.
- Rule-based checks precede model-based visual critique.
- Statistical and semantic edits cannot be silently auto-applied.
