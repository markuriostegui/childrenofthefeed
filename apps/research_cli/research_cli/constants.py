from __future__ import annotations

ROOT_DIRS = [
    "vectors",
    "sources",
    "sources/raw",
    "sources/browser_jobs",
    "claims",
    "profiles",
    "timelines",
    "chapters",
    "papers",
    "papers/appendix",
    "volumes",
    "book",
    "book/chapters",
    "book/assets",
    "book/assets/generated",
    "book/assets/generated/covers",
    "book/assets/generated/illustrations",
    "book/assets/charts",
    "book/assets/prompts",
    "book/style",
    "drafts",
    "apps",
    "apps/templates",
    "apps/browser_worker",
    "schemas",
    "docs",
    ".github",
    ".github/workflows",
]

GLOBAL_FILES = [
    "sources/catalog.jsonl",
    "claims/master_claims.jsonl",
    "profiles/entities.jsonl",
    "timelines/master_timeline.jsonl",
]

DOC_FILES = {
    "docs/source_policy.md": """# Source Policy\n\n## Hierarchy\n\n- `T1`: official documents, courts, laws, filings, papers, regulatory reports.\n- `T2`: Reuters, AP, FT, NYT, WSJ, Bloomberg, Nature, Brookings, CFR, CSIS.\n- `T3`: interviews, podcasts, and YouTube transcripts only when they function as primary sources and are corroborated.\n\n## Exclusions\n\nThe following will not be used as factual support:\n\n- conspiratorial media\n- neighborhood blogs\n- anonymous accounts\n- untraceable aggregators\n\n## Editorial Rule\n\nEvery sensitive claim must be frozen with an exact date, exact URL, and evidence level.\n\nState-company interaction claims require extra discipline: use exact dates, exact source boundaries, and formal records or high-credibility reporting for lobbying, procurement, subsidies, regulatory participation, defense ties, and public-benefit restructuring.\n""",
    "docs/editorial_labels.md": """# Editorial Labels\n\n## Documented Fact\n\nA claim supported by at least one `T1` source or two independent `T2` sources.\n\n## Disputed Fact\n\nA relevant claim with documented dispute among actors, experts, institutions, or serious coverage.\n\n## Hypothesis / Interpretation\n\nA political reading or plausible connection that does not meet the threshold to be treated as an established fact.\n\n## Speculative Narrative Risk\n\nA rhetorically tempting claim that outruns the verified record, especially when it compresses causality, attributes hidden intent without strong proof, or converts structural adjacency into a totalizing control story.\n""",
    "docs/legal_risk_rules.md": """# Legal and Reputational Risk Rules\n\n- Do not assert direct CIA-Facebook investment without stronger proof than an adjacency network.\n- Treat personal allegations against Sam Altman as disputed allegations with procedural context and denial.\n- Treat the Suchir Balaji case by separating the official ruling from the family dispute.\n- Do not build guilt by association.\n- When a sensitive connection fails the evidence filter, rewrite it as a trend or hypothesis.\n- Freeze all state-company interaction claims to exact dates and exact sources, especially when they concern procurement, subsidies, lobbying, defense ties, or regulatory influence.\n- Do not imply hidden government command, coordinated conspiracy, or secret motive from elite overlap alone.\n""",
    "docs/research_workflow.md": """# Research Workflow\n\n1. Collect sources by vector.\n2. Normalize each source into a note.\n3. Extract claims and entities.\n4. Populate timelines.\n5. Synthesize by vector.\n6. Assemble chapter briefs.\n7. Seed or update `papers/` as the standalone publication layer.\n8. Generate `volumes/` for the omnibus dossier and the corpus companion.\n9. Export `papers/` and `volumes/` to LaTeX and PDF when needed.\n""",
}

