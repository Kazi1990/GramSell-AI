# GramSell AI Integration Checklist

## Required before production

- Set a real Google Cloud project ID.
- Enable Vertex AI and the required Google Cloud APIs.
- Configure Application Default Credentials locally or a least-privilege Cloud Run service account.
- Configure Cloud SQL PostgreSQL through Secret Manager.
- Configure Google Weather credentials through Secret Manager.
- Configure Google Maps credentials through Secret Manager if required by the selected grounding flow.
- Configure an official payment-provider verification adapter for each supported country before marking payments as paid.
- Keep all production records real and traceable.
- Do not use receipt images as authoritative payment proof.
- Do not expose secrets in frontend code.

## Test gates

1. Backend Python syntax and imports pass.
2. Hybrid validation runs before Vertex AI.
3. Agent pipeline preserves Memory -> Insight -> Guide -> Decision -> Action.
4. Missing external data is represented as unavailable, not fabricated.
5. Payment screenshots cannot create paid transactions.
6. Revenue and profit include only paid/collected recorded orders.
7. Cloud Run starts with Vertex AI enabled.
8. Frontend communicates only with the backend API.
