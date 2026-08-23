ALTER TABLE sellers ADD COLUMN email VARCHAR(254);
ALTER TABLE sellers ADD COLUMN password_hash VARCHAR(512);
CREATE UNIQUE INDEX IF NOT EXISTS ix_sellers_email ON sellers(email);
