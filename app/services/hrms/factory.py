from app.services.hrms.providers.zoho import ZohoConnector


def get_hrms_connector(provider, connection, db, settings):
    connectors = {
        "zoho": ZohoConnector,
    }

    connector_class = connectors.get(provider)

    if not connector_class:
        raise Exception("Unsupported HRMS provider")

    return connector_class(connection, db, settings)
