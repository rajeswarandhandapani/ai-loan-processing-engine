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
- **Frontend:** Angular 17 + Bootstrap 5 (User-facing portal).
- **Backend:** Python FastAPI (Orchestration API).
- **AI Core:** LangChain agent coordinating Azure Cognitive Services.

*(See [docs/architecture.md](docs/architecture.md) for the detailed diagram)*

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
1.  **Prerequisites:**
    - Azure Subscription (Free Tier works).
    - Python 3.11+
    - Node.js 18+
2.  **Setup:**
    - Follow the [Azure Manual Setup Guide](docs/azure-manual-setup.md) to provision resources.
    - Clone the repo.
    - Configure `.env` in the `backend` folder.

## 📅 Development Plan
This project is being built over 4 weeks. See the [Implementation Plan](docs/implementation-plan.md) for details.

---
*Created by [Rajeswaran Dhandapani](https://rajeswarandhandapani.com)*
