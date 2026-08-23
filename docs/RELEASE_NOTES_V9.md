# GramSell AI Production v9

This milestone adds a safe external-integration boundary.

- Seller records can declare an optional social provider.
- Integration status exposes whether social publishing is actually configured.
- Social publishing is never reported as successful without a real provider adapter.
- `social_publish` actions remain proposed until an external connector executes them.
- A provider that is not connected or configured cannot publish.
- SQLite test configuration is now compatible with SQLAlchemy's SQLite pools.
- Existing payment, financial, risk, grounding, and agent integrity controls remain unchanged.
