# Rule taxonomy for design-system-governed UI generation

This is the methodology contribution of GUIML-Bench. A design system is an
abstract idea that practitioners decompose into tokens, components, patterns,
and usage intent. The six classes below make that decomposition measurable.
Each class has a grader type so a single "compliance %" cannot hide where an
agent actually fails.

The taxonomy is the operationalization of the axiomatic-vs-exemplar claim:
classes R1, R2, and R5 are axiomatic (a name is either in the dictionary or it
is not); classes R3 and R6 require judgment about intent and spatial behavior;
R4 sits in between (WCAG rules are axiomatic, but applying them to a generated
tree is a runtime property).

## R1 Lexical / token

**Governs.** Visual values bind to design tokens. The *role* of the token is
correct (helper text uses `text-secondary` or `text-helper`, not `text-primary`
or a raw hex).

**Why it is a class.** Token dictionaries are the leaf of a design system. Hex
codes and arbitrary spacing (`13px`, `bg-[#0f62fe]`) are exemplar mimicry.

**Grader.** Deterministic AST / regex over generated TSX and CSS. Precision and
recall against the task's expected token set. Role accuracy on the expected set.

**Pass.** No raw color or arbitrary spacing; expected tokens present; used tokens
are in the presented pack.

## R2 Structural / API

**Governs.** Only catalog components; only documented props; required
composition (`Modal` contains header/body/footer; `Grid` contains `Column`).

**Why it is a class.** The component API is the system's public contract. Invented
props (`variant="ghost"` on `Tag`) compile-fail or silently no-op.

**Grader.** Import set ⊆ catalog; prop names ⊆ known props; composition overlay
from `carbon/composition.json`; `tsc --noEmit` as a hard gate.

**Pass.** Compiles. No hallucinated component. Required children present.

## R3 Semantic / usage

**Governs.** The *right* component and variant for the intent. Danger only for
irreversible destruction. Exactly one primary action per view. Status is a `Tag`.
Non-blocking feedback is a notification, not a modal.

**Why it is a class.** These rules are what make a UI *feel* like it belongs to
the system, and they cannot be caught by `tsc` or a hex regex. They are the
exemplar-vs-axiomatic gap Cha & Jo's component-level checklist does not isolate.

**Grader.** Binary checkpoints judged by an LLM that is not the generator,
human-validated on a 20% sample with Cohen's κ. Checkpoints with κ < 0.6 are
dropped or flagged.

**Pass.** All critical checkpoints pass; overall checkpoint pass rate reported.

## R4 Accessibility

**Governs.** WCAG 2.1 AA on the rendered DOM at 1440px and 375px.

**Why it is a class.** Accessibility is a first-class design-system rule, not a
post-hoc audit. A11yn showed prompting is insufficient; we treat it as a
measurable class rather than a training objective.

**Grader.** Playwright + axe-core. Severity-weighted violation score
(critical 4, serious 3, moderate 2, minor 1). Inaccessibility rate = any
serious/critical.

**Pass.** No critical/serious violations. Icon-only controls have accessible names.

## R5 Lifecycle

**Governs.** Deprecated, renamed, and split names from a previous major version
are not used. If a v10 name appears, the v11 target is used instead.

**Why it is a class.** Design systems evolve. Models have seen years of the old
version in pretraining. Carbon's `docs/migration/v11.md` is public ground truth
(Updated / Split / New / Deprecated). No published benchmark tests this.

**Grader.** Deterministic lookup against `lifecycle.json`. Trap tasks inject v10
names into the prompt.

**Pass.** Zero forbidden v10 names. Rename-correctness on trap tasks.

## R6 Layout / responsive

**Governs.** Carbon 2x grid usage; no overlapping boxes or horizontal overflow at
the 375px breakpoint.

**Why it is a class.** FigmaBench's fidelity–responsiveness paradox: models that
match a screenshot often emit rigid absolute layout. Enterprise systems require
fluid grid behavior.

**Grader.** Presence of `Grid`/`Column` (or equivalent pack layout primitive);
Playwright bounding-box overlap count and overflow flag at 375px.

**Pass.** Grid used. Overlap count 0. No horizontal overflow.

## Why these six, and not more

Tokens, components, patterns, and intent are the four layers of a design system
as practitioners describe them. R1 and R2 cover the first two layers as
contracts. R3 covers intent. R6 covers the spatial pattern layer. R4 and R5 are
cross-cutting constraints (accessibility is a quality of the whole tree;
lifecycle is a temporal property of every name). Adding "visual fidelity" as a
seventh class would collapse back into Design2Code; we deliberately do not score
pixel similarity as a governance metric.

## Mapping to existing evals

| Class | open-design-system-bench | Cha & Jo checklist | A11yn |
| --- | --- | --- | --- |
| R1 | tokenDiscipline (hex only, no role) | color codes | — |
| R2 | apiFidelity + compile | — | — |
| R3 | judgment rubrics (mixed) | state behavior (mixed) | — |
| R4 | a11yStatic (AST only) | — | WVS / IR |
| R5 | static "deprecation legibility" of docs | — | — |
| R6 | — | — | — |
