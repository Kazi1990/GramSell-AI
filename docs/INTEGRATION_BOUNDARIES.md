# Integration Boundaries

External integrations are capability boundaries, not simulated providers.

A missing credential, connection, or provider adapter produces an explicit unavailable state. The application does not convert an unavailable integration into a successful result.

Social publishing follows:

request -> draft -> seller approval -> provider connector -> provider result -> executed state

Maps and weather remain evidence sources. Payment verification remains provider-authoritative.
