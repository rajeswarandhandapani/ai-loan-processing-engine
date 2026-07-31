# RAG — Retrieval-Augmented Generation

The agent has to answer questions about *our* lending policy. An LLM cannot do
that from training data: the policy is private and it changes. RAG solves this by
looking up the most relevant policy passages at question time and putting them in
the prompt, so the model answers from real text instead of memory.

## The pipeline

```
INGESTION  (offline, run once)          RETRIEVAL  (every question)
──────────────────────────────          ────────────────────────────
  policy.pdf                              "what credit score do I need?"
      │ parse   (pypdf | Azure DI)             │ embed  (same model!)
      ▼                                        ▼
  plain text                               query vector
      │ chunk   (1000 chars, 200 overlap)      │ nearest-neighbour search
      ▼                                        ▼
  ~5 chunks                                top 5 chunks
      │ embed   (text → vector)                │
      ▼                                        ▼
  VECTOR STORE  ◄────────────────────────  prompt context → LLM answer
  (Azure AI Search | ChromaDB)
```

The one rule that ties the halves together: **the same embedding model must be
used for both.** Vectors from two different models are not comparable, so a query
embedded with model A cannot find chunks embedded with model B.

## Modules

| File | What it does |
| --- | --- |
| `embeddings.py` | Text → vector. Local ONNX (default), sentence-transformers, or Azure OpenAI. |
| `chroma.py` | Local vector store (default) — an embedded database in a directory. |
| `azure_search.py` | Hosted vector store — a managed Azure service. |
| `vector_store.py` | Reads the config and hands back whichever store is selected. |
| `ingestion.py` | The offline pipeline: parse → chunk → embed → store. |

Everything downstream depends only on LangChain's `VectorStore` interface
(`add_documents` and `similarity_search`), which is why the backend is a config
switch rather than a code change. The consumer is the `search_lending_policy`
tool in [`app/agent/tools.py`](../agent/tools.py).

## Choosing a backend

**The defaults are fully local** — `VECTOR_STORE_PROVIDER=chroma` and
`EMBEDDING_PROVIDER=local`. No Azure account, no API keys, nothing extra to
install. Azure is opt-in.

| | `chroma` (default) | `azure` |
| --- | --- | --- |
| Setup | none — a directory | Azure resource + keys |
| Cost | free | per query/storage |
| Offline | yes | no |
| Scale | one machine | production-scale |
| Good for | learning, dev, demos | production |

Embeddings switch independently:

| | `local` (default) | `huggingface` | `azure` |
| --- | --- | --- | --- |
| Model | all-MiniLM-L6-v2 | any Hub model | text-embedding-ada-002 |
| Dimensions | 384 | usually 384–1024 | 1536 |
| Runtime | ONNX (ships with Chroma) | PyTorch | Azure API call |
| Install | nothing | `--group local-rag` (~4 GB) | nothing |
| Cost | free | free | per token |

`local` and `huggingface` can run the *same* model — the difference is the
runtime. Use `huggingface` when you want to try other models from the Hub via
`HUGGINGFACE_EMBEDDING_MODEL`; otherwise `local` is lighter and needs no PyTorch.

**One constraint:** `VECTOR_STORE_PROVIDER=azure` requires
`EMBEDDING_PROVIDER=azure`, because the Azure index schema fixes the vector width
at 1536. Local embeddings therefore need the Chroma store. You get a clear error
rather than a confusing failure if you mix them.

## Setup

Nothing to configure — just index the policy once:

```bash
uv run python scripts/index_lending_policy.py
```

That writes vectors to `backend/.chroma/` (git-ignored) and runs a smoke query.
The ~80 MB embedding model downloads on first use, then loads from disk.

Re-run any time to pick up policy changes. Chunk ids are stable, so re-ingesting
updates chunks in place instead of duplicating them. Add `--reset` when the
chunking itself changes, since a run producing fewer chunks would otherwise leave
stale ones behind.

To use hosted Azure AI Search instead, set both `VECTOR_STORE_PROVIDER=azure` and
`EMBEDDING_PROVIDER=azure`, then re-index with `--reset`. Each backend stores its
own vectors, so switching always means an ingest run.

## Things that will bite you

- **Switching embedding models silently returns nothing.** Chroma collections are
  named per model (`lending-policies-all-minilm-l6-v2-onnx`), so changing
  `EMBEDDING_PROVIDER` points at a *different, empty* collection. Re-run the
  ingest script. This is deliberate: a shared collection would either error on
  the dimension mismatch or return nonsense.
- **Placeholder credentials count as unset.** `.env.example` ships values like
  `https://<your-resource>.search.windows.net`. `is_configured()` in
  `app/core/config.py` treats anything still carrying `<...>` as missing, so you
  get a clear error instead of a DNS failure from inside an Azure SDK.
- **The bundled sample PDF is a scan.** It has no text layer, so pypdf extracts
  nothing and ingestion falls back to the built-in `SAMPLE_POLICY_TEXT`. Real
  OCR needs `POLICY_PDF_PARSER=azure_di`.
- **Chunk size is a trade-off.** Larger chunks give the LLM more context per hit
  but blur the embedding — a vector averaging four topics matches none of them
  well. 1000/200 is a reasonable default, not a law.
- **Retrieval quality is capped by chunking.** If an answer spans two chunks and
  only one is retrieved, the model sees half the story. That is what the overlap
  is for.

## Where to go next

The current setup is deliberately the simplest thing that works — pure vector
similarity, fixed `k=5`, no reranking. Natural next experiments: hybrid search
(keyword + vector), a reranker over the top 20 hits, metadata filters per policy
section, or making retrieval its own LangGraph node so you can grade results and
retry the query.
