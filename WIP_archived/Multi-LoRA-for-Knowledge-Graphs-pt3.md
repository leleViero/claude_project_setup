_This is Part 3 of our series on building knowledge graphs with local LLMs._ [_Part 1_](https://medium.com/graph-praxis/local-llms-for-graph-rag-extraction-what-actually-works-388233dd9eda) _benchmarked four open-weight models on entity-relation extraction._ [_Part 2_](https://medium.com/graph-praxis/building-knowledge-graphs-with-local-llms-from-benchmarking-to-fine-tuning-ed572268aa3f) _fine-tuned Qwen3–8B on the REBEL dataset and achieved 100% structural reliability — but Triple F1 collapsed on domain-specific text. The diagnosis: a single fine-tuned model learns one predicate vocabulary and can’t transfer it across domains. This article is about the architectural solution._

## The Problem: One Adapter Can’t Speak Every Domain

In Part 2, we fine-tuned Qwen3–8B on 3,000 REBEL samples and got a model that produces perfect JSON every single time. 100% schema conformance, no parsing failures, no retries. Structurally, the problem was solved.

But when we pointed it at our legal documents, it produced triples like `(TechCorp Industries, filed a patent infringement lawsuit against, DataFlow Systems)` instead of the expected `(TechCorp Industries, filed_lawsuit_against, DataFlow Systems)`. When we evaluated it on held-out REBEL data, something even stranger happened: the model extracted entirely different — but equally valid — triples from the same text. A passage mentioning Deutsche Eislauf-Union and Germany would yield `(Deutsche Eislauf-Union, organizes, competition)` from the model, while REBEL's gold label was `(Deutsche Eislauf-Union, country, Germany)`. Both correct. Neither matching.

The core issue is that a production pipeline doesn’t process one type of document. Ours handles legal filings, medical records, financial reports, and technical documentation. Each domain has its own entity types, predicate vocabularies, and extraction conventions. A legal adapter needs to output `filed_lawsuit_against` and `Party` entities. A medical adapter needs `treats_condition` and `Drug` entities. A financial adapter needs `acquired_by` and `Instrument` entities.

The naive solutions don’t work. Training one model on all domains creates predicate vocabulary conflicts — the model averages across domains and speaks none of them well. Running separate fine-tuned models per domain means 16GB × N domains in GPU memory, which scales terribly. Using few-shot prompting per domain gets the best extraction quality (Part 1 showed Llama 3.1 hitting 0.732 Triple F1 with few-shot), but at 20% schema conformance — meaning 80% of your documents produce unparseable output.

We needed something that scales like one model but specializes like many.

## The Idea: Modular Domain Adapters

LoRA (Low-Rank Adaptation) fine-tuning works by freezing the base model’s weights and training a small set of adapter matrices — low-rank decompositions that modify the attention and feed-forward layers. For a Qwen3–8B model with rank 64, each adapter is roughly 250MB. The base model is 16GB. The adapter is 1.5% of the base.

This asymmetry is the whole idea. Instead of N separate fine-tuned models, we keep one base model loaded and swap lightweight adapters in and out depending on the document domain. The memory math makes the case:

Four separate fine-tuned models: 4 × 16GB = 64GB. That’s three to four GPUs just for extraction. One base model plus four LoRA adapters: 16GB + 4 × 250MB = 17GB. That fits on a single RTX 3090 with room for KV cache. Same domain coverage, 99.7% less memory.

But does the theory hold in practice? A key concern with domain-specific adapters is catastrophic forgetting — when specializing for legal text, does the model lose its ability to produce valid JSON or extract entities in general?

This is where a 2024 ICML paper, “LoRA Learns Less and Forgets Less” by Biderman et al., becomes directly relevant. They showed that LoRA and full fine-tuning sit on the same Pareto curve: LoRA learns less of the target domain but also forgets less of what the base model already knows. For multi-domain extraction, this tradeoff is exactly what we want. Each adapter specializes in its domain’s predicate vocabulary without destroying the base model’s structural JSON generation ability or general entity recognition. The forgetting resistance isn’t a limitation — it’s the enabling property.

The infrastructure to serve this has also matured. S-LoRA (Sheng et al., 2023) demonstrated serving thousands of concurrent LoRA adapters on a single GPU using unified memory paging. Punica (Chen et al., 2023) introduced the SGMV kernel that batches inference across different adapters simultaneously, achieving 12x throughput over sequential serving. vLLM adopted both of these natively. This isn’t experimental — it’s production infrastructure with battle-tested implementations.

## Our Pipeline: Classify, Route, Extract

The architecture has three stages: a lightweight classifier that determines the document’s domain, a routing layer that selects the appropriate LoRA adapter, and the extraction model itself. Each stage is independently simple. Together, they solve the multi-domain problem.

## Stage 1: Document Classification

The routing decision — which adapter should process this document? — needs to be fast and doesn’t need to be perfect. We considered three approaches, each with different tradeoffs.

The simplest is **metadata-based routing**. In most production pipelines, documents arrive with context: which system they came from, which department uploaded them, what file type they are. A legal document management system feeds the legal adapter. A clinical notes database feeds the medical adapter. This adds zero latency and requires no model at all. For pipelines with clean metadata, this is the right answer.

When metadata isn’t available, a **lightweight classifier** works well. A fine-tuned DistilBERT or RoBERTa-small model classifies documents into domain categories in under 5ms on CPU. These models are 250MB — comparable to a single LoRA adapter — and can be trained on a few hundred labeled document headers. You don’t need 8 billion parameters to distinguish a patent filing from a clinical trial report.

The third option is **embedding-based routing**: compute document embeddings, compare to domain centroid vectors, and route to the nearest domain. No training required beyond computing the centroids from a handful of example documents per domain. Slightly less accurate than a trained classifier, but deployable immediately.

We add a confidence threshold to all approaches. If the classifier’s confidence falls below 70%, the document routes to a general-purpose adapter trained on the REBEL base without domain specialization. Better to extract with generic predicates than to apply the wrong domain’s vocabulary.

## Stage 2: Adapter Routing via vLLM

The serving layer is where the multi-LoRA magic happens. vLLM supports multiple LoRA adapters natively through its `--enable-lora` flag. The server loads the base model once and keeps adapter weights either in GPU memory (hot) or CPU memory (warm), swapping them in on demand.

The server starts with:

```
vllm serve Qwen/Qwen3-8B \
  --enable-lora \
  --max-loras 4 \
  --max-lora-rank 64 \
  --max-cpu-loras 8 \
  --lora-modules \
    legal=./adapters/legal \
    medical=./adapters/medical \
    financial=./adapters/financial \
    technical=./adapters/technical
```

`--max-loras 4` keeps four adapters in GPU memory simultaneously. `--max-cpu-loras 8` keeps an additional four in CPU memory for quick swap-in. The `--max-lora-rank` must match the rank used during training.

The API is OpenAI-compatible. The routing layer simply sets the `model` parameter to the appropriate adapter name:

```
response = client.chat.completions.create(
    model="legal",  
    messages=[
        {"role": "system", "content": EXTRACTION_PROMPT},
        {"role": "user", "content": document_text}
    ]
)
```

Switching between pre-loaded adapters is effectively free — it’s a pointer swap in the attention layers, not a model reload. If an adapter needs to be loaded from CPU memory, the overhead is 50–100ms. We pre-load all hot adapters at startup by sending a dummy request for each one, which primes the LRU cache.

The SGMV kernel from Punica, integrated into vLLM, means that requests targeting different adapters can be batched in the same forward pass. A batch containing three legal documents and two medical documents processes simultaneously — no need to sort by domain first.

## Stage 3: Domain-Specific Extraction

From the model’s perspective, nothing changes between adapters. The system prompt is identical. The JSON schema is identical. The base model is identical. What changes is the learned behavior in the adapter weights: which predicates the model produces, which entity types it recognizes, and how it decomposes complex passages into atomic triples.

Here’s a concrete example. Given a passage about a pharmaceutical company’s acquisition, the same system prompt with different adapters produces:

**Legal adapter:**

```
{
  "entities": [
    {"name": "Pfizer", "type": "Party"},
    {"name": "Seagen", "type": "Party"},
    {"name": "SEC", "type": "Regulatory_Body"}
  ],
  "triples": [
    {"subject": "Pfizer", "predicate": "acquired", "object": "Seagen"},
    {"subject": "SEC", "predicate": "approved_merger", "object": "Pfizer"}
  ]
}
```

**Financial adapter:**

```
{
  "entities": [
    {"name": "Pfizer", "type": "Company"},
    {"name": "Seagen", "type": "Company"},
    {"name": "$43 billion", "type": "Amount"}
  ],
  "triples": [
    {"subject": "Pfizer", "predicate": "acquired_for", "object": "$43 billion"},
    {"subject": "Seagen", "predicate": "acquired_by", "object": "Pfizer"}
  ]
}
```

Same passage, same model weights, same prompt. Different adapter, different extraction focus. The legal adapter surfaces regulatory relationships and uses `Party` entities. The financial adapter surfaces transaction amounts and uses `Company` entities. Both are correct and useful; each serves a different downstream query pattern.

The extraction format is identical across all adapters — the same JSON schema with the same `entities` and `triples` structure. This means downstream graph ingestion doesn't need to change per domain. A single pipeline writes to Neo4j regardless of which adapter produced the triples.

## Training Multiple Adapters: Practical Guide

## Data Preparation

Each domain adapter needs its own training set, but they all share a common foundation. The recipe we’ve converged on has two layers.

The **base layer** is the same across all adapters: 2,500–3,000 samples from REBEL, filtered for quality (100–1500 character passages, 2–15 triples each, no self-referential triples or date entities). This teaches the model the structural extraction pattern — how to read a passage, identify entities, form triples, and output valid JSON. We described the REBEL conversion pipeline in detail in Part 2.

The **domain layer** is what differentiates each adapter: 200–500 hand-labeled examples using the exact predicate vocabulary and entity types that your domain requires. These samples don’t need to be long or complex. What matters is consistency — every example uses the same predicate names, the same entity type inventory, and the same granularity of triple decomposition.

We blend these at roughly 85% REBEL, 15% domain-specific. The REBEL base prevents overfitting to the small domain set, while the domain overlay teaches the model exactly which predicates to use and which entity types to recognize.

The data format is identical across domains: chat-format JSONL with a system prompt, a user message (the passage), and an assistant message (the extraction JSON). Only the content of the assistant messages differs between domains. This means the same training script works for every adapter.

One practical tip that saved us significant rework: define the predicate vocabulary before labeling a single example. Create a spreadsheet of 30–50 target predicates per domain, with clear definitions and examples. `filed_lawsuit_against` and `filed_suit_against` in the same training set will confuse the model. Consistency in predicates matters far more than volume of training data.

## Training Configuration

We train each adapter independently, never jointly. This was a deliberate choice backed by the Mixture-of-LoRAs literature (2024): different domains have different data scales and training difficulty, and joint training causes interference between tasks. Separate QLoRA runs avoid this entirely.

The critical constraint: **all adapters must be trained from the same base model checkpoint.** This is what makes them swappable. If adapter A was trained from Qwen3–8B commit `abc123` and adapter B from commit `def456`, they won't behave correctly when hot-swapped on the same base model.

The rest of the configuration is the same as Part 2:

-   **Rank 64, alpha 128.** Higher than the typical r=16 default. Structured extraction with domain-specific predicates needs more adapter capacity. The alpha-to-rank ratio of 2 keeps the learning rate scaling reasonable.
-   **Learning rate 3e-5 with cosine schedule.** Three epochs over the full dataset, warmup over the first 3% of steps.
-   **QLoRA with 4-bit quantization.** Fits comfortably on 2x RTX 3090 GPUs.
-   **User-turn masking.** Loss computed only on the assistant’s output, not the input passage.
-   **Training time: 30–45 minutes per adapter.** Four adapters = 2–3 hours total wall time. Not days.

## The Training Trick That Matters Most

The single most impactful decision in our training pipeline isn’t the learning rate or the rank or the number of epochs. It’s the ratio of general-to-domain-specific data.

Training purely on 200 domain-specific examples produces an adapter that overfits to the predicate vocabulary but loses the general extraction ability. It knows to output `filed_lawsuit_against` but forgets how to decompose complex multi-entity passages into atomic triples. Training purely on REBEL produces the opposite: excellent extraction structure but wrong predicates (the problem from Part 2).

The blend is what works. REBEL teaches “how to extract” — the structural pattern of reading text, identifying entities, forming subject-predicate-object triples, and outputting valid JSON. The domain overlay teaches “what to extract” — the specific predicates, entity types, and decomposition conventions your domain requires.

We start at 85/15 (REBEL/domain) and adjust based on validation metrics. If the adapter produces correct predicates but poor triple decomposition, increase the REBEL proportion. If it decomposes well but uses the wrong predicates, increase the domain proportion. In practice, the sweet spot is usually between 80/20 and 90/10.

Always validate on both domain-specific test samples and a general extraction holdout. If general extraction performance drops more than 10% relative to the REBEL-only adapter, the domain proportion is too high.

## Avoiding Common Pitfalls

We’ve trained enough adapters to have a list of things that go wrong. Here’s the short version.

**Entity type alignment across adapters.** If the legal adapter uses `Organization` and the financial adapter uses `Company` for the same concept, your downstream knowledge graph will have duplicate entity types that should be merged. Define a shared entity type ontology across all domains before training. Domain-specific types (like `Statute` or `Drug`) extend the shared base; they don't replace it.

**Don’t overtrain.** Three epochs are usually enough. LoRA is notably sensitive to hyperparameters — Biderman et al. (2024) showed this clearly. Watch validation loss and stop early if it climbs. We’ve seen adapters degrade after epoch 4–5, even when training loss continues to decrease.

**Test the base model too.** After training a legal adapter, run it through the general REBEL evaluation from Part 2. If Entity F1 drops below 0.6 or schema conformance drops below 95%, something went wrong — probably too much domain-specific data or too high a learning rate.

**Version your adapters.** In production, you’ll be updating adapters as your domain vocabulary evolves, as new predicate types emerge, and as you fix extraction errors. Treat adapters like model artifacts: version them, track the training data provenance, log evaluation metrics, and keep rollback copies. A bad adapter update that goes to production will result in corrupted triples in your knowledge graph.

## System Setup: From Training to Serving

### Hardware Requirements

The beauty of the multi-LoRA approach is that it fits on hardware you probably already have.

For **development and proof of concept**, a single RTX 3090 (24GB) is sufficient. You can train one adapter at a time and serve 2–3 concurrent adapters. This is the setup we used for the experiments in Part 2.

For **small production**, two RTX 3090s or a single A100 (40GB) is the sweet spot. Training with `accelerate` across two GPUs cuts training time in half (33 minutes down to under 20 minutes per adapter). Serving 4-8 adapters is comfortable.

For **scaling up** — if you’re serving 16+ domain adapters or handling hundreds of concurrent extraction requests — an A100 80GB or H100 gives you room for both adapter weights and the KV cache that dominates memory at high concurrency.

Storage is never the bottleneck. Each adapter is ~250MB at rank 64. A hundred adapters is 25GB on disk — smaller than the base model.

### Training Pipeline

The end-to-end flow for adding a new domain adapter:

**Step 1: Prepare training data.** Run the REBEL conversion pipeline (`prepare_rebel.py`) for the base layer. Hand-label 200-500 domain-specific examples following your predicate vocabulary. Blend into a single JSONL file.

**Step 2: Train.** Run QLoRA training with accelerate:

```
accelerate launch --num_processes 2 scripts/train_server.py \
  --data data/legal_train.jsonl \
  --output outputs/legal-adapter
```

**Step 3: Evaluate.** Test the adapter against your domain-specific benchmark and the general REBEL holdout:

```
python scripts/evaluate_local.py \
  --model-path outputs/legal-adapter-merged \
  --compare-with results/baseline_aggregate.csv
```

**Step 4: Deploy.** Copy the adapter weights to the serving directory and register with vLLM. If the server is already running, vLLM picks up new adapters dynamically — no restart required.

The whole cycle from “we need a new domain adapter” to “it’s serving in production” takes a day: half a day for data labeling, an hour for training, an hour for evaluation, and the rest for review and deployment.

## Serving Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│   Document   │────>│   Classifier    │────>│   vLLM + Multi-LoRA  │
│   Ingestion  │     │  (DistilBERT /  │     │                      │
│              │     │   metadata)     │     │  Base: Qwen3-8B      │
└──────────────┘     └─────────────────┘     │  ├─ legal adapter    │
                            │                │  ├─ medical adapter  │
                       domain_id             │  ├─ financial adapter│
                            │                │  └─ technical adapter│
                            └───────────────>│                      │
                                             └──────────┬───────────┘
                                                        │
                                                   JSON triples
                                                        │
                                             ┌──────────▼───────────┐
                                             │   Knowledge Graph    │
                                             │   (Neo4j / Neptune)  │
                                             └──────────────────────┘
```

The key vLLM configuration flags:

`--enable-lora` activates multi-LoRA support. `--max-loras 4` controls how many adapters stay in GPU memory simultaneously — set this to the number of domains you expect to serve concurrently. `--max-lora-rank 64` must match the rank used during training; mismatches will silently produce garbage output. `--max-cpu-loras 8` keeps additional adapters in CPU memory for fast swap-in without reloading from disk. `--lora-modules` maps human-readable adapter names to weight directories.

At request time, the classifier’s output maps directly to a vLLM model name. The routing logic is a single if-statement that sets the `model` parameter in the API call. No orchestration framework, no message queue, no complexity beyond what's needed.

## What’s Coming Next: Automatic Routing and Adapter Fusion

Our current pipeline uses document-level classification: one document, one adapter, one extraction. This handles the vast majority of our workload. But some documents are genuinely multi-domain — a legal brief that discusses financial instruments, or a clinical trial report with regulatory compliance sections. For these, choosing one adapter means losing the other domain’s extraction quality.

The research community is actively working on this problem, and several approaches are worth watching.

**LoRA-Switch** (Kong et al.) introduces token-level dynamic routing with fused CUDA kernels. Instead of choosing one adapter per document, the model routes individual tokens to different adapters during the forward pass. The system-algorithm co-design reduces the latency overhead of dynamic routing from 2.5–3x down to about 24% over static serving. For passages that span legal and financial content in the same paragraph, this could meaningfully improve extraction quality.

**LORAUTER** (Ostapenko et al.) takes a different approach: routing based on task representations rather than document classification. Adapters are selected based on embedding similarity between the input and learned task vectors. More elegant than maintaining a separate classifier, and it scales with the number of tasks rather than the number of adapters.

**MoLoRA** (Li et al.) pushes furthest — per-token mixture of LoRA experts with learned gating. The headline result is striking: a 1.7B model with MoLoRA routing exceeds a vanilla 8B model on reasoning benchmarks. For multi-domain extraction, this is the most promising direction. But it’s too new for production deployment, and framework integration is still in early stages.

**Adapter fusion and LoRA Soups** (Zhao et al.) take the opposite approach: instead of switching between adapters, merge their weights at inference time with learned mixing coefficients. This works well when domains overlap — a legal-financial contract benefits from a blend of both adapters rather than a hard choice between them. LoRAHub showed this is practical for cross-task composition.

For our pipeline, document-level routing handles 95% of cases cleanly. The remaining 5% — ambiguous or genuinely multi-domain documents — is where these techniques will matter. We’re watching LoRA-Switch for vLLM integration most closely, as it’s the most mature of the dynamic approaches.

## Key Takeaways

**One base model + N adapters beats N separate models.** The memory math is overwhelming: 17GB vs 64GB for four domains, on a single GPU. The adapters are hot-swappable with zero model reload, and vLLM’s SGMV kernel batches across different adapters in the same forward pass.

**Train adapters independently, not jointly.** Each domain is its own QLoRA run: same base model, same hyperparameters, different training data. 200–500 domain-specific examples blended with a REBEL base. 30–45 minutes per adapter on consumer GPUs.

**Document classification is the routing layer, not the bottleneck.** A tiny classifier, metadata rules, or even embedding similarity handles routing. The adapter selection doesn’t need to be perfect — it needs to be mostly right, with a general-purpose fallback for uncertain cases.

**vLLM makes this production-ready today.** Native multi-LoRA support, OpenAI-compatible API, LRU caching, concurrent adapter batching. The infrastructure exists; the engineering effort is in the training data, not the serving layer.

**LoRA’s forgetting resistance is the enabling property.** Each adapter specializes without compromising the base model’s JSON generation or general extraction capabilities. Biderman et al. (2024) showed this empirically: LoRA sits on a Pareto curve of learning more while forgetting less. For modular domain adapters, that tradeoff is exactly what you want.

**Define your predicate vocabulary before labeling.** This is the single most impactful thing you can do for extraction quality. A clean, consistent set of 30–50 predicates per domain, defined up front, yields better results than doubling the training data with inconsistent labels.

_This is Part 3 of our Graph RAG extraction series._ [_Part 1_](https://medium.com/graph-praxis/local-llms-for-graph-rag-extraction-what-actually-works-388233dd9eda?sk=00f0c37ddf4cb3407677989b1dda1fa3) _covers benchmarking local LLMs for extraction._ [_Part 2_](https://medium.com/graph-praxis/building-knowledge-graphs-with-local-llms-from-benchmarking-to-fine-tuning-ed572268aa3f?sk=986fb9f71221a266fb6a275eb5259340) _covers fine-tuning and the domain transfer problem. All experiments were run on NVIDIA RTX 3090 GPUs, using vLLM for inference and TRL/PEFT for fine-tuning._

**References**

-   Biderman et al., [“LoRA Learns Less and Forgets Less,”](https://arxiv.org/abs/2405.09673) ICML 2024
-   Sheng et al., [“S-LoRA: Serving Thousands of Concurrent LoRA Adapters,”](https://arxiv.org/abs/2311.03285) MLSys 2024
-   Chen et al., [“Punica: Multi-Tenant LoRA Serving,”](https://arxiv.org/abs/2310.18547) MLSys 2024
-   Kong et al., [“LoRA-Switch: Boosting Efficiency of Dynamic LLM Adapters via System-Algorithm Co-design,”](https://arxiv.org/abs/2405.17741) 2024
-   Ostapenko et al., [“LORAUTER: Effective LoRA Adapter Routing using Task Representations,”](https://arxiv.org/abs/2601.21795) 2025
-   Li et al., [“MoLoRA: Contrastive Learning-Guided Mixture of Long-Short LoRA Experts,”](https://arxiv.org/abs/2603.15965) 2025
-   Zhao et al., [“LoRA Soups: Merging LoRAs for Practical Skill Composition Tasks,”](https://arxiv.org/abs/2410.13025) 2024