# Data Integrity

GramSell AI treats evidence and business records as separate from model-generated recommendations.

Recorded facts:
- Seller records
- Product cost
- Seller-selected selling price
- Inventory
- Orders
- Payment status
- Expenses when recorded
- Savings when recorded

Generated intelligence:
- Market interpretation
- Business insight
- Recommendations
- Decision support
- Draft social-commerce content

The application must never convert generated content into a recorded transaction.

Payment:
- pending means payment has not been verified
- paid means a real payment confirmation has been recorded
- collected means a real COD collection has been recorded
- failed means a real failure has been recorded
- cancelled means the order was cancelled

Financial readiness:
The system may calculate a business readiness indicator from real records. It must not present this as a bank credit score or guarantee a loan outcome.
