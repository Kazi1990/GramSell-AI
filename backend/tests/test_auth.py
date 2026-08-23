import os
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("AUTH_TOKEN_SECRET", "test-secret-1234567890")
from app.auth import hash_password, verify_password

def test_password_hashing_and_verification():
    encoded = hash_password("StrongPassword123!")
    assert encoded != "StrongPassword123!"
    assert verify_password("StrongPassword123!", encoded)
    assert not verify_password("WrongPassword123!", encoded)
