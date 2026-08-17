# TeleRAG

TeleRAG is a grounded retrieval-augmented assistant for official 3GPP
telecommunications specifications. It answers from indexed source evidence,
returns provenance-rich citations, and abstains when retrieval, generation, or
validation is insufficient.

```text
3GPP PDFs
  -> metadata and checksums
  -> page-preserving extraction
  -> clause-aware structure detection
  -> provenance-preserving chunks
  -> dense and BM25 retrieval
  -> reciprocal-rank fusion and reranking
  -> evidence sufficiency gate
  -> grounded Gemini generation
  -> citation and grounding validation
  -> ANSWERED or controlled ABSTAINED response
```

See [docs/architecture.md](docs/architecture.md) for the component and trust-boundary design.

## Repository status

The implemented project contains:

- Python ingestion, retrieval, generation, validation, API, and evaluation modules.
- A React/Vite frontend with citation display and source inspection.
- Unit and integration tests.
- Docker and Docker Compose configuration.
- Reproducible manifest and processed-index outputs under `data/processed/`.

The current verified test suite contains 14 passing tests. The live local
demonstration has also been verified with Gemini `gemini-2.5-flash-lite`,
including validated citations and grounding.

## Corpus

The supplied PDFs currently reside directly under `data/`:

| Specification | Supplied version | Release | Pages |
|---|---:|---:|---:|
| TS 23.501 | 17.10.0 | 17 | 575 |
| TS 23.502 | 17.13.0 | 17 | 755 |
| TS 24.501 | 17.15.0 | 17 | 996 |
| TR 21.905 | 16.0.0 | 16 | 70 |

The intended Release 18 documents TS 23.503, TS 38.300, and TS 38.331 are not
currently supplied. Metadata conflicts are recorded in the corpus manifest
rather than silently corrected.

For the current development corpus, all four PDFs can be explicitly processed:

```powershell
.\.venv\Scripts\python.exe -m app.ingestion `
  --input data `
  --expected-release 18 `
  --build-indexes `
  --allow-hash-fallback
```

This processes all available documents while recording release mismatch
warnings. To enforce a release boundary, use strict mode:

```powershell
.\.venv\Scripts\python.exe -m app.ingestion `
  --input data `
  --expected-release 18 `
  --strict-release
```

Strict mode skips documents whose embedded release does not match the expected
release. It never moves, overwrites, or deletes source PDFs.

## Setup

Create the project virtual environment and install the tested base stack:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Optional semantic embeddings and cross-encoder reranking are available through
the larger ML stack:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
```

The ML stack may download large PyTorch and model artifacts. Without it,
`ALLOW_HASH_FALLBACK=true` enables the deterministic local embedding and
lexical reranking fallback used for local testing. The fallback is intended for
development and reproducibility, not as a replacement for semantic models in a
production deployment.

## Configuration

Copy `.env.example` to `.env` and set the provider configuration. Never commit
`.env` or expose the API key in logs or frontend code.

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
LLM_MODEL=gemini-2.5-flash-lite
ALLOW_HASH_FALLBACK=true
```

The application loads `.env` automatically. If a Gemini key is present and
`LLM_PROVIDER` is omitted, Gemini is selected by default. Provider failures are
converted into controlled abstentions.

## Running the backend

Start the API after ingestion and index creation:

```powershell
$env:ALLOW_HASH_FALLBACK="true"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The API listens on `http://localhost:8000`.

### Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service and retrieval availability |
| POST | `/api/v1/chat` | Grounded question answering |
| POST | `/api/v1/ingestion/run` | Run controlled ingestion |
| GET | `/api/v1/documents` | List manifest documents |
| GET | `/api/v1/documents/{document_id}` | Inspect one manifest record |

Example chat request:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/api/v1/chat `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"question":"What does the AMF do during registration?"}'
```

Responses contain `status`, `answer`, validated citations, grounding metadata,
and retrieval counts. A citation includes specification, release, version,
clause, page range, source document, and inspectable source text.

## Running the frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

The frontend runs on `http://localhost:5173` and communicates with the backend
at `http://localhost:8000`. It displays answers, abstentions, grounding status,
metadata-rich citations, and a source-text inspector.

To create a production frontend bundle:

```powershell
npm.cmd run build
```

## Testing

Run all unit and integration tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The test suite covers:

- PDF metadata and release validation.
- Clause detection and structure-aware chunking.
- BM25, dense retrieval, reciprocal-rank fusion, and reranking fallback.
- Citation rejection and grounding validation.
- Out-of-domain and invalid-request abstention.
- Prompt-injection trust-boundary behavior.
- Provider failure handling.
- API contracts and real-corpus strict ingestion behavior.

## Evaluation

Evaluation code is under `app/evaluation/`. Run it with:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner
```

`data/evaluation/questions.json` is intentionally empty until questions can be
manually tied to verified clauses in the actual indexed corpus. No evaluation
scores are fabricated. Populate it with human-verified source references before
using retrieval recall, precision, MRR, or abstention metrics.

## Docker

Docker configuration is provided through `Dockerfile` and
`docker-compose.yml`:

```powershell
docker compose up --build
```

Docker was not available in the current verification environment, so the
container build remains an environment-dependent verification step.

## Security and grounding controls

- Secrets are loaded from environment configuration only.
- Retrieved PDF text is treated as untrusted data, not instructions.
- User questions have length and validation limits.
- Metadata filters support specification, release, and version constraints.
- Evidence is gated before generation.
- Provider output must use retrieved source IDs.
- Invalid citations and unsupported claims are rejected.
- Provider failures result in controlled abstention.
- Chain-of-thought and hidden prompts are not returned to clients.

## Limitations and next improvements

- The current supplied corpus is not the intended Release 18 corpus.
- The local verified path uses hash embeddings unless the optional ML stack is installed.
- Live Gemini generation requires a valid Gemini key and an available model.
- Evaluation ground truth still needs to be authored against the final corpus.
- Complex tables and diagrams may require additional parser-specific handling.
- Future work includes stronger table extraction, semantic claim-level grounding,
  rate limiting, background ingestion jobs, and CI-based Docker verification.
