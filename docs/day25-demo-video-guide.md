# Day 25: Demo Video Recording Guide

## Overview
This guide provides step-by-step instructions to record a professional demo video showcasing the AI Loan Processing Engine with **3 distinct scenarios**:

| Scenario | Company | Expected Decision | Duration |
|----------|---------|-------------------|----------|
| 1 | **Acme Tech Solutions** | ✅ PRE-APPROVED | ~3 min |
| 2 | **Sunrise Bakery Co** | ⚠️ CONDITIONALLY APPROVED | ~3 min |
| 3 | **Nexus Digital Startup** | ❌ NOT ELIGIBLE | ~3 min |

**Total Video Duration:** ~10-12 minutes (including intro/outro)

---

## Prerequisites

### 1. Recording Software
Choose one:
- **OBS Studio** (Free, full-featured) - https://obsproject.com/
- **Loom** (Easy, cloud-based) - https://loom.com/
- **Camtasia** (Professional, paid)

### 2. Start Services

**Terminal 1 - Backend:**
```bash
cd /home/rajes/proworkspace/ai_portfolio_project/ai-loan-processing-engine/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /home/rajes/proworkspace/ai_portfolio_project/ai-loan-processing-engine/frontend
npm start
```

**Verify:**
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:4200

### 3. Sample Documents Location
All PDF documents are ready in:
```
backend/tests/sample_data/companies/
├── acme_tech_solutions/     # Scenario 1: APPROVE
├── sunrise_bakery/          # Scenario 2: CONDITIONAL
└── nexus_digital_startup/   # Scenario 3: NOT ELIGIBLE
```

### 4. Browser Setup
- Use Chrome or Firefox
- Set browser zoom to **100%**
- Resolution: **1920x1080** recommended
- Clear any personal bookmarks from view
- Close unnecessary tabs

---

## Recording Settings (OBS Studio)

### Video Settings
- **Resolution:** 1920x1080
- **FPS:** 30
- **Format:** MP4 (H.264)

### Audio Settings
- Use a good microphone (external USB recommended)
- Test audio levels before recording
- Minimize background noise

### Screen Capture
- Capture browser window only (not full screen)
- Hide taskbar if possible

---

## Video Script & Scenarios

### Introduction (~30 seconds)

**Script:**
> "Welcome to the AI Loan Processing Engine demo. This is an intelligent small business loan automation system powered by Azure AI services. I'll demonstrate three real-world scenarios: a fully approved loan, a conditional approval, and a rejection case. Let's begin."

---

## Scenario 1: Acme Tech Solutions (APPROVED)

### Company Profile
| Attribute | Value |
|-----------|-------|
| **Company** | Acme Tech Solutions LLC |
| **Industry** | Technology Consulting |
| **Location** | Austin, TX |
| **Founded** | March 2021 (3+ years) |
| **Annual Revenue** | $1,550,000 |
| **Net Income** | $183,750 (11.9% margin) |
| **Credit Score** | 762 (Excellent) |
| **Loan Request** | $150,000 |

### Documents to Upload
From `backend/tests/sample_data/companies/acme_tech_solutions/`:

| Order | File | Document Type |
|-------|------|---------------|
| 1 | `acme_business_bank_statement.pdf` | Bank Statement |
| 2 | `acme_profit_loss_2024.pdf` | Financial Statement |
| 3 | `acme_balance_sheet_2024.pdf` | Financial Statement |
| 4 | `credit_report_summary.pdf` | Other |

### Step-by-Step Recording

#### Step 1.1: Clear Session
1. Refresh the browser (F5) to start fresh
2. Show the empty chat interface

**Narration:**
> "For our first scenario, we have Acme Tech Solutions, a well-established technology consulting company from Austin, Texas."

#### Step 1.2: Upload Bank Statement
1. Click the upload area or drag-drop
2. Select `acme_business_bank_statement.pdf`
3. Wait for processing to complete
4. **Pause to show extracted data**

**Narration:**
> "I'm uploading their business bank statement. Notice how the AI automatically extracts key information like account details and transaction summaries."

#### Step 1.3: Upload Financial Statements
1. Upload `acme_profit_loss_2024.pdf`
2. Upload `acme_balance_sheet_2024.pdf`
3. Show the document list growing

**Narration:**
> "Now I'll add their profit and loss statement and balance sheet. These show strong financials with over $1.5 million in annual revenue."

#### Step 1.4: Chat - Introduction
**Type in chat:**
```
Hi, I'm Michael Chen, owner of Acme Tech Solutions. I'd like to apply for a $150,000 business loan for expansion.
```

**Wait for response, then narrate:**
> "The AI agent greets the applicant and acknowledges the loan request."

#### Step 1.5: Chat - Eligibility Question
**Type in chat:**
```
Based on my uploaded documents, do I qualify for this loan?
```

**Wait for response, then narrate:**
> "The agent analyzes the uploaded documents and checks against our lending policies. Notice how it references specific data from the documents."

