# GramSell AI

GramSell AI is a Google-centered, voice-first business assistant for rural and underserved sellers in Bangladesh, India, and South Africa.

## Architecture

Seller -> Voice/Image/Text -> FastAPI -> Deterministic Hybrid Processing -> Vertex AI Gemini -> Memory -> Insight -> Guide -> Decision -> Action

The five agents are coordinated capabilities around a central LLM engine.

## Principles

- No fabricated sellers
- No fabricated customers
- No fabricated orders
- No fabricated payments
- No fabricated revenue
- No fabricated profit
- No fabricated loan approvals
- No Firestore
- No vector database
- No Telegram
- No hard-coded business records
- No payment verification claim without a real provider signal
- No bank credit decision claim

## Google services

- Gemini 3.1 Flash-Lite for default low-latency agent work
- Vertex AI for configured critical Decision workloads
- Google Maps Platform for location and Maps grounding
- Google Weather API for weather context
- Cloud SQL for PostgreSQL for structured persistence
- Cloud Storage for private object storage when enabled
- Cloud Run for deployment
- Secret Manager for secrets in production

## Country configuration

Bangladesh:
- Bangla
- BDT
- bKash or Nagad as seller-provided payment destination

India:
- Hindi
- INR
- UPI as seller-provided payment destination

South Africa:
- isiZulu
- ZAR
- Seller-configured local payment destination

Payment destinations are stored as seller-provided information. Automated payment verification requires an official provider integration and is not simulated.

## Data model

Products store production cost, seller-selected selling price, margin, quantity and inventory state.

Orders store payment method and payment status. Revenue and profit are calculated only from real recorded orders and costs.

Financial readiness is decision support based on real recorded business data. It is not a bank credit score and does not guarantee lending.

## Local development

1. Create a PostgreSQL database.
2. Copy `.env.example` to `.env`.
3. Configure the Google credentials and database.
4. Start the API.
5. Start the web application.

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend expects `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.

## Production

Deploy the backend and frontend through Cloud Run. Keep credentials server-side and use Secret Manager. Do not expose Google service credentials or model API keys in browser code.

## Integration Rules

The master project uses Cloud SQL PostgreSQL as the structured persistence layer. The five agent capabilities remain coordinated functions around a central Vertex AI Gemini engine.

The first-stage request path is:

Seller input -> deterministic hybrid validation -> seller context -> Vertex AI -> Memory -> Insight -> Guide -> Decision -> Action.

The application does not use a fake-data fallback. Missing credentials or unavailable external data remain unavailable and must not be converted into fabricated business facts.

Payment status `paid` or `collected` cannot be assigned through the generic payment update endpoint. It requires an authoritative provider verification path.

## Current working milestone
This build combines the previous core, payment, financial, and risk layers with multimodal input, grounded agent execution, streaming agent status, and the production neon activity interface. It is a development milestone, not the final release.
