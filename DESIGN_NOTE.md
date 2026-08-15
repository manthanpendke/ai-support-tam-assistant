# Design Note — AI Technical Support & TAM Platform

## 1. Production Failure Modes

### Failure Mode 1: Incorrect LLM classification or hallucination

The LLM may incorrectly classify a ticket, invent information, or select a product or issue that is not supported by the available data. This is especially risky for urgency and routing decisions because an incorrect P1/P2 classification could affect support response times.

To detect this, the system validates every LLM response using Pydantic structured-output models. The triage pipeline also grounds known-issue information against the retrieved knowledge-base documents rather than trusting the LLM response alone. Evaluation cases provide regression coverage for important classification scenarios.

To mitigate this further in production, I would add confidence thresholds, human review for high-impact classifications, and continuous evaluation using representative production samples.

### Failure Mode 2: Retrieval failure or incorrect knowledge-base grounding

The retrieval layer may return an irrelevant document or fail to retrieve the correct troubleshooting information. This can result in an incorrect known-issue classification or an inappropriate support recommendation.

The current design uses TF-IDF retrieval and explicitly grounds structured error identifiers against retrieved knowledge-base content. The system also preserves the source document used for grounding so the result can be traced back to the knowledge base.

In production, I would monitor retrieval precision and add semantic/vector retrieval or a hybrid search strategy for larger knowledge bases. Retrieval results could also be evaluated using offline relevance metrics.

### Failure Mode 3: Incomplete or inconsistent customer data

Account data and ticket data can be incomplete or inconsistent. For example, an account may contain escalation notes mentioning P1 tickets while the structured P1 count is zero. Ticket account IDs may also not always have a corresponding account record.

The system therefore calculates deterministic account-health metrics from available data and exposes `data_quality_warnings` rather than silently hiding inconsistencies. Missing account records are handled gracefully.

In production, I would add schema validation at ingestion time, data-quality dashboards, and alerts for important inconsistencies.

## 2. Latency vs Quality

A concrete trade-off is the use of a lightweight TF-IDF retrieval layer before calling the LLM. TF-IDF is faster and simpler than introducing a remote embedding service or vector database, which keeps the prototype lightweight and reduces infrastructure dependencies.

The trade-off is that lexical retrieval may be less effective for semantically similar queries that use different terminology. A more sophisticated semantic retrieval system could improve recall but would add latency and infrastructure complexity.

If latency became the hard constraint, I would reduce the number of retrieved chunks, use a smaller/faster LLM for straightforward classification, cache repeated knowledge-base retrievals, and avoid unnecessary LLM calls when deterministic rules can safely answer the request.

## 3. Data Sensitivity

Support tickets and account summaries may contain personally identifiable information or other sensitive customer information. The current implementation uses only the synthetic dataset supplied for the assignment and does not introduce external customer data.

The design also avoids unnecessary external data sources and keeps the knowledge base local. API credentials are stored through environment variables rather than being embedded in source code.

In a production deployment, I would add PII detection and redaction before sending content to an external LLM API. Sensitive fields that are not required for the task should be removed before inference. Access controls, audit logging, encryption in transit and at rest, and a provider configuration that prevents training on customer prompts would also be required.

## 4. Scaling to 10× Volume

The current architecture is suitable for the assignment-scale dataset but would require changes at significantly higher volume.

The first bottleneck would likely be the retrieval layer and repeated LLM calls. A TF-IDF index can work well for a small knowledge base, but at larger scale I would move to a persistent vector or hybrid search index. Ticket and account data would also move from JSON files to a database or data service.

LLM calls would become the largest operational cost and latency factor. I would introduce asynchronous processing, request batching where appropriate, caching, rate limiting, retries with exponential backoff, and model routing based on task complexity.

For account-health generation, deterministic calculations should remain outside the LLM so that they can scale independently and remain reproducible. The LLM should primarily perform summarisation and synthesis.

The evaluation harness would also run automatically in CI and against sampled production data to detect regressions before model or prompt changes are deployed.