# Resume and Republish Runbook

This runbook is for a fresh conversation, a new maintainer, or any restart after a long pause. Its job is to let someone recover the state of the project quickly and continue safely.

## Goal

In under 15 minutes, you should be able to answer:

- what the project is trying to prove
- what is canonical
- what the current publication package contains
- whether the next task is intake, synthesis, revision, or republication
- what must be rebuilt after the update

## Restart Order

1. Read [start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md).
2. Read [project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md).
3. Inspect [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html).
4. Inspect [papers/appendix/README.md](/Users/hassan/repos/AI-Empire/papers/appendix/README.md) for current corpus totals.
5. Inspect [build/reviews/publication_qc.md](/Users/hassan/repos/AI-Empire/build/reviews/publication_qc.md).
6. Read [publication_completion_audit.md](/Users/hassan/repos/AI-Empire/docs/publication_completion_audit.md) to separate locally-proven status from live-deployment status.
7. Choose work mode: intake, synthesis, revision, or publication.
8. Perform one bounded update at the correct canonical layer.
9. Rebuild only the outputs affected by that change.
10. Rerun QA and leave a written trace for the next maintainer.

## How To Classify the Next Task

### Evidence Intake

Choose this when:

- a new source must be added
- a note is missing
- claims are incomplete
- a vector is evidentially thin

Start in:

- `vectors/`
- `sources/`
- `claims/`
- `profiles/`
- `timelines/`

### Analytical Synthesis

Choose this when:

- the source material exists but the vector argument is weak
- chapter bridges are stale
- claim boundaries are unclear

Start in:

- vector summaries
- vector claim indexes
- vector timelines
- `chapter_bridge.md`

### Narrative Revision

Choose this when:

- chapter prose is stale
- a standalone paper no longer reflects the chapter corpus
- the omnibus or companion language needs refresh

Start in:

- `chapters/`
- then `papers/`
- then `volumes/` if needed

### Publication Rebuild

Choose this when:

- source files are already correct
- only HTML, TeX, PDF, or QA outputs need regeneration

Start with the CLI commands, not with direct edits to `build/`.

## How To Decide Where a Change Belongs

- evidence record changed -> update `vectors/`, registries, and maybe `chapters/`
- argument changed -> update `chapters/`
- standalone reader experience changed -> update `papers/`
- omnibus or companion navigation, framing, or totals changed -> update `volumes/`
- literary/public experience changed -> update `book/`
- methodology or conventions changed -> update `docs/`

If the task is specifically about literary visuals, use this triage:

- prose-only literary revision -> `book/chapters/`
- prompt design or prompt correction -> `book/assets/prompts/`
- missing or replaced generated visual -> asset file plus `book/assets/asset_manifest.json`
- export or layout issue -> `apps/research_cli/` or templates, then rebuild

## Republication Sequence

Use this order after any meaningful update:

1. confirm the scope of the change
2. update notes, claims, entities, and timeline as needed
3. refresh vector synthesis
4. refresh affected chapter corpus files
5. refresh affected paper files
6. refresh omnibus or companion source files if counts, framing, or shared navigation changed
7. refresh `book/` if the public-literary edition changed
8. rebuild indexes and exports
9. rerun publication QA
10. record what changed

If literary visuals changed, also verify:

- the new asset exists under `book/assets/generated/`
- the prompt exists in `book/assets/prompts/`
- the asset is registered in `book/assets/asset_manifest.json`
- the relevant chapter markdown references the new file

## Commands

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-index --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli seed-papers --root /Users/hassan/repos/AI-Empire --overwrite
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-master-paper --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli export-papers --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli seed-book --root /Users/hassan/repos/AI-Empire --overwrite
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli export-book --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-site --root /Users/hassan/repos/AI-Empire
```

`build-site` is the single public-artifact assembly step. It rebuilds `build/site/` and republishes the story reader at `build/site/website/` automatically. The Pages copy reuses shared book imagery to keep the artifact smaller; the local `website/` output remains self-contained.

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

If that QA command fails because `pypdf` is missing in the local Python installation, rerun it with the bundled Codex runtime:

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
/Users/hassan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
-m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

## What To Verify Before You Stop

- the changed layer is canonical, not generated
- any touched source has a note
- any new claim has the right label
- any material change to the argument is reflected in the chapter corpus
- any material change to public-facing prose is reflected in the relevant paper or volume source
- exported outputs were rebuilt if publication-facing files changed
- QA was rerun if exports were rebuilt

## What To Leave for the Next Researcher

At the end of a pass, document:

- what you changed
- why it changed
- which layers were touched
- whether corpus totals changed
- whether publication artifacts were regenerated
- what remains queued, weak, or unresolved
