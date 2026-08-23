# GramSell AI Production 65% v7

This build extends the 50% milestone with a strict agent output contract and grounding-state validation.

## Agent contract

Every agent response is normalized into:

- facts
- recommendations
- uncertainties
- actions
- evidence

The Action Agent cannot claim an application action was executed unless the application actually executes it. A model-produced `executed` state is downgraded to `proposed` and marked with an execution guard.

## Grounding integrity

Grounding availability is exposed separately from grounded data. Missing or unavailable external data is never treated as evidence.

## Verification

Backend integrity suite: 11 tests passed.