SCHEMA_FILES = {
    "schemas/source_record.schema.json": """{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "title": "SourceRecord",\n  "type": "object",\n  "required": ["source_id", "title", "url", "source_tier", "source_type", "vector_ids"],\n  "properties": {\n    "source_id": {"type": "string"},\n    "title": {"type": "string"},\n    "author": {"type": ["string", "null"]},\n    "publisher": {"type": ["string", "null"]},\n    "published_at": {"type": ["string", "null"]},\n    "captured_at": {"type": ["string", "null"]},\n    "url": {"type": "string"},\n    "source_tier": {"enum": ["T1", "T2", "T3"]},\n    "source_type": {"type": "string"},\n    "vector_ids": {"type": "array", "items": {"type": "string"}},\n    "chapter_ids": {"type": "array", "items": {"type": "string"}},\n    "language": {"type": ["string", "null"]},\n    "reliability_notes": {"type": ["string", "null"]},\n    "local_paths": {"type": "array", "items": {"type": "string"}}\n  }\n}\n""",
    "schemas/claim_record.schema.json": """{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "title": "ClaimRecord",\n  "type": "object",\n  "required": ["claim_id", "claim_text", "evidence_level", "vector_id", "source_ids"],\n  "properties": {\n    "claim_id": {"type": "string"},\n    "claim_text": {"type": "string"},\n    "claim_type": {"type": "string"},\n    "evidence_level": {"type": "string"},\n    "vector_id": {"type": "string"},\n    "source_ids": {"type": "array", "items": {"type": "string"}},\n    "counterevidence_ids": {"type": "array", "items": {"type": "string"}},\n    "chapter_ids": {"type": "array", "items": {"type": "string"}},\n    "legal_risk": {"type": ["string", "null"]},\n    "editorial_note": {"type": ["string", "null"]}\n  }\n}\n""",
    "schemas/entity_record.schema.json": """{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "title": "EntityRecord",\n  "type": "object",\n  "required": ["entity_id", "name", "entity_type"],\n  "properties": {\n    "entity_id": {"type": "string"},\n    "name": {"type": "string"},\n    "entity_type": {"type": "string"},\n    "aliases": {"type": "array", "items": {"type": "string"}},\n    "relevance": {"type": ["string", "null"]},\n    "connected_vectors": {"type": "array", "items": {"type": "string"}},\n    "source_ids": {"type": "array", "items": {"type": "string"}},\n    "controversy_status": {"type": ["string", "null"]}\n  }\n}\n""",
    "schemas/timeline_event.schema.json": """{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "title": "TimelineEvent",\n  "type": "object",\n  "required": ["event_id", "date", "label", "vector_ids", "source_ids"],\n  "properties": {\n    "event_id": {"type": "string"},\n    "date": {"type": "string"},\n    "label": {"type": "string"},\n    "description": {"type": ["string", "null"]},\n    "vector_ids": {"type": "array", "items": {"type": "string"}},\n    "entity_ids": {"type": "array", "items": {"type": "string"}},\n    "source_ids": {"type": "array", "items": {"type": "string"}},\n    "chapter_ids": {"type": "array", "items": {"type": "string"}},\n    "confidence": {"type": ["string", "null"]}\n  }\n}\n""",
    "schemas/chapter_map.schema.json": """{\n  "$schema": "https://json-schema.org/draft/2020-12/schema",\n  "title": "ChapterMap",\n  "type": "object",\n  "required": ["chapters"],\n  "properties": {\n    "chapters": {\n      "type": "array",\n      "items": {\n        "type": "object",\n        "required": ["chapter_id", "title", "vector_ids"],\n        "properties": {\n          "chapter_id": {"type": "string"},\n          "title": {"type": "string"},\n          "vector_ids": {"type": "array", "items": {"type": "string"}},\n          "core_thesis": {"type": ["string", "null"]}\n        }\n      }\n    }\n  }\n}\n""",
}

