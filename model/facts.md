# DataHub platform — verified facts for the diagrams

Every claim in these packs must trace to a line here (source in brackets).

## The hub

- **DataHub** — Java 17 / Spring Boot 3.3.4, one service, **one capability per
  application, one schema per application**, all under `/api/datahub`
  [docu_independent/services/datahub/README.md].
- Two deployment faces:
  1. **Deployed core** (`dh-repository-backend-….us-east4.run.app`): `/metarepository/*`
     — repository catalogue (repo → dataset → table → column, descriptions, hints),
     `dbConnectors` to source DBs, `setContext`, `repoStatus`, **query execution**
     [qa/textsql/docs/DATAHUB.md].
  2. **Reference capability host** (`services/datahub`, port 8090): `build` (schema
     `ais`: records/metadata/connections, vendored), `chat` (guided-QA context:
     qa-context, ddl-queries, context-criteria), `docuqa` (schema `docuqa`: 9 corpus
     tables + indices + triggers, job queue, content plane) [services/datahub README +
     controllers].
- DataHub DB: PostgreSQL 16 + pgvector (HNSW m=16, ef=64), migrated by Flyway
  (V1 ais, V2 docuqa). Content plane: `blobs/{sha256}`, `corpus/{document_id}/…` —
  manifest, header, relations, page text, images; purge never deletes blobs.
- Coarse transactional endpoints (outbox semantics): `documents/ingest-submit`,
  `documents/{id}/persist` (idempotent), `documents/{id}/purge`, `jobs/{id}/fail`.
- Queue: table `jobs`, claim `FOR UPDATE SKIP LOCKED`, attempts+1, jittered
  exponential backoff, dead-letter at max_attempts, lease sweep.
- Search: `POST /search/vector` (halfvec cosine), `POST /search/lexical`
  (ts_rank_cd), `GET /documents/search`, `GET /headers/search`,
  `GET /contracts/{id}/versions`. Caller does RRF fusion, coverage rerank, caps.
  Graph: one-hop `neighbors`; capped BFS stays in senses.
- Contract-drift gate: Java `OpenApiContractTest` vs
  `contracts/openapi/datahub-docuqa.yaml`.

## Integration semantics (every spoke)

- Four headers on every call: `Sessionid`, `Tenantid`, `Tenantorgunitid`,
  `Username`; missing one → HTTP 500 (not 401). Case-insensitive; per-request
  propagation with `DATAHUB_*` env fallback. No token, no login endpoint.
- Response envelope `{code, status, data, pagination, message}` on list/mutation
  endpoints; **not everything enveloped** (`/execute` bare with `res_status`,
  `count/jobstatus` bare array).
- Not found = **HTTP 500 + `code: DH40002`**, never 404. Domain errors arrive as
  HTTP 500 with 200-shaped body — branch on `code`.
- `POST /metarepository/execute` **always answers HTTP 200**; success is
  `res_status: true`. No server-side row cap — cap client-side (spokes use 1000).
  Heavy queries 30–50 s → client timeout 120 s.
- Tenant is shared production with real source DBs attached.

## Spoke 1 — Text-SQL (qa/textsql)

- One repo, two services, one shared spine (ADR-0001). no-data :8001 (build DDL,
  criteria, embeddings; guided QA; **never executes**), yes-data :8000 (agentic QA,
  **does execute**). Spine: config, db pool, sessions_db, cleanup, observability,
  protobuf stubs, DataHub client. Capability layer per-service (agents/graphs not
  shared — 2 generations, 31–77% similar).
- Own state: Postgres+pgvector per service (yes-data :5433, no-data :5435): `history`,
  `conversation_sessions`, `conversation_state`. Builds table?
  build-feature tables belong to DataHub.
- `DATAHUB_API_STYLE = reference | repository` switch (deployed default
  `repository`): QA context derived from `metaEditJsonData`; build feature still on
  the reference contract — next milestone.
- Discovery: `GET /api/v2/QA/repositories[/{repo_id}]`, `user-id` header required.
- yes-data live run: 10,757,124 order lines via `/metarepository/execute` (OMS repo,
  Oracle). Multi-dialect: PostgreSQL, Oracle, BigQuery.
- Observability stack: OTel collector 4317/4318 → Tempo 3200, Prometheus 9090,
  Grafana 3000. **The MCP variant is out of scope** (own branch, not drawn).

## Spoke 2 — DocuQA (docu_independent)

- **No database of its own** (ADR-0014): DataHub owns corpus tables, queue, content
  plane. Services hold no DB credentials, no SQL.
