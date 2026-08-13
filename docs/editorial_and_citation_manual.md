# Editorial and Citation Manual

## Purpose

This manual defines how the project should read in public and how evidence should appear across chapters, standalone papers, the omnibus dossier, and the corpus companion.

It replaces the older draft-era assumption that a thin paper plus a repo appendix was enough. The current publication system is richer and more reader-facing.

## Publication Layers

The project publishes in four coordinated reader-facing forms.

### `chapters/`

Purpose:

- canonical narrative corpus
- reference-corpus synthesis
- bridge between vectors and formal publication prose

Rules:

- readable prose, not full paper formatting
- strong factual paragraphs should remain visibly traceable
- source IDs may appear inline for corpus traceability
- interpretation must remain visibly bounded
- chapter transitions should preserve the cumulative reform arc

Recommended anchor format inside the chapter corpus:

```text
[Sources: source-id-1, source-id-2]
```

### `papers/`

Purpose:

- fully self-sufficient scholarly papers
- one standalone paper per chapter
- readable in isolation by a cold reader

Rules:

- each paper must defend itself without requiring repo knowledge
- use reader-friendly notes and bibliography, not raw internal notation as the main reading experience
- use clickable external links in notes and bibliography when the source is external
- use human-readable appendix labels for paper-local evidence apparatus
- cross-reference other papers only as reinforcement, never as dependency

### `volumes/`

Purpose:

- `dossier_omnibus.md`: continuous long-form volume joining the chapter argument
- `corpus_companion.md`: full audit volume exposing the project-wide research apparatus

Rules:

- omnibus should read as a coherent book-length dossier
- companion should function as the professional audit surface for researchers
- internal registries should be humanized before they become public-facing companion prose

### `book/`

Purpose:

- literary/public-consumption edition
- magazine-style rewrite for general readers
- chapter-by-chapter public adaptation aligned to the research program

Rules:

- lighter notes may point primarily to the corresponding chapter paper
- factual restraint must remain intact even when the prose becomes more literary
- images, charts, and chapter openers should feel intentional and on-brand
- disputed material still requires explicit restraint notes where relevant
- the literary layer may simplify apparatus, but it may not invent new support

Operational note:

- generated literary visuals should be backed by prompt documents in `book/assets/prompts/`
- every public-facing asset used in the book should be registered in `book/assets/asset_manifest.json`
- chapter image placement should be controlled in `book/chapters/*.md`, not by direct edits to exported HTML

## Standalone Paper Standard

Every paper should contain, at minimum:

1. Title
2. Abstract
3. Keywords
4. Research Question
5. Scope and Framing Note
6. Central Thesis
7. Evidence and Method Note
8. Introduction
9. Historical or Institutional Context
10. Main Analysis
11. Counterarguments
12. Limits of the Evidence
13. Reform Relevance
14. Conclusion
15. Notes
16. References
17. Embedded Appendix

Chapter `10` must additionally contain exactly three named reform sections:

- `Refactor Section 230`
- `AI Weights as Patrimony of Humanity`
- `Limit Government Capture by AI Companies`

## Omnibus and Companion Logic

### Omnibus

The omnibus should:

- preserve the chapter order and reform accumulation
- retain enough chapter-local support to stay legible as a continuous book
- use internal cross-references where useful
- avoid forcing the reader into repo navigation

### Companion

The companion should:

- expose the full source, claim, entity, event, and note surfaces
- provide human-readable public labels first
- preserve raw audit IDs as secondary metadata
- explain evidence labels, risk boundaries, and crosswalk logic

## Citation Model

### External Sources

In public outputs:

- notes should carry readable short-form citation information
- bibliography entries should include the real external URL
- PDFs and HTML should preserve clickable links

### Internal Evidence References

When referring to internal project support, use reader-facing references such as:

- `See Appendix A3`
- `See Appendix B2`
- `See Companion Source S-066`
- `See Companion Claim C-212`

Do not expose raw repo paths in public prose as if they were scholarly references.

### Raw Audit IDs

Raw IDs remain important, but they are audit metadata rather than the main reading surface.

Use them:

- in appendix metadata
- in companion registers
- in maintainer-facing traceability

Do not use them as the main public heading when a human-readable title is available.

## Appendix Model

### Paper-Local Appendices

Each paper should carry only the evidence apparatus needed to defend itself.

Typical paper appendix components:

- source register for that paper
- claim subset used in that paper
- timeline slice used in that paper
- relevant entity subset
- evidence-boundary note where necessary

### Global Audit Surfaces

The companion volume is the exhaustive researcher-facing audit surface.

The internal registry files under `papers/appendix/` remain useful as generation substrate and maintainer support, but they should not be the primary explanation surface for outside readers.

## How To Express Evidence Labels in Prose

### `Documented Fact`

- use normal assertive prose
- support it with notes and bibliography
- do not amplify certainty beyond the source boundary

### `Disputed Fact`

- mark the dispute status explicitly in the prose
- identify the source of the dispute when relevant
- do not pretend the matter is settled if it is not

### `Hypothesis / Interpretation`

- signal the interpretive turn clearly with phrases such as:
  - `Interpretation:`
  - `A bounded reading is...`
  - `The strongest structural reading is...`
- cite the factual basis that makes the interpretation plausible

### `Speculative Narrative Risk`

- use in boundary-setting passages, notes, or appendix warnings
- do not let it masquerade as normal assertive prose
- use it to explain where a seductive story outruns the record

## Self-Sufficiency Rule

Every standalone paper must independently establish:

- its question
- its thesis
- its evidence standard
- the factual basis it relies on
- the boundary between fact and interpretation
- its relevance to the reform agenda

Repetition is acceptable when it materially improves autonomy.

## Cross-Series Rule

Cross-reference is encouraged, but only as reinforcement.

Each paper may identify:

- which adjacent papers deepen the argument
- which earlier papers establish shared premises
- which later papers extend the implications

But no paper should require another paper for basic comprehension.

## Literary-Layer Rule

The literary edition is not a cosmetic reskin of the papers.

Each literary chapter should:

- establish its own atmosphere and pacing
- simplify the note burden by pointing back to the corresponding paper
- preserve the same core factual discipline as the paper layer
- remain visibly part of the same three-reform architecture

The literary reader should be able to move from:

- a public-facing chapter
- to the corresponding chapter paper
- to the omnibus or companion if deeper audit is needed

## Reform Alignment Rule

The publication system remains cumulative and directional:

- `01` and `02` support `Refactor Section 230`
- `04`, `05`, and `06` support `AI Weights as Patrimony of Humanity`
- `07` and `08` support `Limit Government Capture by AI Companies`
- `09` explains why the three reforms are necessary together
- `10` states the reforms directly

The public writing can be forceful, but it must remain evidentiary first and normative second.

## Style Boundaries

- be sharp, not sloppy
- expose power, not fantasy
- separate structural critique from hidden-intent storytelling
- keep the project publishable by maintaining legal and evidentiary restraint
- treat the patrimony-of-humanity position as advocated doctrine, not settled law