VECTORS = [
    {
        "id": "01_surveillance_capitalism",
        "title": "Surveillance capitalism and data capture",
        "chapter_ids": ["01", "10"],
        "summary": "Social infrastructure turned into behavioral extraction, weakening passive-intermediary defenses and preparing the case for platform accountability.",
    },
    {
        "id": "02_social_decay_youth_harm_hypersexualization",
        "title": "Social harm, youth, and moral reconfiguration",
        "chapter_ids": ["02", "10"],
        "summary": "Attention, mental health, institutional trust, and hypersexualization as amplified effects supporting sovereign-scale accountability.",
    },
    {
        "id": "03_covid_acceleration_and_geopolitics",
        "title": "COVID as accelerator and geopolitical arena",
        "chapter_ids": ["03"],
        "summary": "Lockdowns, digital dependency, origin uncertainty, and geopolitical interpretation.",
    },
    {
        "id": "04_data_to_models_copyright_weights",
        "title": "From human data to models and weights",
        "chapter_ids": ["00", "04", "10"],
        "summary": "Capture of human labor, training data, copyright conflict, and enclosure of model weights as the basis for patrimony-oriented governance.",
    },
    {
        "id": "05_talent_hoarding_section174_layoffs",
        "title": "Talent hoarding, Section 174, and layoffs",
        "chapter_ids": ["05", "10"],
        "summary": "Overhiring, Section 174, margin pressure, and AI as a legitimizing narrative layered onto structural correction.",
    },
    {
        "id": "06_ai_double_use_reasoning_deepseek",
        "title": "Dual-use AI, reasoning, and DeepSeek",
        "chapter_ids": ["06", "10"],
        "summary": "Rhetorical danger, strategic cheapness, and reasoning as packaging or real progress.",
    },
    {
        "id": "07_export_controls_compute_defense_access",
        "title": "Export controls, compute, and defense",
        "chapter_ids": ["07", "08", "10"],
        "summary": "Compute chokepoints, access to frontier models, and state-corporate alignment.",
    },
    {
        "id": "08_power_networks_legitimacy_capture",
        "title": "Power networks, legitimacy, and institutional capture",
        "chapter_ids": ["08", "09", "10"],
        "summary": "Lobbying, governance, operational state interfaces, religion, and legitimization structures.",
    },
    {
        "id": "09_future_if_unchecked",
        "title": "Future if unchecked",
        "chapter_ids": ["09", "10"],
        "summary": "A continuity scenario of dependency, access hierarchy, and shrinking cognitive sovereignty.",
    },
    {
        "id": "10_counterstrategy_response_agenda",
        "title": "Response agenda and counterstrategy",
        "chapter_ids": ["10"],
        "summary": "Three reforms plus cognitive, labor, and public-infrastructure counterstrategy.",
    },
    {
        "id": "11_facebook_thiel_intelligence_adjacency",
        "title": "Facebook, Thiel, and intelligence adjacency",
        "chapter_ids": ["01", "07", "08"],
        "summary": "Cross-cutting vector on capital networks, surveillance, and the security apparatus.",
    },
    {
        "id": "12_cambridge_analytica_meta_metaverse_rebrand",
        "title": "Cambridge Analytica, Meta, and the metaverse diversion",
        "chapter_ids": ["01", "02", "03"],
        "summary": "Psychographic targeting, reputational laundering, and the failure of the metaverse.",
    },
    {
        "id": "13_openai_governance_qstar_talent_exodus",
        "title": "OpenAI, Q*, and technical exodus",
        "chapter_ids": ["06", "07", "08"],
        "summary": "Governance, capability anxiety, talent departures, and political-corporate alignment.",
    },
    {
        "id": "14_named_individuals_disputes_and_risk",
        "title": "Named individuals, disputes, and risk",
        "chapter_ids": ["08"],
        "summary": "Sensitive cases only when they have structural relevance and sufficient support.",
    },
]

