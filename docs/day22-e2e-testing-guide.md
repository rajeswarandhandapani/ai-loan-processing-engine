# Day 22: End-to-End Testing Guide

## Overview
This guide covers the "Happy Path" end-to-end testing for the AI Loan Processing Engine: **Upload → Chat → Approval**.

## Prerequisites

### 1. Start Backend Server
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
Verify: http://localhost:8000/docs (Swagger UI)

### 2. Start Frontend Server
```bash
cd frontend
npm start
```
Verify: http://localhost:4200

### 3. Ensure Azure Services are Running
- Azure OpenAI (GPT-4o)
- Azure Document Intelligence
- Azure AI Search (with indexed lending policy)
- Azure AI Language

---

## Sample Test Documents

Located in `backend/tests/sample_data/`:

| Document | Path | Purpose |
|----------|------|---------|
| Bank Statement | `bank_statements/acme_business_bank_statement.pdf` | Shows business cash flow, revenue deposits |
| Invoice #1 | `invoices/acme_invoice_001.pdf` | $25,000 consulting invoice |
| Invoice #2 | `invoices/acme_invoice_002.pdf` | $42,500 development invoice |
| P&L Statement | `financial_statements/acme_profit_loss_2024.pdf` | Annual revenue $1.55M, net income $183K |
| Balance Sheet | `financial_statements/acme_balance_sheet_2024.pdf` | Assets, liabilities, equity |
| Receipt | `receipts/acme_receipt_001.pdf` | Office supplies purchase |

### Converting HTML to PDF
```bash
cd backend/tests/sample_data
python convert_to_pdf.py
```
Or manually: Open HTML in browser → Print → Save as PDF

---

## Happy Path Test Scenarios

### Scenario 1: Qualified Business Loan Application

**Test Case:** Acme Tech Solutions LLC applies for a $150,000 business expansion loan.

**Business Profile (from sample documents):**
- Company: Acme Tech Solutions LLC
- Location: Austin, TX
- EIN: 84-1234567
- Annual Revenue: $1,550,000 (2024 projected)
- Net Income: $183,750
- Time in Business: 3+ years
- Current Cash: $83,280
- Existing Debt: $125,000 business loan

#### Step 1: Upload Bank Statement
1. Navigate to http://localhost:4200
2. Click "Upload Document"
3. Select `acme_business_bank_statement.pdf`
4. Choose document type: **Bank Statement**
5. Click Upload

**Expected Result:**
- ✅ Upload success message
- ✅ Document appears in uploaded documents list
- ✅ Extracted data shows: Account holder, ending balance, transaction summary

#### Step 2: Initial Chat - Greeting
**User Message:**
```
Hi, I'm interested in applying for a business loan for my company.
```

**Expected Agent Response:**
- Greets the user professionally
- May ask about loan purpose or amount
- Should acknowledge any uploaded documents

#### Step 3: Chat - Loan Amount Inquiry
**User Message:**
```
I'd like to borrow $150,000 for business expansion. Is that possible?
```

**Expected Agent Response:**
- Uses `search_lending_policy` tool
- References policy limits ($10K - $500K)
- May mention loan-to-revenue ratio (max 3x annual revenue)
- Asks follow-up questions about business details

#### Step 4: Upload Additional Documents
1. Upload `acme_profit_loss_2024.pdf` (Financial Statement type)
2. Upload `acme_invoice_001.pdf` (Invoice type)

#### Step 5: Chat - Eligibility Check
**User Message:**
```
Based on my uploaded documents, do I qualify for the loan?
```

**Expected Agent Response:**
- Uses `get_analyzed_financial_documents_from_session` tool
- References specific data from documents:
  - Revenue: $1.55M annual
  - Positive cash flow
  - Existing business operations
- Uses `search_lending_policy` to check criteria:
  - ✅ Revenue > $100K (requirement met)
  - ✅ Time in business > 2 years
  - ✅ Loan amount < 3x revenue ($150K < $4.65M)
- Provides preliminary eligibility assessment

#### Step 6: Chat - Interest Rate Inquiry
**User Message:**
```
What interest rate would I get?
```

**Expected Agent Response:**
- Uses `search_lending_policy` tool
- Explains rate tiers based on credit score
- May ask about credit score if not provided

