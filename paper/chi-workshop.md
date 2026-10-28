# From Exemplars to Axioms: A Rule Taxonomy for Design-System-Governed Generative UI

**Position paper for CHI 2026 workshop *What does Generative UI mean for HCI Practice?***
Daphne Cheng (Georgia Tech), Vijay K. Madisetti (Georgia Tech)

## What we are arguing

HCI has spent decades turning abstract design into systems: tokens, components, patterns, usage rules. Generative UI tools currently skip that decomposition. They treat a design system as a pile of examples and a markdown file. The result is interfaces that look right and are not the system.

This is Option 4 in the workshop framing: the engineering stack for genUI needs a design language that is more than code generation and more than a component registry. We propose that the missing object is a *rule taxonomy*, and that the missing measurement is compliance *per class*, not a single checklist percentage.

## The taxonomy

We decompose a design system into six rule classes, each with a grader:

| Class | Layer of the system | What fails today |
| --- | --- | --- |
| R1 Lexical | tokens | hex, arbitrary spacing, wrong token *role* |
| R2 Structural | component API | invented props, broken composition |
| R3 Semantic | usage intent | danger used decoratively; status as a button; modal for a toast |
| R4 Accessibility | cross-cutting | axe-core serious/critical at 375 and 1440 |
| R5 Lifecycle | evolution | v10 names from pretraining after a major rename |
| R6 Layout | pattern / grid | absolute positioning; overflow at 375 |

R1, R2, and R5 are axiomatic. R3 and R6 require judgment about intent and space. R4 is a runtime property of the whole tree. Collapsing them into "95% compliant" (Cha & Jo, CHI EA 2026, registry condition) is why the problem looks solved.

## What we are building, and why it is a workshop artifact

GUIML-Bench is an 80-task public benchmark on IBM Carbon v11, with hidden-ground-truth prompts, three system scales, and lifecycle traps taken from Carbon's own migration table. GUIML is a JSON graph in which every node is typed by rule class and status, retrieved by class, linted, and compiled. The point for HCI practice is not the compiler. It is that *designers already do this decomposition by hand*, and we are asking whether an agent can be given the same structure rather than a screenshot and a prayer.

This sits on the designer-facing side of the workshop's first dimension (genUI as design-time material), and it is a prerequisite for the end-user-facing side: if a model generates UI at run-time, the only way to keep brand, a11y, and lifecycle contracts is to evaluate them as rules, not vibes.

## What we want from the room

1. Is R3 (semantic/usage) the right place to keep a human in the loop, or can it be encoded more formally than we think?
2. Should a design system's "AI-readiness" be a property of its *docs* (open-design-system-bench's static audit) or of *agent behavior on a public task suite* (our position)?
3. What would it take for a second system (Material, a product-specific library) to be expressed in the same taxonomy without losing the designer's language?

Artifacts: `docs/taxonomy.md` in the companion repository; tasks and Carbon rule graph staged for Hugging Face.