CHAPTERS = [
    {
        "id": "00",
        "title": "Opening framework",
        "core_thesis": "Intellectual property over weights, extraction of human value, and technical empire culminate in a three-reform response.",
        "vector_ids": ["04_data_to_models_copyright_weights", "01_surveillance_capitalism", "05_talent_hoarding_section174_layoffs", "07_export_controls_compute_defense_access", "08_power_networks_legitimacy_capture", "10_counterstrategy_response_agenda"],
    },
    {
        "id": "01",
        "title": "Social networks as infrastructure for free data capture",
        "core_thesis": "Social platforms prepared the behavioral raw material of the AI empire.",
        "vector_ids": ["01_surveillance_capitalism", "11_facebook_thiel_intelligence_adjacency", "12_cambridge_analytica_meta_metaverse_rebrand"],
    },
    {
        "id": "02",
        "title": "Social erosion and moral reconfiguration",
        "core_thesis": "Algorithmic optimization degraded attention, trust, and the moral imagination.",
        "vector_ids": ["02_social_decay_youth_harm_hypersexualization", "12_cambridge_analytica_meta_metaverse_rebrand"],
    },
    {
        "id": "03",
        "title": "COVID as a historical accelerator",
        "core_thesis": "The health crisis consolidated digital dependency and concentrated algorithmic mediation.",
        "vector_ids": ["03_covid_acceleration_and_geopolitics", "12_cambridge_analytica_meta_metaverse_rebrand"],
    },
    {
        "id": "04",
        "title": "AI arrives when the human raw material already exists",
        "core_thesis": "Foundation models emerge after a decade of free capture of human labor.",
        "vector_ids": ["04_data_to_models_copyright_weights", "05_talent_hoarding_section174_layoffs", "06_ai_double_use_reasoning_deepseek"],
    },
    {
        "id": "05",
        "title": "Talent, overhiring, valuation, and layoffs",
        "core_thesis": "AI was used as the legitimizing story for a structural financial correction.",
        "vector_ids": ["05_talent_hoarding_section174_layoffs"],
    },
    {
        "id": "06",
        "title": "AI as a dual-use rhetorical weapon",
        "core_thesis": "What is dangerous and what is cheap coexist as part of the same strategy of power.",
        "vector_ids": ["06_ai_double_use_reasoning_deepseek", "13_openai_governance_qstar_talent_exodus"],
    },
    {
        "id": "07",
        "title": "Imperial control over access",
        "core_thesis": "Export controls, compute, and defense alliances define who gets access to frontier intelligence.",
        "vector_ids": ["07_export_controls_compute_defense_access", "11_facebook_thiel_intelligence_adjacency", "13_openai_governance_qstar_talent_exodus"],
    },
    {
        "id": "08",
        "title": "Power network, legitimacy, and institutional capture",
        "core_thesis": "Frontier firms operate inside networks of political, media, financial, security, and moral legitimacy.",
        "vector_ids": ["07_export_controls_compute_defense_access", "08_power_networks_legitimacy_capture", "11_facebook_thiel_intelligence_adjacency", "13_openai_governance_qstar_talent_exodus", "14_named_individuals_disputes_and_risk"],
    },
    {
        "id": "09",
        "title": "Future if no action is taken",
        "core_thesis": "Without intervention, AI deepens social dependency and stratifies access to cognition.",
        "vector_ids": ["09_future_if_unchecked"],
    },
    {
        "id": "10",
        "title": "What to do",
        "core_thesis": "The response program centers three reforms: Section 230 reform, patrimony-oriented governance of frontier weights, and anti-capture obligations for AI firms.",
        "vector_ids": ["01_surveillance_capitalism", "02_social_decay_youth_harm_hypersexualization", "04_data_to_models_copyright_weights", "05_talent_hoarding_section174_layoffs", "06_ai_double_use_reasoning_deepseek", "07_export_controls_compute_defense_access", "08_power_networks_legitimacy_capture", "09_future_if_unchecked", "10_counterstrategy_response_agenda"],
    },
]