#### Step 7: Chat - Required Documents
**User Message:**
```
What other documents do I need to submit?
```

**Expected Agent Response:**
- Uses `search_lending_policy` tool
- Lists required documents from policy:
  - Business license
  - Tax returns (2 years)
  - Bank statements (12 months)
  - Personal identification
  - etc.

#### Step 8: Chat - Pre-Qualification Decision
**User Message:**
```
Based on everything, can you give me a pre-qualification decision?
```

**Expected Agent Response:**
- Summarizes all analyzed information
- Provides preliminary approval/pre-qualification
- Lists any conditions or additional requirements
- Explains next steps

---

### Scenario 2: Edge Case - Startup Business

**Test Case:** New business (< 2 years) applying for loan.

**User Messages:**
1. "I started my business 8 months ago. Can I get a loan?"
2. "My personal credit score is 750."
3. "I have $50,000 in savings I can put down."

**Expected Agent Behavior:**
- References startup policy exceptions
- Notes requirements: strong credit (720+), industry experience, down payment (20%+)
- May suggest alternative paths or smaller loan amounts

---

### Scenario 3: Policy Questions Only

**Test Case:** User asks policy questions without uploading documents.

**User Messages:**
1. "What's the minimum credit score needed?"
2. "What are the interest rates?"
3. "Can I use the loan for cryptocurrency trading?"

**Expected Agent Behavior:**
- Uses `search_lending_policy` for each question
- Provides accurate policy information
- For prohibited uses, clearly states restrictions

---

## API Testing with curl/Postman

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload?document_type=bank_statement&session_id=test-session-001" \
  -H "accept: application/json" \
  -F "file=@backend/tests/sample_data/bank_statements/acme_business_bank_statement.pdf"
```

### Chat Message
```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the loan eligibility requirements?",
    "session_id": "test-session-001"
  }'
```

### Get Document Types
```bash
curl http://localhost:8000/api/v1/documents/types
```

---

## Test Checklist

### Upload Flow
- [ ] PDF upload succeeds
- [ ] Document type selection works
- [ ] Progress indicator shows during upload
- [ ] Success/error messages display correctly
- [ ] Uploaded documents list updates
- [ ] Session ID properly links documents to chat

### Chat Flow
- [ ] Messages send successfully
- [ ] Agent responds within reasonable time (< 30s)
- [ ] Typing indicator shows while waiting
- [ ] Message history persists in session
- [ ] Agent uses appropriate tools based on context
- [ ] Responses are formatted properly (markdown)

### Tool Usage
- [ ] `search_lending_policy` - Returns relevant policy chunks
- [ ] `get_analyzed_financial_documents_from_session` - Retrieves uploaded docs
- [ ] `analyze_user_sentiment` - Detects user emotions
- [ ] `extract_entities` - Identifies key information

### Integration
- [ ] Frontend ↔ Backend communication works
- [ ] Session state maintained across requests
- [ ] Documents linked to correct chat session
- [ ] Error handling displays user-friendly messages

---

## Common Issues & Troubleshooting

### Issue: "Failed to process chat message"
**Cause:** Azure OpenAI connection issue
**Fix:** Check `.env` file has correct Azure OpenAI credentials

### Issue: Document upload fails
**Cause:** Azure Document Intelligence not configured
**Fix:** Verify `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` and `KEY` in `.env`

### Issue: Policy search returns empty
**Cause:** Azure AI Search index not populated
**Fix:** Run `python scripts/index_lending_policy.py`

### Issue: CORS errors in browser
**Cause:** Frontend URL not in allowed origins
**Fix:** Check `main.py` CORS middleware includes `http://localhost:4200`

### Issue: Session documents not found
**Cause:** Session ID mismatch between upload and chat
**Fix:** Ensure same session ID used for both operations

---

## Success Criteria for Day 22

✅ **All test scenarios pass without errors**
✅ **Happy path completes: Upload → Chat → Pre-qualification**
✅ **Agent correctly uses tools based on context**
✅ **Document data is accurately extracted and referenced**
✅ **Policy information is correctly retrieved**
✅ **User experience is smooth and professional**

---

## Next Steps (Day 23)
- Fix any bugs discovered during testing
- Improve agent prompt engineering based on response quality
- Add edge case handling for identified issues
