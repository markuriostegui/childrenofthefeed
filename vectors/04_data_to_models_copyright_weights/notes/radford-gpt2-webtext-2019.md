---
source_id: radford-gpt2-webtext-2019
vector_ids: ["04_data_to_models_copyright_weights"]
chapter_ids: ["04"]
source_tier: T1
source_type: paper
url: https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf
published_at: 2019-02-14
captured_at: 2026-07-02T20:21:08Z
status: complete
stance: factual
risk_level: low
---

# Language Models are Unsupervised Multitask Learners

## Factual Summary

- This February 14, 2019 OpenAI paper gives Chapter 4 a direct primary-source bridge from social-platform behavior to large-model training data.
- The GPT-2 paper describes WebText as a new web scrape built from outbound links shared on Reddit that received at least 3 karma.
- That matters because it shows that model builders were not only harvesting an abstract web archive; they were also leveraging socially filtered traces of human attention and judgment as a data-selection mechanism.

## Key Quotes or Findings

- The paper says OpenAI created a new web scrape that emphasized document quality rather than using an existing corpus.
- It states that the team scraped outbound links from Reddit that had received at least 3 karma.
- The paper explains that this heuristic was intended to capture links users found interesting, educational, or funny.
- It reports that the resulting WebText dataset contained the text subset of 45 million links and, after cleaning, slightly over 8 million documents totaling 40 GB of text.

## What It Proves

- That a major OpenAI training corpus was explicitly built from socially filtered outbound links shared on Reddit.
- That Chapter 4 can make a direct bridge from social-platform activity to model-training inputs instead of speaking only in broad abstractions about "the internet."
- That training-data pipelines can incorporate unpaid human curation signals even when the final corpus is presented as a neutral technical dataset.

## What It Suggests

- That large-model development depended not only on scraped content, but also on the behavioral traces of platform users who collectively surfaced what counted as worth reading.
- That the line between passive web collection and active social filtration is thinner than many simplified training-data narratives imply.

## What It Does Not Prove

- It does not prove the use of private social-media data.
- It does not prove that all later frontier models used the same source design or selection pipeline.
- It does not, by itself, resolve the legal question of whether socially filtered public links can be repurposed without compensation or consent.

## Reliability

- High reliability for documentary baseline questions because this is a `T1` paper. It is strongest on what it directly records and weaker on broader interpretation.
- Current note risk posture: `low`.

## Claims It Supports

- `radford-gpt2-webtext-2019-04-data-to-models-copyright-weights-claim-01`: That a major OpenAI training corpus was explicitly built from socially filtered outbound links shared on Reddit. (Documented Fact)
- `radford-gpt2-webtext-2019-04-data-to-models-copyright-weights-claim-02`: That Chapter 4 can make a direct bridge from social-platform activity to model-training inputs instead of speaking only in broad abstractions about "the internet." (Documented Fact)
- `radford-gpt2-webtext-2019-04-data-to-models-copyright-weights-claim-03`: That training-data pipelines can incorporate unpaid human curation signals even when the final corpus is presented as a neutral technical dataset. (Documented Fact)

## Risk Label

- Low. Strong `T1` technical source with direct relevance to the dossier's argument about human attention, data capture, and model formation.
