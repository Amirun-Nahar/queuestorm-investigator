# QueueStorm Investigator 🔍

An AI-powered, production-ready support-ticket analysis and routing engine built with FastAPI and OpenAI/Gemini. 

QueueStorm Investigator is designed to ingest customer complaints, autonomously cross-reference them with raw transaction histories, and output deterministic, strictly structured JSON data that can be consumed directly by downstream microservices.

---

## 🌟 Key Features

1. **Intelligent Case Classification**: Autonomously categorizes incoming tickets into scenarios such as `fraud_risk`, `phishing_or_social_engineering`, `account_takeover`, or `service_complaint`.
2. **Evidence Cross-Referencing**: Analyzes complex transaction histories against unstructured customer complaints to generate a forensic verdict (`consistent`, `inconsistent`, `insufficient_data`).
3. **Structured Outputs Enforcement**: Uses advanced JSON Schema enforcement to guarantee that the LLM returns 100% perfectly typed and structured JSON on every single request. No hallucinated schemas or missing fields.
4. **Post-Processing Safety Shield**: A robust, deterministic regex firewall that intercepts the AI's generated customer reply and strips out prohibited content—ensuring the AI never asks for a user's PIN, OTP, Password, CVV, and never makes unauthorized promises (e.g., "we will refund you").
5. **Human-in-the-Loop Triggers**: Automatically flags tickets for human review (`human_review_required: true`) if the AI's confidence score drops below 60% or if severe social engineering/phishing is detected.
6. **Mock Testing Environment**: Ships with an industry-standard `MOCK_AI` toggle for rapid CI/CD testing, allowing the entire API structure, data models, and safety shields to be tested instantly without consuming LLM quotas.

---

## 🤖 MODELS & AI Approach

For this investigator engine, we built a flexible, model-agnostic architecture, but we specifically chose **OpenAI's `gpt-4o-mini`** (or **Gemini 2.0 Flash**) as the core LLMs.

**Why these models?**
- **Structured Outputs / JSON Mode**: The prompt specifically requires returning a single JSON object. These models natively support JSON Schema parsing (e.g., via `client.beta.chat.completions.parse`), guaranteeing 100% adherence to our strict Pydantic response models.
- **Latency**: Support ticket routing systems must be fast. `gpt-4o-mini` and `gemini-2.0-flash` provide incredibly fast time-to-first-token (TTFT) while maintaining the complex reasoning capabilities needed to act as an investigator (comparing dates, amounts, and statuses).
- **Cost-Efficiency**: Given the volume of typical support tickets, smaller, highly-optimized reasoning models are the industry standard for classification and routing compared to massively expensive ultra-large models.

**The Prompting Approach**: We avoid simple "classification" prompts. Instead, the System Prompt forces the LLM to adopt the persona of an **investigator**. It is explicitly instructed to cross-reference the customer's text against timestamps and amounts in the transaction history *before* arriving at a classification or confidence score.

---

## 🏗️ Project Architecture

```text
User Request (JSON) -> FastAPI Endpoint -> Pydantic Schema Validation
                                                  |
                                                  v
   [AI Engine] <- (Prompt + Strict Schema) -> LLM (OpenAI / Gemini)
        |
        v
Safety Shield (Regex Firewall) -> Re-Validation (Pydantic) -> Final JSON Response
```

---

## 🚀 Quick Start Guide

### 1. Clone & Setup
```bash
git clone <repo-url>
cd queuestorm-investigator
python -m venv venv

# Activate the virtual environment:
# On Windows: venv\Scripts\activate
# On Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Edit the `.env` file and insert your API keys.

### 3. Start the Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
*The interactive Swagger UI dashboard is instantly available at: [http://localhost:8000/docs](http://localhost:8000/docs)*

---

## 🧪 Running the Test Suite

The project includes a comprehensive end-to-end testing suite (`test_full.py`) that tests schema validation, the regex safety shield, and various live AI analysis behaviors (fraud, phishing, missing data).

If you do not want to consume API credits, simply enable the mock environment:
1. Set `MOCK_AI=true` in your `.env` file.
2. Ensure the server is running (`uvicorn main:app`).
3. Run the tests in a new terminal:
```bash
python test_full.py
```

---

## 🐳 Docker Deployment

You can run the entire API in an isolated container.

### 1. Build the Image
```bash
docker build -t queuestorm-investigator .
```

### 2. Run the Container
```bash
docker run -d \
  --name queuestorm \
  -p 8000:8000 \
  --env-file .env \
  queuestorm-investigator
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Optional | – | Your Google Gemini API Key. |
| `OPENAI_API_KEY` | Optional | – | Your OpenAI API Key (Fallback if Gemini isn't used). |
| `MODEL` | No | `gpt-4o-mini` | The model string you wish to use. |
| `MOCK_AI` | No | `false` | Set to `true` to bypass the LLM network request for unit testing. |

*(Note: You only need to provide **one** API key. The system will auto-detect which to use.)*

---

## 📖 API Reference

### `GET /health`
Returns the status of the server.

### `POST /analyze-ticket`
Analyzes a support ticket and returns a forensic decision.

**Example cURL Request:**
```bash
curl -X POST http://localhost:8000/analyze-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "complaint": "I did not authorize a $500 transfer to an unknown account yesterday.",
    "transaction_history": [
      {
        "transaction_id": "TXN-9821",
        "amount": 500.00,
        "currency": "USD",
        "timestamp": "2025-06-24T14:32:00Z",
        "type": "transfer",
        "status": "completed",
        "merchant": "Unknown Account"
      }
    ]
  }'
```

**Example Output:**
```json
{
  "ticket_id": "TKT-001",
  "case_type": "unauthorized_transaction",
  "department": "fraud_risk",
  "priority": "high",
  "relevant_transaction_id": "TXN-9821",
  "evidence_verdict": "consistent",
  "confidence_score": 0.98,
  "reasoning": "The customer reported an unauthorized $500 transfer which exactly matches transaction TXN-9821.",
  "customer_reply": "Thank you for alerting us. We are currently investigating this unauthorized transaction and a specialist will reach out shortly.",
  "human_review_required": true
}
```

---

## 📝 License
This project is licensed under the MIT License.
