# Contributor Manual

## Goal

This repo is designed so outside contributors can extend the research without weakening the evidence standards. A valid contribution is not "interesting information." A valid contribution is one bounded, traceable improvement to the source-to-claim-to-argument system.

This manual is optimized for one safe contribution bundle at a time.

## The Smallest Valid Contribution Bundle

At minimum, one bounded contribution should include:

- one correctly tiered source record
- one complete note
- at least one correctly labeled claim
- vector-level integration
- exact-date discipline for sensitive matters

If the source introduces a meaningful actor or dated turning point, it should also include:

- one entity update
- one timeline update

## Step 1. Choose the Right Vector

Before adding anything, identify the vector and chapter burden.

- platform extraction or surveillance design -> `01`
- social harm, youth harm, moral reconfiguration -> `02`
- training data, copyright, weights, enclosure -> `04`
- labor, valuation, Section 174, layoffs -> `05`
- rhetorical weaponization, subsidy logic, reasoning politics -> `06`
- access control, export controls, compute, defense ties -> `07`
- legitimacy, governance, lobbying, institutional capture -> `08`

If the material is mostly colorful, personality-centered, or evidentially thin, it probably belongs in `queue.md`, not in the main corpus.

## Step 2. Add One Source

For one accepted source, do all of the following:

- capture or ingest the artifact if needed
- add the source record to `sources/catalog.jsonl`
- place the note in the vector's `notes/` directory
- classify the source tier correctly
- record exact date and exact URL

## Step 3. Write One Note

Every note must explain:

- what happened
- what the source directly proves
- what it only suggests
- what it does not prove
- how reliable it is
- which claims it supports

Required sections:

- `Factual Summary`
- `Key Quotes or Findings`
- `What It Proves`
- `What It Suggests`
- `What It Does Not Prove`
- `Reliability`
- `Claims It Supports`
- `Risk Label`

If you cannot write the "What It Does Not Prove" section honestly, the source is not ready to support the dossier.

## Step 4. Register Claims

Add claims only for statements directly supported by the note.

Allowed labels:

- `Documented Fact`
- `Disputed Fact`
- `Hypothesis / Interpretation`
- `Speculative Narrative Risk`

Do not use `Hypothesis / Interpretation` to disguise weak sourcing. It is for bounded analysis built on stronger factual ground.

## Step 5. Update Entities and Timeline if Needed

Update entities only when the source adds a meaningful actor, institution, program, law, or corporate node.

Update the timeline only when the source marks:

- a dated turning point
- a procedural milestone
- a policy change
- a material corporate or institutional event

## Step 6. Update Vector Synthesis

If the source materially changes a vector, update the vector synthesis before touching prose.

Typical updates:

- `claims/index.md`
- `timeline/index.md`
- `summaries/vector-report.md`
- `chapter_bridge.md`

## Step 7. Update Downstream Prose Only After the Above Is Stable

Only after the source, note, claim, entity, timeline, and vector layers are correct should you touch:

- `chapters/`
- `papers/`
- `volumes/` if the task explicitly includes omnibus or companion refresh
- `book/` if the public-literary edition should reflect the same structural change

Do not start in polished prose and reverse-engineer support later.

## Downstream Impact Rules

When deciding what else must change:

- if only the evidence layer changed, stop at vector synthesis
- if a chapter argument changed, update `chapters/`
- if standalone readers would now see stale citations or stale framing, update `papers/`
- if corpus totals, public audit explanations, or shared volume framing changed, update `volumes/`
- if a research change should reach the public-facing magazine/book edition, update `book/`

If you are unsure whether a publication rebuild is needed, flag it for the maintainer rather than guessing.

## Literary Contribution Bundle

If your contribution touches the public-literary edition, the smallest safe bundle is:

- the relevant `book/chapters/*.md` change
- any new or revised prompt in `book/assets/prompts/`
- the generated asset itself, if one was added or replaced
- the matching `book/assets/asset_manifest.json` entry

Do not add a new literary visual without documenting the prompt source and manifest entry.

## Do Not Do This

- Do not use conspiratorial media, anonymous accounts, or neighborhood blogs as factual backbone.
- Do not turn elite overlap into proof of hidden command.
- Do not use named-individual scandal to carry a structural argument.
- Do not add uncited sensitive claims to chapters, papers, or volumes.
- Do not collapse `Documented Fact` and `Hypothesis / Interpretation`.
- Do not cite a paper-form argument to prove the corpus; the corpus proves the paper, not the reverse.
- Do not add a source just because it confirms the thesis emotionally.
- Do not update generated files under `build/` directly.

## Safe Defaults

- prefer one strong `T1` source over several weak summaries
- prefer two independent `T2` sources over one rhetorical commentary piece
- if in doubt about a candidate source, keep it in `queue.md`
- if a topic is morally explosive but evidentially thin, label the boundary instead of stretching the claim
- if the contribution does not clearly strengthen one of the three reforms, keep it out of the main narrative until the case is stronger

## Final Check Before Submission

- source exists in catalog
- note has all required sections
- claims are registered
- entity and timeline were updated if warranted
- vector synthesis still reads coherently
- any touched chapter or paper remains aligned to the three reforms
- no public-facing reference points to a raw repo path as reader evidence
- you can explain in one sentence why this contribution matters structurally
