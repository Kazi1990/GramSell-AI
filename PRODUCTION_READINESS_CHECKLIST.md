# Production Readiness Checklist

## Application
- [x] FastAPI backend
- [x] Seller registration and login
- [x] Password hashing with scrypt
- [x] Signed bearer session tokens
- [x] API authentication boundary
- [x] Seller-scoped authorization
- [x] Request-size guard
- [x] Request IDs
- [x] Generic internal-error responses
- [x] Payment verification boundary
- [x] Financial planning safeguards
- [x] Risk evidence safeguards
- [x] Agent output integrity contract
- [x] Grounding/MCP boundary
- [x] Social integration boundary
- [x] Frontend authentication flow
- [x] Backend automated tests: 15 passed

## Deployment-time
- [ ] Configure production secrets in Secret Manager
- [ ] Configure production database
- [ ] Configure live Vertex AI access
- [ ] Configure live Maps MCP access
- [ ] Configure approved payment provider adapters
- [ ] Configure approved social provider adapters
- [ ] Build frontend in deployment environment
- [ ] Deploy backend to Cloud Run with the dedicated service account
- [ ] Run post-deployment smoke tests

No production credential or provider secret is included in this archive.
