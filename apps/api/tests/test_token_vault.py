from app.crypto.token_vault import TokenVault


def test_token_encrypt_decrypt_roundtrip():
    vault = TokenVault()
    enc = vault.encrypt('abc123token')
    assert enc != 'abc123token'
    dec = vault.decrypt(enc)
    assert dec == 'abc123token'