- harness :8003 — Node 22, only public surface, agent loop (pi-agent-core), 12
  tools, frozen SSE vocabulary (`update/token/complete/error`), citation guard
  (every figure matched to a `corpus://` ref), durable sessions own volume
  (ADR-0013, never in DataHub). llm/ = Gemini client.
- library :8001 api (upload, hash, ingest-submit) + worker (claim → pipeline →
  persist, at-least-once; pipeline does no catalog I/O — pure BuildResult).
- senses :8002 — vector+lexical fusion (RRF, coverage rerank, per-doc cap),
  reference resolution (content plane, char budgets), capped BFS (depth ≤3,
  100 nodes, 500 edges) carrying `corpus://` evidence.
- lib: `docuqa_corpus` (domain), `docuqa_datahub` (transport).
- web UI :5173 React/Vite proxies to harness. python 3.13.

## Spoke 3 — WebBot-Lite (code name Quarry, package `analytica`, edge_dog) — renamed for the packs per user

- Browser-native analysis agent. Data never leaves the tab: DuckDB-WASM in a
  Web Worker, OPFS workspace, localStorage KV. Same harness in tab/CLI/embed —
  three host seams: `QueryEngine`, `KVStore`, `LlmClient`.
- Egress from tab: model calls (schema, compact column profiles, context doc,
  tool results capped at 50 rows) and — in aidesk/embed mode — DataHub metadata
  and ONE generated SQL statement via same-origin proxy /api/datahub (real
  identity headers injected server-side; browser gets placeholders).
  `EmbedConfig.datahub` for embed hosts; runtime connector shared by all entries.
- Client enforces: 4 headers, envelope unwrap, DH40002→not-found, typed
  `DataHubQueryRejected` with server `msg` (e.g. ORA-00904); row cap
  `DATAHUB_MAX_ROWS` (default 1000); SQL wrapped (`ROWNUM` / `LIMIT`) read-only.
- execute result rows → CSV → uploaded back as a local DuckDB table (verified
  live: OMS repo, `COUNT` = 812211).
- Deploy: docker → nginx + Gemini proxy, one process, Cloud Run
  (`analytica-web`, :8080). Langfuse sidecar in dev (`npm run dev:trace`).

## Spoke 1b — Text-SQL MCP transport (qa/text-sql-mcp)

- Standalone repo (the MCP variant lives on its own branch per ADR-0001 — the consolidation
  leaves it alone; it is not a copy of the shared spine).
- Same qa_agentic pipeline (LangGraph + PydanticAI) over **FastMCP**: transports stdio · SSE ·
  streamable-http (:8080), entrypoints/mcp_server.py.
- Direct DataHub, no proxy: same client layer (`src/core/datahub.py` — envelope, DH40002, four
  headers; `repository_metadata.py` pure parser; two `QaContextStore` impls), both API styles via
  `DATAHUB_API_STYLE`.
- Tools: `text_sql_list_repositories`, `text_sql_get_repository` (include_ddl), `text_sql_ask`
  (repo_id only — connector/dialect resolved from DataHub), `text_sql_resume`, history tools,
  `text_sql_health`. Resources: `repo://{id}/schema|criteria|metadata`, `datahub://repositories`,
  `conversation://{thread}/state`. Discovery-first instructions; error mapping (no stack traces).
- Own Postgres for history + LangGraph checkpoints; optional Redis sessions; **degraded startup**:
  if Postgres/LLM init fails it still serves discovery + health, runtime tools return actionable
  config errors. Deliberate deviation: catalogue `dialect` falls back to `dataSourceType`.
- Verified live against the deployed DataHub (PLAN.md steps 1–11 all ✅).

## Not drawn (deliberate)

- The pre-refactor hub (`work/projects/datahub`, dh-commoner) — historical.
- Text-SQL MCP variant (own branch, out of scope per ADR-0001).
- Code-level module graphs below capability level.

## Diagram conventions

- solid = synchronous HTTP/JSON · dashed = content/object plane · dotted = SSE /
  model calls. Colours: DataHub blue `#dae8fc/#6c8ebf`, Text-SQL orange
  `#ffe6cc/#d79b00`, DocuQA green `#d5e8d4/#82b366`, Quarry purple
  `#e1d5e7/#9673a6`, ghost gray, state yellow `#fff2cc/#d6b656`.
- Exec pack: 16:9 pages, neutral capability names, no ports/endpoints.
- Tech pack: A3 landscape, endpoint families, ports, schemas, semantics.
