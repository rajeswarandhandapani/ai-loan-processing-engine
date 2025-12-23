# Azure Manual Setup Guide

This guide provides step-by-step instructions to set up the necessary Azure resources using the Azure Portal.

## Prerequisites
1. **Azure Account:** You need an active Azure subscription. (Free Tier works for most services).
2. **Resource Group:** Create a new Resource Group named `rg-loan-engine-dev-001`.

---

## 1. Azure OpenAI Service
*Note: Access to Azure OpenAI requires a separate application approval.*

1. **Search:** "Azure OpenAI" in the top search bar.
2. **Create:** Click "Create".
   - **Region:** `East US` or `Sweden Central` (regions with GPT-5 capacity).
   - **Name:** `oai-loan-engine-dev`.
   - **Pricing Tier:** Standard S0.
3. **Deploy Models:**
   - Go to "Model deployments" -> "Manage deployments" (opens Azure OpenAI Studio).
   - **Deploy:** `gpt-5` or `gpt-4o` (Name it: `gpt-5-deployment`).
   - **Deploy:** `text-embedding-ada-002` (Name it: `text-embedding-deployment`).
4. **Get Keys:** Go back to the Azure Portal resource -> "Keys and Endpoint". Save `KEY 1` and `Endpoint`.

---

## 2. Azure Document Intelligence (formerly Form Recognizer)
1. **Search:** "Document Intelligence".
2. **Create:** Click "Create".
   - **Region:** Same as Resource Group.
   - **Name:** `doc-loan-engine-dev`.
   - **Pricing Tier:** Free F0 (if available) or Standard S0.
3. **Get Keys:** Go to "Keys and Endpoint". Save `KEY 1` and `Endpoint`.

---

## 3. Azure AI Search (formerly Cognitive Search)
1. **Search:** "AI Search".
2. **Create:** Click "Create".
   - **Region:** Same as Resource Group.
   - **Name:** `search-loan-engine-dev`.
   - **Pricing Tier:** Free (limited to 1 free search service per subscription) or Basic.
3. **Get Keys:** Go to "Keys" -> "Primary admin key". Save `Key` and `Url`.

---

## 4. Azure AI Language Service
1. **Search:** "Language".
2. **Create:** Click "Create".
   - **Select:** "Language Service" (Custom question answering & Text Analytics).
   - **Name:** `lang-loan-engine-dev`.
   - **Pricing Tier:** Free F0 (if available) or Standard S.
3. **Get Keys:** Go to "Keys and Endpoint". Save `KEY 1` and `Endpoint`.

---

## 5. Storage Account (Optional for Dev, Required for Prod)
1. **Search:** "Storage accounts".
2. **Create:** Click "Create".
   - **Name:** `stloanenginedev001` (must be globally unique).
   - **Redundancy:** LRS (Locally-redundant storage) - Cheapest option.
3. **Containers:** Go to "Data storage" -> "Containers". Create a container named `documents`.

---

## Configuration Summary (.env file)
Once created, populate your backend `.env` file with these values:

```ini
# Azure OpenAI
AZURE_OPENAI_ENDPOINT="https://oai-loan-engine-dev.openai.azure.com/"
AZURE_OPENAI_API_KEY="<YOUR_KEY>"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-5-deployment"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-deployment"

# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://doc-loan-engine-dev.cognitiveservices.azure.com/"
AZURE_DOCUMENT_INTELLIGENCE_KEY="<YOUR_KEY>"

# Azure AI Search
AZURE_SEARCH_SERVICE_ENDPOINT="https://search-loan-engine-dev.search.windows.net"
AZURE_SEARCH_ADMIN_KEY="<YOUR_KEY>"

# Azure AI Language
AZURE_LANGUAGE_ENDPOINT="https://lang-loan-engine-dev.cognitiveservices.azure.com/"
AZURE_LANGUAGE_KEY="<YOUR_KEY>"
```