#### Step 1.6: Chat - Interest Rate
**Type in chat:**
```
My credit score is 762. What interest rate would I get?
```

**Wait for response, then narrate:**
> "With an excellent credit score of 762, the agent explains the favorable interest rate tier."

#### Step 1.7: Chat - Final Decision
**Type in chat:**
```
Can you give me a pre-qualification decision?
```

**Wait for response, then narrate:**
> "And here's the verdict - Acme Tech Solutions is PRE-APPROVED. The agent summarizes all the positive factors: strong revenue, excellent credit, adequate time in business, and healthy profit margins."

**Transition:**
> "That was our approval scenario. Now let's look at a more challenging case."

---

## Scenario 2: Sunrise Bakery (CONDITIONAL APPROVAL)

### Company Profile
| Attribute | Value |
|-----------|-------|
| **Company** | Sunrise Bakery Co LLC |
| **Industry** | Retail Bakery / Catering |
| **Location** | Boulder, CO |
| **Founded** | September 2019 (5+ years) |
| **Annual Revenue** | $668,000 |
| **Net Income** | $16,552 (2.5% margin) - **THIN** |
| **Credit Score** | 698 (Good) |
| **Existing Debt** | $134,100 |
| **Loan Request** | $75,000 |

### Documents to Upload
From `backend/tests/sample_data/companies/sunrise_bakery/`:

| Order | File | Document Type |
|-------|------|---------------|
| 1 | `bank_statement_nov_2024.pdf` | Bank Statement |
| 2 | `profit_loss_2024.pdf` | Financial Statement |
| 3 | `balance_sheet_2024.pdf` | Financial Statement |
| 4 | `owner_credit_report.pdf` | Other |

### Step-by-Step Recording

#### Step 2.1: Clear Session
1. **Refresh browser** to start a new session
2. Show empty interface

**Narration:**
> "Our second scenario is Sunrise Bakery, a local bakery in Boulder, Colorado. They've been in business for 5 years but have faced some challenges."

#### Step 2.2: Upload Documents
1. Upload `bank_statement_nov_2024.pdf`
2. Upload `profit_loss_2024.pdf`
3. Upload `balance_sheet_2024.pdf`
4. Upload `owner_credit_report.pdf`

**Narration:**
> "I'm uploading their financial documents. The AI will analyze these and identify some concerns."

#### Step 2.3: Chat - Introduction
**Type in chat:**
```
Hello, I'm Maria Rodriguez, owner of Sunrise Bakery. We're looking for a $75,000 loan to open a second location.
```

**Wait for response.**

#### Step 2.4: Chat - Business Details
**Type in chat:**
```
We've been in business for 5 years, but 2023 was tough. We just turned profitable again this year.
```

**Wait for response, then narrate:**
> "The agent acknowledges the business history and shows empathy for the challenges faced."

#### Step 2.5: Chat - Eligibility Check
**Type in chat:**
```
Based on my documents, can I get approved for the loan?
```

**Wait for response, then narrate:**
> "Watch how the agent identifies both positive and concerning factors. The thin profit margin and existing debt are flagged as issues."

#### Step 2.6: Chat - Final Decision
**Type in chat:**
```
What's your final assessment?
```

**Wait for response, then narrate:**
> "The result is CONDITIONAL APPROVAL. The agent lists specific conditions: collateral requirements, a detailed business plan, proof of cash reserves, and possibly a higher interest rate. This is a realistic outcome for a business with borderline financials."

**Transition:**
> "Now let's see what happens when a business doesn't meet the basic requirements."

---

## Scenario 3: Nexus Digital Startup (NOT ELIGIBLE)

### Company Profile
| Attribute | Value |
|-----------|-------|
| **Company** | Nexus Digital Solutions Inc |
| **Industry** | AI/SaaS Startup |
| **Location** | San Jose, CA |
| **Founded** | April 2024 (**8 months only**) |
| **YTD Revenue** | $78,900 |
| **Net Loss** | ($137,700) - **SIGNIFICANT** |
| **Cash Balance** | $6,170 - **CRITICAL** |
| **Credit Score** | 745 (Very Good) |
| **Loan Request** | $100,000 |

### Documents to Upload
From `backend/tests/sample_data/companies/nexus_digital_startup/`:

| Order | File | Document Type |
|-------|------|---------------|
| 1 | `bank_statement_nov_2024.pdf` | Bank Statement |
| 2 | `profit_loss_2024.pdf` | Financial Statement |
| 3 | `balance_sheet_2024.pdf` | Financial Statement |
| 4 | `owner_credit_report.pdf` | Other |

### Step-by-Step Recording

#### Step 3.1: Clear Session
1. **Refresh browser** to start fresh
2. Show empty interface

**Narration:**
> "Our final scenario is Nexus Digital, an AI startup in San Jose. They're only 8 months old and burning cash fast."

#### Step 3.2: Upload Documents
1. Upload all 4 documents from the folder

**Narration:**
> "Their documents tell a challenging story - significant losses and limited runway."

