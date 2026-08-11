# Architecture

## MVP path

```text
FigureSpec -> local data loader -> venue profile -> renderer
           -> static/scientific audit -> artifacts + provenance
           -> deterministic reviewer pass -> review report
           -> structural fingerprint -> baseline comparison
```

The MVP deliberately has no arbitrary-code execution and no model dependency.

## Verification stages

The three checking stages answer different questions and deliberately do not
overlap:

| Stage | Input | Question |
| --- | --- | --- |
| `audit` | FigureSpec | Is this figure allowed to be made this way? |
| `review` | one run bundle | Is this bundle intact and readable? |
| `regress` | two renders | Did this figure change since last time? |

`audit` runs before and during a render. `review` runs after a render, against
the produced bundle, and is the only stage that reads exported artifacts back
in. `regress` is the only stage that compares across runs, which is why it
cannot rely on file digests: exported SVG carries a creation timestamp and is
never byte-identical between two renders of the same spec.

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
- Reviewer Mode reads a bundle; it never repairs or re-renders it.
- Baselines are reviewable JSON, so a rendering change is visible in code review.
- Statistical and semantic edits cannot be silently auto-applied.
