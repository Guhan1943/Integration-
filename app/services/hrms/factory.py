from app.services.hrms.providers.zoho import ZohoConnector
from app.services.hrms.providers.bamboo import BambooConnector


def get_hrms_connector(provider, connection, db, settings):
    connectors = {
        "zoho": ZohoConnector,
        "bamboo": BambooConnector,
    }

    connector_class = connectors.get(provider)

    if not connector_class:
        raise Exception("Unsupported HRMS provider")

    return connector_class(connection, db, settings)
