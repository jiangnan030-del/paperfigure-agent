# Architecture

## Executable path

```text
FigureSpec -> local data loader -> venue profile -> renderer
           -> static/scientific audit -> artifacts + provenance
           -> deterministic reviewer pass -> review report
           -> structural fingerprint -> committed baseline comparison
           -> baseline/candidate bundle comparison
           -> explicit human gate -> deterministic submission package
```

The executable path has no arbitrary-code generation and no model dependency.

## Verification and delivery stages

| Stage | Input | Question |
| --- | --- | --- |
| `audit` | FigureSpec | Is this figure allowed to be made this way? |
| `review` | one run bundle | Is this bundle intact, accessible, and venue-aware? |
| `regress` | spec + committed baseline | Did this figure drift since the accepted rendering? |
| `compare` | two run bundles | Did the candidate improve without changing data or semantics? |
| `package` | accepted run bundle + human approval | Is the delivery complete and self-verifying? |

The stages deliberately do not substitute for one another. A manifest digest
checks one run; it cannot replace a cross-run baseline because SVG contains a
creation timestamp. A structural baseline detects drift; it cannot decide
whether the scientific claim is valid. Packaging therefore preserves an
explicit human approval gate even after every deterministic check passes.

## Planned agent layers

1. **Prompt** — task templates and output protocol.
2. **Context** — claim, data profile, venue rules, prior audit, licensed references.
3. **Harness** — tools, sandbox, permissions, state, logs, budgets, recovery.
4. **Loop** — plan, execute, verify, minimally repair, stop.
5. **Graph** — typed nodes, fan-out, merge, checkpoint, and human gates.
6. **Evolver** — offline trace mining, benchmark replay, versioned promotion, rollback.

These remain later product layers. Phase 2 completes the deterministic
verification substrate they must call rather than reimplement.

## Trust boundaries

- Data inputs are untrusted and remain local by default.
- A FigureSpec is declarative; it must not embed executable code.
- Renderers receive validated records, not arbitrary Python expressions.
- Rule-based checks precede model-based visual critique.
- Reviewer Mode reads a bundle; it never repairs or re-renders it.
- Baselines are reviewable JSON, so rendering changes remain visible in review.
- Comparison treats changed input data and semantic encodings as errors.
- Packaging rejects symlinks and altered artifacts and requires human approval.
- Statistical, semantic, licensing, and publication decisions cannot be silently applied.