TEMPLATES = {
    "apps/templates/vector_readme.md.tmpl": """# {title}\n\n## ID\n\n`{id}`\n\n## Target Chapters\n\n{chapter_list}\n\n## Working Thesis\n\n{summary}\n\n## Guiding Questions\n\n- What is firmly documented?\n- What is disputed?\n- Which connections should be treated as hypotheses?\n\n## Exclusions\n\n- Do not turn conjectures into facts.\n- Do not use excluded outlets as factual support.\n- Do not lose date and source traceability.\n\n## Key Disputes\n\n- State the most important unresolved evidentiary or interpretive conflict in this vector.\n- Mark where the record supports only a bounded political reading rather than a settled fact.\n- Record any overclaim boundary that must remain visible during drafting.\n""",
    "apps/templates/queue.md.tmpl": """# Queue\n\n## High Priority\n\n- Add backbone `T1` and `T2` sources.\n\n## Medium Priority\n\n- Corroborable primary interviews.\n\n## Low Priority\n\n- Non-central contextual material.\n""",
    "apps/templates/chapter_bridge.md.tmpl": """# Chapter Bridge\n\n## Vector\n\n`{id}`\n\n## Feeds Chapters\n\n{chapter_list}\n\n## Expected Claims\n\n- Structural claim: explain what this vector establishes at the strongest documentary level.\n- Historical-context claim: explain how this vector advances chronology, institutional uptake, or background sequence.\n- Limitation or counterargument claim: explain what this vector does not prove or where it must remain bounded.\n\n## Risks\n\n- Flag sensitive names and procedural-status issues.\n- Mark hypotheses before moving to continuous prose.\n- Keep overclaim boundaries visible when the vector touches conspiracy-adjacent material.\n""",
    "apps/templates/source_note.md.tmpl": """---\nsource_id: {source_id}\nvector_ids: {vector_ids}\nchapter_ids: {chapter_ids}\nsource_tier: {source_tier}\nsource_type: {source_type}\nurl: {url}\npublished_at: {published_at}\ncaptured_at: {captured_at}\nstatus: draft\nstance: review\nrisk_level: review\n---\n\n# {title}\n\n## Factual Summary\n\n- Summarize the source in 3-6 factual bullets with exact boundaries.\n\n## Key Quotes or Findings\n\n- Capture the most important findings, dates, numbers, or claims with precise attribution.\n\n## What It Proves\n\n- State only what the source directly supports at `Documented Fact` level.\n\n## What It Suggests\n\n- Record bounded implications or political readings that still require corroboration or synthesis.\n\n## What It Does Not Prove\n\n- Mark the limits, missing causality, and any tempting overclaims the source cannot carry.\n\n## Reliability\n\n- Note source tier, institutional position, and any reasons for caution.\n\n## Claims It Supports\n\n- List claim IDs or likely downstream chapter uses once extraction is complete.\n\n## Risk Label\n\n- Record legal, reputational, or editorial risk such as `low`, `review`, or `high`.\n""",
    "apps/templates/chapter_brief.md.tmpl": """# Chapter {id}: {title}\n\n## Core Thesis\n\n{core_thesis}\n\n## Connected Vectors\n\n{vector_list}\n\n## Usable Claims\n\n- Add only claims that are strong enough to survive later prose hardening.\n\n## Backbone Sources\n\n- Add the primary sources and the strongest supporting `T2` sources for this chapter.\n\n## Foreseeable Objections\n\n- Record the strongest good-faith challenge or evidentiary limit to the chapter's thesis.\n\n## Limits of the Evidence\n\n- Mark what remains disputed, interpretive, or provenance-limited before continuous drafting.\n""",
    "apps/templates/dossier_master.md.tmpl": """# Long Dossier: from surveillance capitalism to AI imperialism\n\n## Status\n\nMaster draft not yet written. This file will be populated once the critical vectors have corpus, claims, timelines, and chapter briefs.\n\n## Chapters\n\n{chapter_outline}\n""",
}
