# Implementation Plan: 4 Weeks (1 Hour/Day)

## Week 1: Foundation & AI Service Setup
**Goal:** Get all Azure resources running and verify connectivity with simple Python scripts.

- [x] **Day 1:** Create Azure Account & Resource Group. Provision **Azure OpenAI** and **Azure Document Intelligence**.
- [ ] **Day 2:** Initialize Git repo, project structure, and Python virtual environment. Install SDKs.
- [ ] **Day 3:** **Script 1:** Write a Python script to upload a sample PDF to **Document Intelligence** and print extraction results.
- [ ] **Day 4:** Provision **Azure AI Search** and **Azure AI Language**. Save all keys to a local `.env` file.
- [ ] **Day 5:** **Script 2:** Write a Python script to index a sample "Lending Policy" PDF into **Azure AI Search**.
- [ ] **Day 6:** **Script 3:** Write a Python script to query **Azure OpenAI** (Hello World chat).
- [ ] **Day 7:** Buffer day / Review & Organize code.

## Week 2: Backend Development (FastAPI)
**Goal:** Build the core API that orchestrates the AI services.

- [ ] **Day 8:** Setup FastAPI skeleton (main.py, routers). Create `/health` endpoint.
- [ ] **Day 9:** Create `/upload` endpoint. Accept PDF file, save locally, run Document Intelligence, return JSON.
- [ ] **Day 10:** Implement **LangChain/Semantic Kernel** basic agent. Setup state management (in-memory dict).
- [ ] **Day 11:** Integrate **AI Search (RAG)** tool into the Agent. Allow Agent to query policy.
- [ ] **Day 12:** Integrate **AI Language** service for sentiment analysis on user input.
- [ ] **Day 13:** Create `/chat` endpoint. Connect User Message -> Agent -> Response.
- [ ] **Day 14:** Testing: Use Postman/curl to simulate a full conversation flow.

## Week 3: Frontend Development (Angular)
**Goal:** Build a clean, professional UI for the loan applicant.

- [ ] **Day 15:** Initialize Angular project (`ng new`). Install Bootstrap (`npm install bootstrap`).
- [ ] **Day 16:** Create Layout (Header, Footer, Sidebar). Create `LoanApplicationComponent`.
- [ ] **Day 17:** Build **File Upload Component**. Integrate with `/upload` API. Show progress bar.
- [ ] **Day 18:** Build **Chat Component**. Display user vs. agent messages bubbles.
- [ ] **Day 19:** Integrate `/chat` API. Handle loading states (typing indicators).
- [ ] **Day 20:** Add "Dashboard View": Visualize extracted data (e.g., Revenue Chart) using a simple chart library.
- [ ] **Day 21:** Polish UI: Add easy error handling (toasts) and gradient styling matching the portfolio.

## Week 4: Integration & Polish
**Goal:** Connect the pieces, fix bugs, and prepare for portfolio showcase.

- [ ] **Day 22:** End-to-End testing: Run through the "Happy Path" (Upload -> Chat -> Approval).
- [ ] **Day 23:** Fix bugs found during testing. Improve Agent prompt engineering (system instructions).
- [ ] **Day 24:** Add **README.md** with screenshots and setup instructions.
- [ ] **Day 25:** Create a short **Demo Video** (OBS Studio / Loom).
- [ ] **Day 26:** Cleanup code (add comments, type hints, remove unused imports).
- [ ] **Day 27:** (Optional) Deploy Backend to Azure Container Apps or Render.
- [ ] **Day 28:** (Optional) Deploy Frontend to GitHub Pages or Azure Static Web Apps.
- [ ] **Day 29:** Final Portfolio Update: Add project link to your main website.
- [ ] **Day 30:** Celebrate! Post on LinkedIn.
