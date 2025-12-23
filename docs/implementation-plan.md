# Implementation Plan: 4 Weeks (1 Hour/Day)

## Week 1: Foundation & AI Service Setup
**Goal:** Get all Azure resources running and verify connectivity with simple Python scripts.

- [x] **Day 1:** Create Azure Account & Resource Group. Provision **Azure OpenAI** and **Azure Document Intelligence**.
- [x] **Day 2:** Initialize Git repo, project structure, and Python virtual environment. Install SDKs.
- [x] **Day 3:** **Script 1:** Write a Python script to upload a sample PDF to **Document Intelligence** and print extraction results.
- [x] **Day 4:** Provision **Azure AI Search** and **Azure AI Language**. Save all keys to a local `.env` file.
- [x] **Day 5:** **Script 2:** Write a Python script to index a sample "Lending Policy" PDF into **Azure AI Search**.
- [x] **Day 6:** **Script 3:** Write a Python script to query **Azure OpenAI** (Hello World chat).
- [x] **Day 7:** Buffer day / Review & Organize code.

## Week 2: Backend Development (FastAPI)
**Goal:** Build the core API that orchestrates the AI services.

- [x] **Day 8:** Setup FastAPI skeleton (main.py, routers). Create `/health` endpoint.
- [x] **Day 9:** Create `/upload` endpoint. Accept PDF file, save locally, run Document Intelligence, return JSON.
- [x] **Day 10:** Implement **LangChain**-based agent core (no tools yet). Define conversation memory and basic routing.
- [x] **Day 11:** Add agent tools for **Azure Document Intelligence** and **Azure AI Search**, plus in-memory session state.
- [x] **Day 12:** Implement **RAG flow** with Azure AI Search (index sample lending policy and retrieve relevant chunks). Wire into the agent as a tool.
- [x] **Day 13:** Integrate **Azure AI Language** (sentiment, entities) and finalize `/chat` endpoint (User Message -> Agent -> Response).
- [x] **Day 14:** Backend end-to-end testing using Postman/curl, plus basic error handling and logging for all core endpoints.

## Week 3: Frontend Development (Angular)
**Goal:** Build a clean, professional UI for the loan applicant.

- [x] **Day 15:** Initialize Angular project (`ng new`). Install Bootstrap CSS only (`npm install bootstrap bootstrap-icons`).
- [x] **Day 16:** Create Layout (Header, Footer, Sidebar). Create `LoanApplicationComponent`.
- [x] **Day 17:** Build **File Upload Component**. Integrate with `/upload` API. Show progress bar using Angular animations.
- [x] **Day 18:** Build **Chat Component**. Display user vs. agent messages bubbles. Use Angular for scroll behavior and typing indicators.
- [x] **Day 19:** Integrate `/chat` API. Handle loading states (typing indicators) with Angular reactive programming.
- [x] **Day 20:** Add "Dashboard View": Visualize extracted data (e.g., Revenue Chart) using a simple chart library.
- [x] **Day 21:** UI polish & buffer: Complete redesign to minimal single-page layout. Removed unnecessary components (sidebar, footer, dashboard with charts). Created clean two-column layout with file upload + chat interface.

## Week 4: Integration & Polish
**Goal:** Connect the pieces, fix bugs, and prepare for portfolio showcase.

- [x] **Day 22:** End-to-End testing: Run through the "Happy Path" (Upload -> Chat -> Approval).
- [x] **Day 23:** Fix bugs found during testing. Improve Agent prompt engineering (system instructions).
- [ ] **Day 24:** Add **README.md** with screenshots and setup instructions.
- [ ] **Day 25:** Create a short **Demo Video** (OBS Studio / Loom).
- [x] **Day 26:** Cleanup code (add comments, type hints, remove unused imports).
- [ ] **Day 27:** Deploy Backend to Azure Container Apps or Render (production-like environment for demo).
- [ ] **Day 28:** Deploy Frontend to GitHub Pages or Azure Static Web Apps and connect it to the live backend.
- [ ] **Day 29:** Final Portfolio Update: Add project link to your main website.
- [ ] **Day 30:** Celebrate! Post on LinkedIn.
