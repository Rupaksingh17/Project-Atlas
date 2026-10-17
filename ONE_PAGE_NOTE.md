# What I Would Do With One More Week

If granted one additional week to extend Project Atlas beyond the take-home requirements, I would prioritize the following five architectural initiatives:

---

## 1. Hybrid Search with Cross-Encoder Re-Ranking
While dense embeddings (ChromaDB with all-MiniLM-L6-v2) excel at semantic similarity, they occasionally miss exact numerical figures and tabular codes.
- **Action**: Implement hybrid retrieval combining BM25 keyword matching with dense vector retrieval via Reciprocal Rank Fusion (RRF).
- **Re-ranker**: Introduce a lightweight cross-encoder (e.g. `bge-reranker-base` or `FlashRank`) to rescore the top 20 candidate chunks down to the 4 most relevant chunks before context injection. This reduces hallucination risk and improves citation precision for specific market metrics.

---

## 2. Semantic Caching for Sub-50ms Latency and Cost Reduction
In syndicated research environments, multiple analysts and clients often query identical or semantically equivalent questions (e.g., "smart water meter 2024 size" vs "2024 global smart water meter valuation").
- **Action**: Implement a semantic cache using Redis and cosine similarity thresholding (similarity >= 0.96).
- **Impact**: Cache hits return verified answers in under 50ms at zero LLM inference cost, drastically reducing operating expenditures while maintaining per-client entitlement isolation.

---

## 3. Multimodal Ingestion for Embedded PDF Charts and Infographics
Key market projections in syndicated reports are frequently locked inside charts, graphs, and infographics rather than raw body text.
- **Action**: Deploy an automated extraction pipeline using a multimodal visual model (such as Gemini Vision or LayoutLMv3).
- **Output**: Transcribe raster bar charts and growth plots into structured Markdown tables and JSON metrics at ingestion time, tagging each chart with its source page and coordinates.

---

## 4. Streaming Token Generation via Server-Sent Events (SSE)
Current integration returns complete responses via standard JSON payloads. While latency is under 1 second locally, live LLM generation across large documents benefits from progressive streaming.
- **Action**: Implement an SSE endpoint in FastAPI (`POST /chat/stream`) and integrate a JavaScript streaming chunk reader in the CodeIgniter 3 view.
- **Impact**: Decreases Time to First Token (TTFT) to under 400ms, enhancing perceived responsiveness during complex calculations.

---

## 5. Cloud Infrastructure and Automated Production CI/CD
- **Action**: Package the multi-container stack into AWS ECS (Fargate) behind an Application Load Balancer with AWS Aurora MySQL.
- **Security & Observability**: Introduce OpenTelemetry tracing with Langfuse for real-time cost, token, and latency observability per client organization. Provide infrastructure as code using Terraform.
