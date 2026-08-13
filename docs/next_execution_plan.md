# Next Execution Plan: Conclusion Hardening, Deduplication, and Draft Gate

This file is a historical planning snapshot, not the current operating manual.

For current onboarding, workflow, and republication rules, use:

- [start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md)
- [research_workflow.md](/Users/hassan/repos/AI-Empire/docs/research_workflow.md)
- [resume_and_republish_runbook.md](/Users/hassan/repos/AI-Empire/docs/resume_and_republish_runbook.md)

## Summary

Use the current English research OS as the baseline and spend the next implementation pass on the areas that are still structurally weaker in practice, not on more scaffolding.

The repo is now materially stronger than the previous plan snapshot suggested. Chapters `02` through `08` all have populated briefs, and the mid-dossier core is no longer the main bottleneck.

The next pass should still **not** begin continuous long-form prose.

The priority now is to:

- harden the conclusion layer in Chapters `09` and `10`,
- normalize shared evidence into those two vectors so they are not only manually synthesized,
- trim duplication in Chapters `06` through `08`, especially Chapter `08`,
- and define a clear draft-readiness gate for when the dossier can move from outline and briefs into prose.

## Plan Review: State Versus Prior Plan

## What the previous pass actually achieved

- Chapter briefs `05`, `06`, `07`, and `08` are fully populated and no longer contain placeholder text.
- Chapters `02`, `03`, and `04` are materially stronger than before and now have meaningful backbone source sets.
- Chapters `09` and `10` exist as real chapter briefs rather than `Pending.` shells.
- Vector `08_power_networks_legitimacy_capture` is no longer thin and now has a substantial evidence base.
- Vectors `05`, `12`, and `13` have enough backbone material to support later prose drafting.
- The repo remains English-first across notes, vector reports, chapter briefs, and the master dossier outline.

## Current source coverage from `sources/catalog.jsonl`

- `01_surveillance_capitalism`: `3`
- `02_social_decay_youth_harm_hypersexualization`: `7`
- `03_covid_acceleration_and_geopolitics`: `8`
- `04_data_to_models_copyright_weights`: `13`
- `05_talent_hoarding_section174_layoffs`: `10`
- `06_ai_double_use_reasoning_deepseek`: `5`
- `07_export_controls_compute_defense_access`: `10`
- `08_power_networks_legitimacy_capture`: `21`
- `09_future_if_unchecked`: `1`
- `10_counterstrategy_response_agenda`: `1`
- `11_facebook_thiel_intelligence_adjacency`: `5`
- `12_cambridge_analytica_meta_metaverse_rebrand`: `10`
- `13_openai_governance_qstar_talent_exodus`: `19`
- `14_named_individuals_disputes_and_risk`: `4`

## What is still weak or uneven

- Vector `09_future_if_unchecked` now includes `gpts-are-gpts-labor-impact-2023`, but the vector report still behaves like a light synthesis layer rather than a fully normalized evidence-backed vector.
- Vector `10_counterstrategy_response_agenda` still has no local note files and remains the thinnest chapter-support layer in the repo.
- Chapters `09` and `10` are readable, but they are still driven more by manual synthesis than by an evenly populated editorial pipeline.
- Chapter `08` is strong, but it is overfull and repetitive because it inherits too many near-duplicate claims from vectors `08`, `11`, `13`, and `14`.
- Chapters `06` and `07` are stronger than before, but they should be checked for governance-language duplication that now appears across multiple shared sources.
- `drafts/dossier_master.md` is still correctly functioning as a structural outline, not a publishable narrative draft.

## Current chapter-layer status

- Chapter `05`: solid enough to support later prose drafting.
- Chapter `06`: usable, but benefits from editorial compression.
- Chapter `07`: usable, but should be checked for overlap with Chapter `08`.
- Chapter `08`: evidentially strong but needs trimming and sharper hierarchy.
- Chapter `09`: conceptually clear, but still under-normalized.
- Chapter `10`: directionally strong, but still the least grounded in dedicated vector-level notes.

## Next-Pass Objective

Move the dossier from “brief-complete” to “draft-gated.”

That means the next pass should ensure that the final conclusion chapters are supported by enough normalized evidence, while the late middle chapters are compressed into tighter, more defensible editorial forms.

## Implementation Priorities

## 1. Harden the conclusion vectors first

Focus on:

- `09_future_if_unchecked`
- `10_counterstrategy_response_agenda`

These are now the main structural bottlenecks before long-form drafting.

## Vector 09: Future if no action is taken

Add exactly `3` new sources beyond the already-added `gpts-are-gpts-labor-impact-2023`:

- `1` `T1` or `T2` source on education, cognition, or learning effects under AI-assisted or screen-mediated dependency.
- `1` `T1` or `T2` source on labor-market stratification, inequality, or exposure asymmetry beyond the initial GPTs paper.
- `1` `T1` or `T2` source on access stratification, compute concentration, or unequal availability of high-end AI capability.

Target output:

