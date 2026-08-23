# GramSell AI Architecture

```text
Voice / Image / Text
        |
        v
FastAPI Input Gateway
        |
        v
Central LLM Engine
        |
        +--> Memory Agent
        |
        +--> Insight Agent <--> Google Maps Grounding / Google Weather
        |
        +--> Guide Agent
        |
        +--> Decision Agent <--> Vertex AI when configured
        |
        +--> Action Agent
        |
        v
Business Action
        |
        +--> Product Listing
        +--> Customer Response
        +--> Order Workflow
        +--> Payment State
        +--> Business Record
        |
        v
Cloud SQL PostgreSQL
```

The five agents are coordinated capabilities, not five unrelated model deployments.

Google Maps grounding is enabled at the LLM layer for insight workloads when configured.

Weather data is retrieved from Google Weather API using seller location.

Country configuration determines language and currency.

The browser never receives model credentials or database credentials.
