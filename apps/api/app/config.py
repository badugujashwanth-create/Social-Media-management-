from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'SMCC API'
    environment: str = 'development'
    api_v1_prefix: str = '/api/v1'
    secret_key: str = Field(default='change-me', alias='SECRET_KEY')
    token_encryption_key: str = Field(alias='TOKEN_ENCRYPTION_KEY')

    app_public_url: str = Field(default='http://localhost:3000', alias='APP_PUBLIC_URL')
    api_public_url: str = Field(default='http://localhost:8000', alias='API_PUBLIC_URL')
    frontend_base_url: str = Field(default='http://localhost:3000', alias='FRONTEND_BASE_URL')

    postgres_dsn: str = Field(default='postgresql+psycopg2://smcc:smcc@localhost:5432/smcc', alias='POSTGRES_DSN')
    redis_url: str = Field(default='redis://localhost:6379/0', alias='REDIS_URL')
    s3_endpoint: str = Field(default='http://localhost:9000', alias='S3_ENDPOINT')
    s3_access_key: str = Field(default='minioadmin', alias='S3_ACCESS_KEY')
    s3_secret_key: str = Field(default='minioadmin', alias='S3_SECRET_KEY')
    s3_bucket: str = Field(default='smcc', alias='S3_BUCKET')
    s3_region: str = Field(default='us-east-1', alias='S3_REGION')
    s3_public_base: str = Field(default='http://localhost:9000/smcc', alias='S3_PUBLIC_BASE')

    access_token_expire_minutes: int = Field(default=60 * 24, alias='ACCESS_TOKEN_EXPIRE_MINUTES')
    dev_mode: bool = Field(default=True, alias='DEV_MODE')

    facebook_client_id: str | None = Field(default=None, alias='FACEBOOK_CLIENT_ID')
    facebook_client_secret: str | None = Field(default=None, alias='FACEBOOK_CLIENT_SECRET')
    facebook_redirect_uri: str | None = Field(default=None, alias='FACEBOOK_REDIRECT_URI')

    linkedin_client_id: str | None = Field(default=None, alias='LINKEDIN_CLIENT_ID')
    linkedin_client_secret: str | None = Field(default=None, alias='LINKEDIN_CLIENT_SECRET')
    linkedin_redirect_uri: str | None = Field(default=None, alias='LINKEDIN_REDIRECT_URI')

    x_client_id: str | None = Field(default=None, alias='X_CLIENT_ID')
    x_client_secret: str | None = Field(default=None, alias='X_CLIENT_SECRET')
    x_redirect_uri: str | None = Field(default=None, alias='X_REDIRECT_URI')
    ayrshare_api_key: str | None = Field(default=None, alias='AYRSHARE_API_KEY')

    app_rate_limit: str = Field(default='120/minute', alias='APP_RATE_LIMIT')


@lru_cache
def get_settings() -> Settings:
    return Settings()
