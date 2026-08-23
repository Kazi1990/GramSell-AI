CREATE TABLE IF NOT EXISTS business_actions (
    id BIGSERIAL PRIMARY KEY,
    seller_id BIGINT NOT NULL REFERENCES sellers(id),
    action_type VARCHAR(40) NOT NULL,
    payload TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'proposed',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP NULL
);
CREATE INDEX IF NOT EXISTS ix_business_actions_seller ON business_actions(seller_id);
CREATE INDEX IF NOT EXISTS ix_business_actions_status ON business_actions(status);
