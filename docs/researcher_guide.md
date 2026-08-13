# Researcher Guide

This guide is for outside researchers, journalists, policy readers, and collaborators who want to use the package professionally without needing to understand the repo's internal maintenance habits first.

## What the Project Is Trying To Do

The project assembles an evidence-based argument about how surveillance capitalism matured into a broader regime of AI enclosure, labor displacement, access control, and institutional capture.

It is investigative first, but it is not neutral about its destination. The work accumulates toward three reforms:

- `Refactor Section 230`
- `AI Weights as Patrimony of Humanity`
- `Limit Government Capture by AI Companies`

## How To Read the Package

There are four reader-facing outputs.

### 1. Standalone Papers

Use the standalone papers when you want one chapter-sized argument that can be read in isolation.

Each paper is intended to stand on its own. It should explain:

- the question
- the thesis
- the evidence standard
- the relevant factual basis
- the interpretive limits
- the reform relevance

### 2. Omnibus Dossier

Use the omnibus when you want the full long-form argument as a continuous volume.

This is the best format if you want to follow the cumulative logic from:

- platform extraction
- social erosion
- pandemic acceleration
- data-to-model enclosure
- labor and financial restructuring
- strategic access control
- legitimacy and capture
- final reform synthesis

### 3. Corpus Companion

Use the companion when you want to audit the underlying system directly.

The companion is where you should go to inspect:

- source registers
- claim registers
- entity registers
- event registers
- note registers
- crosswalks between chapters and corpus components

### 4. Literary Edition

Use the literary edition when you want the public-facing narrative version of the project.

It is designed for a broader audience:

- lighter notes
- stronger visuals
- chapter-by-chapter navigation
- direct bridges back to the chapter papers for documentary support

The literary edition also has its own documented visual program. Public covers, narrative illustrations, and infographics are generated and tracked through a prompt-and-manifest system so the visual layer can be inspected and maintained rather than treated as undocumented decoration.

## How Evidence Labels Work

The project uses four evidence states.

### `Documented Fact`

A statement directly supported by the cited source record.

### `Disputed Fact`

A statement whose status is contested in the relevant record and is marked as such.

### `Hypothesis / Interpretation`

A bounded reading drawn from documented facts. It is an argument, not a disguised fact claim.

### `Speculative Narrative Risk`

A warning that a tempting interpretation outruns the evidence. These boundaries exist to stop the project from drifting into unsupported narrative.

## How To Move From a Public Claim to Its Support

Use the package in this order:

1. read the claim in the body prose
2. inspect the note or footnote attached to that passage
3. open the bibliography entry if you want the external source directly
4. use the paper-local appendix if you want the paper-specific source, claim, event, or entity slice
5. use the corpus companion if the paper references a broader audit label such as `Source S-066` or `Claim C-212`

## How To Read Internal References

When a paper says:

- `See Appendix A3`

stay inside that paper.

When a paper says:

- `See Companion Source S-066`

go to the corpus companion and find that source entry in the Source Register.

The public-facing system is designed so you do not need repo-path literacy to follow the evidence.

## How To Cite the Project Responsibly

If you are citing a public argument from one paper:

- cite the paper itself
- cite the external sources that are materially central to the claim when appropriate
- distinguish clearly between the paper's documented claims and its interpretations

If you are auditing the project's evidence structure:

- cite the corpus companion for registry-level material
- use the public audit labels when relevant
- avoid treating interpretive passages as if they were official factual determinations

## Limits You Should Keep in Mind

This project is designed to be forceful without becoming conspiratorial.

That means:

- not every adjacency is treated as proof
- not every disputed personal allegation enters the main argument
- not every structural interpretation is presented as settled fact
- the reform agenda is normative and explicit, but it is downstream of the evidence layer

## Fastest Entry Point

If you want the shortest route into the package, open:

- [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html)

That index links to the standalone papers, the omnibus dossier, the corpus companion, and the literary edition.
