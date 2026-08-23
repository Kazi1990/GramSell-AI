CREATE TABLE IF NOT EXISTS payment_events (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    provider VARCHAR(40) NOT NULL,
    provider_reference VARCHAR(160) NOT NULL,
    status VARCHAR(40) NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    reason TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_payment_provider_reference UNIQUE (provider, provider_reference)
);
CREATE INDEX IF NOT EXISTS ix_payment_events_order_id ON payment_events(order_id);
CREATE INDEX IF NOT EXISTS ix_orders_seller_payment ON orders(seller_id, payment_status);
CREATE INDEX IF NOT EXISTS ix_memory_seller_created ON business_memory(seller_id, created_at);
