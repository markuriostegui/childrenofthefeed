---
source_id: carlini-extracting-training-data-2020
vector_ids: ["04_data_to_models_copyright_weights"]
chapter_ids: ["04"]
source_tier: T1
source_type: paper
url: https://arxiv.org/abs/2012.07805
published_at: 2020-12-14
captured_at: 2026-07-02T17:47:20Z
status: complete
stance: factual
risk_level: review
---

# Extracting Training Data from Large Language Models

## Factual Summary

- This foundational paper demonstrates a training-data extraction attack against GPT-2, a language model trained on scraped public internet data.
- The authors show that it is possible to recover hundreds of verbatim training sequences from the model, including personal information, code, and other unique strings.
- They also report that larger models were more vulnerable than smaller ones in their extraction experiments.

## Key Quotes or Findings

- The abstract says GPT-2 was trained on “scrapes of the public Internet.”
- It says the researchers extracted hundreds of verbatim text sequences from the model's training data.
- The extracted examples included names, phone numbers, email addresses, code, IRC conversations, and UUIDs.
- The authors say larger models were more vulnerable than smaller models.

## What It Proves

- That large language models can sometimes reproduce identifiable verbatim material from their training data rather than only abstract statistical patterns.
- That Chapter 4 can connect training-data appropriation to memorization and leakage with direct technical evidence.
- That the notion of model weights as a harmlessly abstract transformation of source material is too simple for the full technical record.

## What It Suggests

- Review causal relationships carefully before elevating them into a thesis.
- That compressed model representations can still retain recoverable traces of training examples.
- That legal debates about training cannot be severed cleanly from technical debates about memorization and extraction.

## What It Does Not Prove

- It does not prove that all or most outputs from large language models are copies of training data.
- It does not prove that every frontier model leaks training data to the same degree.
- It does not by itself settle whether training is lawful under copyright doctrine.

## Reliability

- High reliability for documentary baseline questions because this is a `T1` paper. It is strongest on what it directly records and weaker on broader interpretation.
- Current note risk posture: `review`.

## Claims It Supports

- `carlini-extracting-training-data-2020-04-data-to-models-copyright-weights-claim-01`: That large language models can sometimes reproduce identifiable verbatim material from their training data rather than only abstract statistical patterns. (Documented Fact)
- `carlini-extracting-training-data-2020-04-data-to-models-copyright-weights-claim-02`: That Chapter 4 can connect training-data appropriation to memorization and leakage with direct technical evidence. (Documented Fact)
- `carlini-extracting-training-data-2020-04-data-to-models-copyright-weights-claim-03`: That the notion of model weights as a harmlessly abstract transformation of source material is too simple for the full technical record. (Documented Fact)

## Risk Label

- Low to medium. Strong technical evidence with high relevance to legal and political arguments, but it must not be overstated into universal copying claims.
