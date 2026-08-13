---
source_id: deepseek-v3-technical-report-2024
vector_ids: ["06_ai_double_use_reasoning_deepseek", "07_export_controls_compute_defense_access"]
chapter_ids: ["06", "07"]
source_tier: T1
source_type: paper
url: https://arxiv.org/abs/2412.19437
published_at: 2024-12-27
captured_at: 2026-07-02T15:45:03Z
status: complete
stance: factual
risk_level: medium
---

# DeepSeek-V3 Technical Report

## Factual Summary

- The DeepSeek-V3 preprint was first submitted to arXiv on December 27, 2024 and revised on February 18, 2025.
- The abstract describes a MoE model with 671B total parameters, 37B activated per token, trained on 14.8 trillion tokens and requiring 2.788 million H800 GPU hours.
- The source anchors the argument that advances in reasoning and performance do not belong exclusively to a handful of closed U.S. labs.

## Key Quotes or Findings

- arXiv dates the first version to December 27, 2024 and the revised version to February 18, 2025.
- The abstract states that DeepSeek-V3 outperforms other open-source models and reaches performance comparable to leading closed-source models.
- It highlights Multi-head Latent Attention, an auxiliary-loss-free strategy, and multi-token prediction.
- The abstract also states that the model checkpoints are available.

## What It Proves

- That by late 2024 there was already a competitor publicly claiming frontier-adjacent performance through a technical report.
- That the debate over reasoning, efficiency, and cost cannot be reduced to the marketing of a single Western actor.
- That narratives of absolute scarcity around advanced capabilities must be contrasted with open technical reports and partial replicability.

## What It Suggests

- That some of the value attributed to certain commercial packages may come from integration, distribution, and political capital as much as from pure algorithmic novelty.
- That strategic competition also turns on training efficiency, openness of weights/checkpoints, and speed of diffusion.

## What It Does Not Prove

- It does not prove that any third party can immediately match a complete commercial frontier system.
- It does not prove total equivalence with every proprietary capability of closed labs.
- It does not prove on its own that benchmark claims hold across all real-world uses.

## Reliability

- High reliability for documentary baseline questions because this is a `T1` paper. It is strongest on what it directly records and weaker on broader interpretation.
- Current note risk posture: `medium`.

## Claims It Supports

- `deepseek-v3-technical-report-2024-claim-01`: That by late 2024 there was already a competitor publicly claiming frontier-adjacent performance through a technical report. (Documented Fact)
- `deepseek-v3-technical-report-2024-claim-02`: That the debate over reasoning, efficiency, and cost cannot be reduced to the marketing of a single Western actor. (Documented Fact)
- `deepseek-v3-technical-report-2024-claim-03`: That narratives of absolute scarcity around advanced capabilities must be contrasted with open technical reports and partial replicability. (Documented Fact)
- `vector06-open-publication-solves-control-overclaim-claim-01`: That open reasoning papers or public model releases eliminate the politics of compute concentration, distribution control, or institutional gatekeeping around frontier AI. (Speculative Narrative Risk)

## Risk Label

- Medium. Strong primary technical source, but still a self-report by the authors; benchmark and cost claims should be contrasted externally when needed.
