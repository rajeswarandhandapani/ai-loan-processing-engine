# Sample Company Documents for E2E Testing

This folder contains complete document packages for 3 fictional companies to test the loan approval flow.

## Test Scenarios Overview

| Company | Expected Decision | Key Issues |
|---------|-------------------|------------|
| **Acme Tech Solutions** | ✅ **PRE-APPROVED** | Strong financials, meets all criteria |
| **Sunrise Bakery Co** | ⚠️ **CONDITIONALLY APPROVED** | Good but thin margins, borderline DTI |
| **Nexus Digital Startup** | ❌ **NOT ELIGIBLE** | < 2 years, negative cash flow, losses |

---

## 1. Acme Tech Solutions LLC (APPROVE)

**Location:** `acme_tech_solutions/`

**Business Profile:**
- Industry: Technology Consulting / Software Development
- Location: Austin, TX
- EIN: 84-1234567
- Founded: March 2021 (3+ years)
- Owner: Michael Chen (100%)

**Key Financials:**
- Annual Revenue: $1,550,000 (2024 projected)
- Net Income: $183,750 (11.9% margin)
- Cash Balance: $83,280
- Existing Debt: $125,000 business loan
- Owner Credit Score: **762** (Excellent)

**Loan Request:** $150,000 for business expansion

**Why APPROVED:**
- ✅ Revenue > $100K minimum ($1.55M)
- ✅ Time in business > 2 years (3.5 years)
- ✅ Credit score > 650 (762)
- ✅ Positive cash flow
- ✅ Loan amount < 3x revenue
- ✅ Current ratio 2.53:1

**Documents:**
- `business_license.pdf` - TX LLC Certificate
- `bank_statement_*.pdf` - Nov 2024 statement
- `profit_loss_2024.pdf` - P&L with YoY comparison
- `balance_sheet_2024.pdf` - Current balance sheet
- `tax_return_2022.pdf` - Prior year tax return
- `tax_return_2023.pdf` - Most recent tax return
- `owner_personal_financial_statement.pdf` - Owner PFS
- `credit_report_summary.pdf` - Owner credit report
- `acme_invoice_001.pdf` - Sample customer invoice
- `acme_invoice_002.pdf` - Sample customer invoice

---

## 2. Sunrise Bakery Co LLC (CONDITIONAL)

**Location:** `sunrise_bakery/`

**Business Profile:**
- Industry: Retail Bakery / Wholesale / Catering
- Location: Boulder, CO
- EIN: 84-7823456
- Founded: September 2019 (5+ years)
- Owner: Maria Rodriguez (100%)

**Key Financials:**
- Annual Revenue: $668,000 (2024 projected)
- Net Income: $16,552 (2.5% margin) - **THIN**
- Cash Balance: $22,330
- Existing Debt: $134,100 (SBA loan + equipment)
- Owner Credit Score: **698** (Good)

**Loan Request:** $75,000 for second location expansion

**Why CONDITIONALLY APPROVED:**
- ✅ Revenue > $100K ($668K)
- ✅ Time in business > 2 years (5 years)
- ✅ Credit score > 650 (698)
- ⚠️ Thin profit margin (2.5%)
- ⚠️ Current ratio 1.16:1 (below 1.5 target)
- ⚠️ Recent loss in 2023 (just turned profitable)
- ⚠️ High existing debt load

**Conditions for Approval:**
1. Collateral required (equipment as security)
2. Detailed expansion business plan
3. 6-month cash reserve demonstration
4. Higher interest rate tier (Prime + 5-6%)

**Documents:**
- `business_license.pdf` - CO LLC Certificate
- `bank_statement_nov_2024.pdf` - Nov 2024 statement
- `profit_loss_2024.pdf` - P&L showing turnaround
- `balance_sheet_2024.pdf` - Current balance sheet
- `tax_return_2023.pdf` - Shows 2023 loss
- `owner_credit_report.pdf` - Owner credit (698)

---

## 3. Nexus Digital Solutions Inc (REJECT)

**Location:** `nexus_digital_startup/`

**Business Profile:**
- Industry: AI/SaaS Startup
- Location: San Jose, CA
- EIN: 88-4567890
- Founded: April 2024 (**8 months only**)
- Owner: Jason Park (Founder/CEO)

**Key Financials:**
- YTD Revenue: $78,900 (annualized ~$118K) - **BORDERLINE**
- Net Loss: ($137,700) - **SIGNIFICANT LOSSES**
- Cash Balance: $6,170 - **CRITICAL**
- Burn Rate: ~$17,200/month
- Owner Credit Score: **745** (Very Good)

**Loan Request:** $100,000 for product development

**Why NOT ELIGIBLE:**
- ❌ Time in business < 2 years (only 8 months)
- ❌ Negative cash flow (burning cash)
- ❌ Operating at significant loss
- ❌ Cash runway < 2 weeks
- ❌ Negative equity (insolvent on paper)
- ❌ Current ratio 0.44:1

**Mitigating Factors (for startup exception discussion):**
- ✅ Owner credit 745 (> 720 startup threshold)
- ✅ $215K personal liquid assets for guarantee
- ✅ Growing MRR (128% over 6 months)
- ✅ Strong founder background (ex-Google)

**Agent should explain:**
- Does not meet standard criteria
- Could discuss startup exception requirements
- Would need significant personal guarantee
- May suggest alternative funding (VC, angels)

**Documents:**
- `business_license.pdf` - CA Corp Certificate (8 months old)
- `bank_statement_nov_2024.pdf` - Shows cash struggles
- `profit_loss_2024.pdf` - Shows significant losses
- `balance_sheet_2024.pdf` - Shows negative equity
- `owner_credit_report.pdf` - Strong personal credit

---

## How to Use These Documents

### For E2E Testing:
1. Start backend: `uvicorn app.main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm start`
3. Upload documents from one company folder
4. Chat with agent about loan application
5. Verify agent gives correct decision

### Expected Agent Behavior:

**Acme Tech Solutions:**
```
User: "I'd like to apply for a $150,000 loan"
Agent: Reviews documents → "You're PRE-APPROVED for $150,000..."
```

**Sunrise Bakery:**
```
User: "Can I get a $75,000 expansion loan?"
Agent: Reviews documents → "You're CONDITIONALLY APPROVED, but we need..."
```

**Nexus Digital:**
```
User: "I need $100,000 for my startup"
Agent: Reviews documents → "Based on the policy, your business doesn't meet 
the 2-year requirement. However, there are startup exceptions if..."
```

---

## Document Checklist per Policy

| Document | Acme | Sunrise | Nexus |
|----------|------|---------|-------|
| Business License | ✅ | ✅ | ✅ |
| Bank Statements | ✅ | ✅ | ✅ |
| P&L Statement | ✅ | ✅ | ✅ |
| Balance Sheet | ✅ | ✅ | ✅ |
| Tax Returns (2 yr) | ✅ | ✅ (1 yr) | ❌ N/A |
| Owner Credit Report | ✅ | ✅ | ✅ |
| Personal Financial Statement | ✅ | ❌ | ❌ |
| Invoices/Contracts | ✅ | ❌ | ❌ |
