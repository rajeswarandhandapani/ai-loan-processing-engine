# System Architecture: AI Loan Processing Engine

## Overview
The **AI Loan Processing Engine** is an intelligent, self-service platform designed to automate small business loan applications. It leverages Azure AI services to act as a virtual loan officer, capable of interviewing applicants, analyzing financial documents, validating compliance against policy manuals, and providing instant pre-qualification decisions.

## High-Level Architecture

```mermaid
graph TD
    subgraph "Client Layer"
        Web[Angular Web App]
    end

    subgraph "API Layer"
        API[FastAPI Backend]
    end

    subgraph "AI Orchestration Layer"
        Agent[AI Agent (LangChain)]
    end

    subgraph "Azure AI Services"
        DI[Azure Document Intelligence]
        Lang[Azure AI Language]
        Search[Azure AI Search]
        OpenAI[Azure OpenAI (GPT-4)]
    end

    subgraph "Data Layer"
        Storage[Azure Blob Storage]
        DB[SQLite / Cosmos DB]
    end

    Web -->|HTTP Requests| API
    API -->|Orchestration| Agent
    
    Agent -->|Extract Data| DI
    Agent -->|Analyze Text| Lang
    Agent -->|Retrieve Policy| Search
    Agent -->|Synthesize Response| OpenAI
    
    API -->|Store Files| Storage
    API -->|Persist State| DB
```

## Core Components

### 1. Frontend (Client Layer)
- **Framework:** Angular 17+
- **Styling:** Bootstrap 5 CSS Only (No JavaScript Components)
- **Key Features:**
  - Interactive Chat Interface for the loan interview (using Angular for interactivity).
  - File Upload Component with progress tracking (Angular-based).
  - Dashboard displaying application status and extracted data.
  - Responsive design for desktop and tablet.
  - Custom Angular components for modals, dropdowns, and other UI interactions.

### 2. Backend (API Layer)
- **Framework:** Python FastAPI
- **Runtime:** Python 3.10+
- **Key Responsibilities:**
  - **REST API:** Endpoints for chat, document upload, and status checks.
  - **Session Management:** Tracking user conversation state.
  - **File Handling:** Securely receiving and storing PDFs.

### 3. AI Agent (Orchestration Layer)
- **Framework:** LangChain / Semantic Kernel
- **Logic:**
  - **Router:** Determines if the user is asking a question, uploading a doc, or ready for a decision.
  - **Tools:** Defined interfaces to call Azure services (e.g., `analyze_document`, `search_policy`, `check_sentiment`).

### 4. Azure AI Services Integration

| Service | Usage Scenario |
|---------|----------------|
| **Azure Document Intelligence** | **Input:** PDF Bank Statements, Tax Forms, Invoices.<br>**Output:** JSON data (Revenue, Expenses, Dates).<br>**Model:** Pre-built Invoice/Receipt models + Layout model. |
| **Azure AI Language** | **Input:** User chat messages.<br>**Output:** Entities (Loan Amount, Business Type), Sentiment (Frustration), PII Redaction. |
| **Azure AI Search** | **Input:** Lending Policy PDF (indexed).<br>**Output:** Relevant policy sections (RAG Pattern).<br>**Features:** Keyword Search + Semantic Ranking. |
| **Azure OpenAI** | **Input:** Context from all above.<br>**Output:** Natural language responses, decision logic, data summarization. |

## Data Flow Scenarios

### Scenario A: Document Upload & Analysis
1. User uploads `bank_statement.pdf` via Angular UI.
2. FastAPI saves file to Blob Storage (or local temp).
3. Agent triggers **Azure Document Intelligence** to extract table data.
4. Extracted data (e.g., "Total Deposits: $50,000") is stored in the session state.
5. Agent uses **Azure OpenAI** to summarize the financial health back to the user.

### Scenario B: Policy Validation (RAG)
1. Agent analyzes extracted data: "Debt-to-Income Ratio is 45%".
2. Agent queries **Azure AI Search**: "What is the max DTI for retail businesses?".
3. **Azure AI Search** returns relevant chunks from "Lending_Policy_2025.pdf".
4. Agent uses **Azure OpenAI** to compare extracted DTI (45%) vs Policy Limit (40%).
5. Agent generates response: "Your DTI is slightly high based on section 4.2..."

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.11 |
| **Backend** | FastAPI, Uvicorn |
| **Frontend** | Angular, TypeScript, Bootstrap |
| **AI SDKs** | `azure-ai-formrecognizer`, `azure-search-documents`, `azure-ai-textanalytics`, `openai`, `langchain` |
| **Database** | SQLite (Dev) / Azure Cosmos DB (Prod) |
| **Storage** | Local Filesystem (Dev) / Azure Blob Storage (Prod) |
