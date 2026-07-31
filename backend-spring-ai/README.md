# backend-spring-ai

A Spring Boot 4 + Spring AI 2 implementation of the AI Loan Processing Engine backend. It serves
the same HTTP API as the Python/FastAPI backend in [`../backend`](../backend), so the Angular
frontend can talk to either one on port 8000 — run one at a time.

This is not a line-by-line port. It is written the way a Spring application would normally be
written, and leans on Spring AI's auto-configuration wherever one exists.

## What the agent does

A loan-officer assistant that interviews an applicant, answers policy questions from a vector
index, reads documents the user uploaded during the conversation, and issues a pre-qualification
decision. The behaviour lives in
[`prompts/loan-officer-system-prompt.md`](src/main/resources/prompts/loan-officer-system-prompt.md) —
the prompt is the spec.

## Requirements

Java 25, Maven 3.9+, and an Azure OpenAI (Foundry) deployment. Azure Document Intelligence is only
needed for document upload; everything else runs without it.

## Running

```bash
cp src/main/resources/application-local.yml.example src/main/resources/application-local.yml
# fill in your endpoint, key and deployment name

mvn spring-boot:run -Dspring-boot.run.profiles=ingest   # one-time: build the policy index
mvn spring-boot:run                                      # serve on :8000
mvn test
```

Then start the frontend (`cd ../frontend && npm start`) and open http://localhost:4200.

The first run downloads the local ONNX embedding model (~90MB), so it takes a minute.

Re-run the ingest profile after editing the policy. Add `-Dspring-boot.run.arguments=--reset` to
drop the previous vectors first — needed only when the policy shrinks, since chunk ids are stable
and otherwise overwrite in place.

## How it fits together

```
chat/       ChatController -> ChatService -> ChatClient (+ ChatMemory, + tools)
document/   DocumentController -> DocumentAnalysisService (Azure Document Intelligence)
            SessionDocumentService  - per-conversation uploads
            DocumentTool            - @Tool the agent calls to read them
rag/        PolicyIngestionService  - read -> split -> embed -> store   (offline)
            PolicySearchTool        - @Tool the agent calls to search   (per request)
            VectorStoreConfig       - the one hand-written bean
config/     WebConfig (CORS), AzureProperties
common/     GlobalExceptionHandler (RFC 9457 ProblemDetail), MetaController
```

### The agent is a ChatClient, not a graph

[`ChatService`](src/main/java/com/rajes/loanengine/chat/ChatService.java) is the whole agent. Spring
AI auto-registers a `ToolCallingAdvisor`, so a `ChatClient` with `.tools(...)` attached already *is*
the reason-act loop: it keeps calling the model and running the tools it asks for until the model
answers in prose. `MessageChatMemoryAdvisor` replays earlier turns, keyed by the client-supplied
session id.

The session id reaches `DocumentTool` through `ToolContext`, not as a tool argument. Spring AI hides
`ToolContext` parameters from the schema sent to the model, so the model cannot ask for a different
user's session.

### Retrieval is a tool, not an advisor

Spring AI ships `QuestionAnswerAdvisor`, which retrieves on *every* request. This app makes search a
`@Tool` instead, so the model decides when the policy is relevant — it skips retrieval on
"hello" and uses it for "what credit score do I need?", which is what the system prompt asks for.

### Almost everything is auto-configured

`ChatClient.Builder`, the chat model, the embedding model, `ChatMemory`, the `ToolCallingAdvisor`
and the Azure AI Search store all come from starters. The single hand-written bean is
`SimpleVectorStore` in [`VectorStoreConfig`](src/main/java/com/rajes/loanengine/rag/VectorStoreConfig.java),
because it has no starter of its own.

## Swapping providers

| Change | How |
|---|---|
| Anthropic instead of Azure OpenAI | `--spring.profiles.active=anthropic` + `ANTHROPIC_API_KEY` |
| Azure AI Search instead of the local store | `spring.ai.vectorstore.type=azure` + `spring.ai.vectorstore.azure.*` |
| Azure embeddings instead of local ONNX | `spring.ai.model.embedding=openai` + `spring.ai.openai.embedding.*` |

`AzureVectorStoreAutoConfiguration` is `matchIfMissing=true`, which is why `application.yml` always
states `spring.ai.vectorstore.type` explicitly — leaving it unset would activate the Azure store.

Azure AI Search indexes are fixed at 1536 dimensions, so pair it with Azure embeddings
(`text-embedding-ada-002`), not the 384-dimension local model.

## Notes on the Azure OpenAI configuration

Spring AI 2.0 removed the separate Azure OpenAI module (`spring-ai-starter-model-azure-openai` no
longer exists). Azure is reached through the OpenAI client instead. Two things are easy to get
wrong:

- **Use the v1 endpoint**, i.e. `base-url: <endpoint>/openai/v1` with the deployment name as
  `spring.ai.openai.chat.model`. The `microsoft-foundry: true` mode targets the legacy
  `/openai/deployments/{name}/...` path, which Foundry resources answer with **404**. The v1
  endpoint accepts the resource key as a bearer token, which is what this client sends.
- **`max-completion-tokens`, not `max-tokens`** — current models reject the older parameter with a
  400.

## API

Unchanged from the Python backend, because the frontend is hardcoded to it.

| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/chat/` | `{message, session_id}` → `{message, session_id}`. Trailing slash matters. |
| GET | `/api/v1/chat/health` | |
| POST | `/api/v1/documents/upload` | multipart `file`; `document_type` and `session_id` are **query** params |
| GET | `/api/v1/documents/types` | |
| GET | `/health`, `/` | |

Two deliberate quirks, both required by the existing client:

- `POST /api/v1/chat/` is mapped to both `""` and `"/"`, because Spring Framework 7 no longer
  matches trailing slashes implicitly.
- A failed document **analysis** returns HTTP 200 with `success: false` and an `error` string; the
  frontend shows it inline in the chat. Validation failures (bad type, too large) still return
  400/413.

Errors use Spring's `ProblemDetail` (RFC 9457), whose `detail` field is exactly what the Angular
client reads off an error response.

## Differences from the Python backend

- **Scope**: no Azure AI Language sentiment/entity tools, and no on-disk caching of Document
  Intelligence results.
- **Chunking**: `TokenTextSplitter` counts tokens where the Python pipeline counted characters, so
  chunk boundaries differ. `app.rag.chunk-size` is in tokens.
- **Local vector store**: `SimpleVectorStore` with JSON persistence rather than ChromaDB. The Java
  Chroma client needs a running Chroma server, whereas Python's is in-process.
- **Upload size caps**: the per-type caps are mutually exclusive here. In the Python version a PDF
  between 10MB and 15MB passes the PDF check and is then rejected by a generic 10MB cap, making the
  advertised 15MB limit unreachable.

For the Python side, see [`../docs/backend-guide-for-java-developers.md`](../docs/backend-guide-for-java-developers.md).
