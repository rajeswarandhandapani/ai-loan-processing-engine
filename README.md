# AI Loan Processing Engine

**Intelligent Small Business Loan Automation with Azure AI**

![Status](https://img.shields.io/badge/Status-Development-blue)
![Azure](https://img.shields.io/badge/Azure-AI-0078D4)
![Python](https://img.shields.io/badge/Backend-FastAPI-green)
![Angular](https://img.shields.io/badge/Frontend-Angular-red)

## 🚀 Overview
The **AI Loan Processing Engine** is a portfolio project demonstrating advanced cloud-native AI engineering skills (aligned with **Microsoft Certified: Azure AI Engineer Associate**).

It acts as a virtual loan officer that:
1.  **Interviews** applicants via a natural language chat.
2.  **Analyzes** uploaded financial documents (PDFs) using **Azure Document Intelligence**.
3.  **Validates** eligibility against complex internal policies using **Azure AI Search** (RAG).
4.  **Decides** on pre-qualification using **Azure OpenAI (GPT-4)**.

## 🏗 Architecture

The system is built using a microservices approach:

```mermaid
flowchart TB
    subgraph Client["🖥️ Client Layer"]
        Web["Angular 21 Web App<br/>Bootstrap 5"]
    end

    subgraph API["⚡ API Layer"]
        FastAPI["FastAPI Backend<br/>Python 3.11+"]
    end

    subgraph AI["🤖 AI Orchestration"]
        Agent["LangChain Agent"]
    end

    subgraph Azure["☁️ Azure AI Services"]
        DI["📄 Document Intelligence<br/>PDF Extraction"]
        Lang["💬 AI Language<br/>Entity & Sentiment"]
        Search["🔍 AI Search<br/>RAG Policy Lookup"]
        OpenAI["🧠 Azure OpenAI<br/>GPT-4o Reasoning"]
    end

    subgraph Data["💾 Data Layer"]
        Storage["Blob Storage"]
        DB["SQLite / Cosmos DB"]
    end

    Web -->|HTTP/REST| FastAPI
    FastAPI -->|Orchestrate| Agent
    Agent -->|Extract| DI
    Agent -->|Analyze| Lang
    Agent -->|Query| Search
    Agent -->|Synthesize| OpenAI
    FastAPI -->|Store Files| Storage
    FastAPI -->|Persist State| DB

    style Client fill:#e3f2fd,stroke:#1976d2
    style API fill:#e8f5e9,stroke:#388e3c
    style AI fill:#fff3e0,stroke:#f57c00
    style Azure fill:#fce4ec,stroke:#c2185b
    style Data fill:#f3e5f5,stroke:#7b1fa2
```

> 📖 *See [docs/architecture.md](docs/architecture.md) for detailed component descriptions*

## 🛠 Tech Stack
- **Cloud:** Microsoft Azure
- **AI Services:**
  - **Azure OpenAI:** GPT-4o for reasoning and conversation.
  - **Azure Document Intelligence:** Extracting data from Bank Statements/Invoices.
  - **Azure AI Search:** Vector-based knowledge retrieval for policy documents.
  - **Azure AI Language:** Sentiment analysis and entity extraction.
- **Backend:** Python, FastAPI, Pydantic.
- **Frontend:** Angular, TypeScript, RxJS.

## 📂 Project Structure
```
ai-loan-processing-engine/
├── backend/           # Python FastAPI Application
├── frontend/          # Angular Web Application
├── docs/              # Documentation & Design
└── README.md          # You are here
```

## 🚦 Getting Started

### Prerequisites
- Azure Subscription (Free Tier works)
- Python 3.11+
- Node.js 18+
- npm 9+

### Installation

```bash
# Clone the repository
git clone https://github.com/rajeswarandhandapani/ai-loan-processing-engine.git
cd ai-loan-processing-engine
```

### 🔧 Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Azure credentials

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

> 🌐 Backend API will be available at: `http://localhost:8000`  
> 📚 API Docs (Swagger): `http://localhost:8000/docs`

### 🎨 Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

> 🌐 Frontend will be available at: `http://localhost:4200`

### 🚀 Quick Start (Both Services)

```bash
# Terminal 1 - Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && npm start
```

### Azure Configuration

Follow the [Azure Manual Setup Guide](docs/azure-manual-setup.md) to provision required Azure resources and configure your `.env` file.

## 📅 Development Plan
This project is being built over 4 weeks. See the [Implementation Plan](docs/implementation-plan.md) for details.

---
*Created by [Rajeswaran Dhandapani](https://rajeswarandhandapani.com)*
