# Production Runbook

1. Create the Google Cloud project and enable the required APIs.
2. Grant the Cloud Run service account least-privilege access to Vertex AI, Cloud SQL, Secret Manager, Speech-to-Text, and required Google services.
3. Store database and provider secrets in Secret Manager.
4. Apply database migrations from `backend/db`.
5. Deploy the backend container to Cloud Run.
6. Configure the frontend API base URL with the Cloud Run backend URL.
7. Verify `/health` and `/ready`.
8. Create one real seller record.
9. Create one real product with a real cost and seller-controlled price.
10. Create a real test order using a controlled test transaction.
11. Verify that a receipt image alone never changes payment status to paid.
12. Verify that an authoritative provider confirmation changes payment status only once.
13. Verify revenue and profit use only paid or collected records.
14. Test all supported countries and configured languages.
15. Test Vertex AI, Speech-to-Text, Maps grounding, and Weather with real configured services.
16. Review Cloud Logging and audit records.
17. Confirm no secret, provider credential, fabricated business record, or private database value is exposed to the browser.