#### Step 3.3: Chat - Introduction
**Type in chat:**
```
Hi, I'm Jason Park, founder of Nexus Digital Solutions. We're building an AI platform and need $100,000 to accelerate development.
```

**Wait for response.**

#### Step 3.4: Chat - Business Age
**Type in chat:**
```
We incorporated 8 months ago. I know we're new, but our technology is promising and I have a strong background - I worked at Google for 5 years.
```

**Wait for response, then narrate:**
> "The agent acknowledges the impressive background but notes the policy requirements."

#### Step 3.5: Chat - Eligibility Check
**Type in chat:**
```
I understand we're new, but my personal credit is 745 and I have $215,000 in personal savings. Does that help?
```

**Wait for response, then narrate:**
> "The agent considers these mitigating factors but explains the core policy constraints."

#### Step 3.6: Chat - Final Decision
**Type in chat:**
```
So what's the final verdict? Can we get approved?
```

**Wait for response, then narrate:**
> "The result is NOT ELIGIBLE. The agent clearly explains why: less than 2 years in business, negative cash flow, and operating losses. But notice - it also provides helpful alternatives like startup exception requirements, venture capital, or angel investors. This shows the AI being helpful even when delivering negative news."

---

## Conclusion (~30 seconds)

**Script:**
> "That concludes our demo of the AI Loan Processing Engine. We've seen how the system handles three real-world scenarios:
> - A strong business that gets immediate pre-approval
> - A borderline case that receives conditional approval with requirements
> - A startup that doesn't meet standard criteria but gets helpful guidance
>
> The system uses Azure AI services for document intelligence, policy retrieval via RAG, and natural language understanding to provide accurate, policy-compliant decisions.
>
> Thank you for watching!"

---

## Post-Recording Checklist

### Video Editing
- [ ] Trim any awkward pauses
- [ ] Add intro title card with project name
- [ ] Add outro with GitHub link and contact info
- [ ] Add captions (optional but recommended)
- [ ] Export at 1080p, H.264

### Suggested Title Card
```
AI Loan Processing Engine
Intelligent Small Business Loan Automation
Built with Azure AI | LangChain | Angular 21

github.com/rajeswarandhandapani/ai-loan-processing-engine
```

### Upload Destinations
- [ ] YouTube (unlisted or public)
- [ ] Loom (if recorded there)
- [ ] LinkedIn (native upload for better reach)
- [ ] Personal portfolio website

---

## Troubleshooting During Recording

### If Agent Takes Too Long (>30s)
- Wait patiently - DO NOT refresh mid-recording
- In post-editing, speed up the waiting period
- Mention: "The agent is analyzing the documents..."

### If Upload Fails
- Check backend logs for errors
- Verify Azure Document Intelligence credentials
- Restart backend if needed

### If Chat Errors
- Refresh and start that scenario over
- This is why we record scenarios separately

---

## Tips for Professional Video

1. **Practice Once** - Do a dry run without recording
2. **Speak Clearly** - Moderate pace, clear pronunciation
3. **Mouse Movements** - Slow, deliberate cursor movements
4. **Pause After Actions** - Give viewers time to see results
5. **Be Enthusiastic** - Show genuine interest in the demo
6. **Handle Errors Gracefully** - If something fails, explain and move on

---

## Quick Reference: Chat Messages

### Scenario 1 (Acme - APPROVE)
```
1. Hi, I'm Michael Chen, owner of Acme Tech Solutions. I'd like to apply for a $150,000 business loan for expansion.
2. Based on my uploaded documents, do I qualify for this loan?
3. My credit score is 762. What interest rate would I get?
4. Can you give me a pre-qualification decision?
```

### Scenario 2 (Sunrise - CONDITIONAL)
```
1. Hello, I'm Maria Rodriguez, owner of Sunrise Bakery. We're looking for a $75,000 loan to open a second location.
2. We've been in business for 5 years, but 2023 was tough. We just turned profitable again this year.
3. Based on my documents, can I get approved for the loan?
4. What's your final assessment?
```

### Scenario 3 (Nexus - NOT ELIGIBLE)
```
1. Hi, I'm Jason Park, founder of Nexus Digital Solutions. We're building an AI platform and need $100,000 to accelerate development.
2. We incorporated 8 months ago. I know we're new, but our technology is promising and I have a strong background - I worked at Google for 5 years.
3. I understand we're new, but my personal credit is 745 and I have $215,000 in personal savings. Does that help?
4. So what's the final verdict? Can we get approved?
```

---

## Success Criteria for Day 25

- [ ] All 3 scenarios recorded successfully
- [ ] Each scenario shows different outcome (Approve/Conditional/Reject)
- [ ] Agent uses document data in responses
- [ ] Agent references lending policies accurately
- [ ] Video is clear and professional
- [ ] Audio is audible and free of major noise
- [ ] Video uploaded to at least one platform

---

*Guide created: December 2024*
*Project: AI Loan Processing Engine*
