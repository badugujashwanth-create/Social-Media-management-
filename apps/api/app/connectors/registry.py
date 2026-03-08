from app.connectors.base import Connector
from app.connectors.facebook import FacebookConnector
from app.connectors.linkedin import LinkedInConnector
from app.connectors.x import XConnector
from app.connectors.instagram_stub import InstagramStubConnector


def get_connectors() -> dict[str, Connector]:
    connectors = [FacebookConnector(), LinkedInConnector(), XConnector(), InstagramStubConnector()]
    return {c.platform_name: c for c in connectors}