- convert Chapter `09` from pure continuity synthesis into a projection chapter anchored by explicit evidence bridges on cognition, labor, and access hierarchy;
- preserve all future-facing language as projection, not disguised fact.

## Vector 10: Counterstrategy and response agenda

Add exactly `4` new sources:

- `1` `T1` or `T2` source on labor bargaining, worker consultation, or deployment governance.
- `1` `T1` or `T2` source on competition, interoperability, antitrust, or structural remedies relevant to concentration.
- `1` `T1` or `T2` source on public-interest AI infrastructure, public compute, or open/public alternatives.
- `1` `T1` or `T2` source on digital hygiene, cognitive literacy, or youth-facing defensive guidance with institutional credibility.

Target output:

- make Chapter `10` feel like a grounded response agenda rather than an abstract manifesto;
- connect each response layer directly back to earlier dossier findings.

## 2. Normalize shared-source coverage into vectors `09` and `10`

Do not change schemas or add new CLI commands.

Use the existing workflow to ensure the conclusion vectors are not filesystem-thin:

- register all new sources in `sources/catalog.jsonl`,
- create note files using the standard English sections,
- add local raw artifacts where capture is expected,
- extract claims into `claims/master_claims.jsonl`,
- update entities and timeline entries where a source adds a dated turning point or actor,
- regenerate the vector reports and chapter briefs after normalization.

Special requirement for this pass:

- Vector `10_counterstrategy_response_agenda` should no longer be a vector with zero local note files.
- Shared sources that materially support both Chapters `09` and `10` should be reflected in both vectors through notes, claims, or both, using the current CLI and repo conventions rather than new interfaces.

## 3. Compress and deduplicate the late middle chapters

Do not add breadth to Chapters `06`, `07`, and `08` unless a source is strictly necessary.

Instead:

- trim repeated governance claims in Chapter `08`,
- reduce overlap between Chapters `07` and `08` where the same source currently performs both access-control and legitimacy work,
- tighten Chapter `06` so reasoning, safety rhetoric, subsidized access, and packaging-versus-capability are distinguishable strands rather than one long claim dump.

Target output:

- Chapter `06` becomes a cleaner rhetorical-weapon chapter.
- Chapter `07` stays focused on chokepoints, export controls, and access.
- Chapter `08` becomes a more selective structural synthesis rather than the repository’s largest claim container.

## 4. Preserve the high-threshold approach to named individuals

Vector `14_named_individuals_disputes_and_risk` should remain narrow.

Only add material if it is:

- a court record, filing, official record, or equivalent; or
- Reuters, AP, or an equivalent high-credibility source with direct structural relevance to Chapter `08`.

Do not expand this vector for color.

Use it only when a named dispute clarifies:

- governance control,
- institutional legitimacy,
- ownership or mission conflict,
- or a court-tested structural struggle.

## 5. Keep the current interface and data model

Use the existing CLI only:

- `add-source`
- `capture-web`
- `capture-browser`
- `ingest-pdf`
- `ingest-transcript`
- `summarize-source`
- `extract-claims`
- `build-index`
- `vector-report`
- `chapter-brief`

Do not add new commands.
Do not add new schema fields.
Keep English as the canonical working language for all new artifacts.

## Regeneration Targets After the Next Pass

After new evidence is added and normalized, regenerate:

- `sources/research_index.sqlite`
- `vectors/09_future_if_unchecked/summaries/vector-report.md`
- `vectors/10_counterstrategy_response_agenda/summaries/vector-report.md`
- `chapters/09_future-if-no-action-is-taken.md`
- `chapters/10_what-to-do.md`

Then refresh only the late middle chapters that need compression:

- `chapters/06_ai-as-a-dual-use-rhetorical-weapon.md`
- `chapters/07_imperial-control-over-access.md`
- `chapters/08_power-network-legitimacy-and-institutional-capture.md`

Regenerate other vectors or chapters only if the new conclusion-layer sources materially change their logic.

## Acceptance Criteria

The next pass is successful when:

- Vector `09` has more than a single dedicated source and includes normalized evidence on cognition, labor, and access hierarchy.
- Vector `10` has dedicated local notes and no longer reads as a mostly manual synthesis shell.
- Chapters `09` and `10` retain projection and normative language where appropriate, but are more clearly anchored to source-derived claims.
- Chapter `08` is shorter, less repetitive, and still structurally supported.
- Chapters `06` and `07` are cleaner and more distinct in argumentative function.
- No new artifacts reintroduce Spanish headings or placeholder text.
- `drafts/dossier_master.md` remains an outline, but the repo reaches a credible draft gate for deciding whether prose writing can start.

## Draft Gate After This Pass

After this pass, make an explicit go or no-go call on beginning continuous prose.

The dossier should move into prose only if:

- Chapters `05` through `10` each have stable briefs with no major evidence gaps,
- the conclusion chapters are supported by normalized evidence rather than only manual synthesis,
- late-stage duplication has been reduced,
- and the remaining gaps are depth gaps, not structural ones.

If those conditions are met, the next plan after this one should be the first controlled prose-writing pass.
