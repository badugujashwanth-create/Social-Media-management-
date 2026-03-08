from cryptography.fernet import Fernet
from app.config import get_settings


class TokenVault:
    def __init__(self, key: str | None = None):
        settings = get_settings()
        self.fernet = Fernet((key or settings.token_encryption_key).encode())

    def encrypt(self, raw: str) -> str:
        return self.fernet.encrypt(raw.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        return self.fernet.decrypt(encrypted.encode()).decode()
