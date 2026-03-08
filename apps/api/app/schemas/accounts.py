from datetime import datetime
from typing import Any
from pydantic import BaseModel
from app.models.enums import Platform


class ConnectorCapabilitiesOut(BaseModel):
    supports_image: bool
    supports_link: bool


class OAuthAccountOut(BaseModel):
    id: int
    platform: Platform
    display_name: str | None
    external_account_id: str
    expires_at: datetime | None
    scopes: str | None
    meta_json: dict[str, Any] | None
    capabilities: ConnectorCapabilitiesOut
    updated_at: datetime

    model_config = {'from_attributes': True}


class ManualTokenConnectIn(BaseModel):
    platform: Platform
    display_name: str
    external_account_id: str
    access_token: str
    refresh_token: str | None = None
    scopes: str | None = None


class OAuthStartOut(BaseModel):
    redirect_url: str


class FacebookPageOut(BaseModel):
    id: str
    name: str
    access_token: str | None = None
