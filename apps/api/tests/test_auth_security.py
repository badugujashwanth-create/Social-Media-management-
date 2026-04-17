from app.auth.security import hash_password, verify_password


def test_hash_password_roundtrip():
    hashed = hash_password('demo-password')

    assert hashed != 'demo-password'
    assert verify_password('demo-password', hashed) is True


def test_verify_password_rejects_invalid_hash():
    assert verify_password('demo-password', 'not-a-bcrypt-hash') is False
