from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import HRMSConnection
from app.db.session import get_db
from app.services.hrms.factory import get_hrms_connector


router = APIRouter(prefix="/api/hrms", tags=["hrms"])


def _map_lifecycle_to_status(lifecycle: str | None) -> str | None:
    if not lifecycle:
        return None

    lifecycle_map = {
        "active": "Active",
        "terminated": "Inactive",
        "relieved": "Relieved",
    }
    return lifecycle_map.get(lifecycle.lower())


# ===== ZOHO OAUTH FLOW (UNCHANGED) =====
@router.get("/auth/")
def hrms_auth_init(
    provider: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not provider:
        return JSONResponse(status_code=400, content={"error": "Provider required"})

    # Skip OAuth init for API Key providers
    if provider.lower() == "bamboohr":
        return JSONResponse(
            status_code=400,
            content={"error": "BambooHR uses API Key auth. Use /api/hrms/connect/ instead"},
        )

    connection = HRMSConnection(
        user_id=0,
        provider=provider,
        access_token="",
        refresh_token=None,
        token_expiry=datetime.now(timezone.utc),
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    connector = get_hrms_connector(provider, connection, db, settings)
    state = f"{provider}:{connection.id}"
    auth_url = connector.get_authorization_url(state)

    return {"auth_url": auth_url}


@router.get("/callback/")
def hrms_oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    # ...existing code...
    if not code or not state:
        return JSONResponse(status_code=400, content={"error": "Invalid callback"})

    try:
        provider, connection_id = state.split(":", 1)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid callback"})

    try:
        connection_id_value = int(connection_id)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "Invalid callback"})

    connection = (
        db.query(HRMSConnection)
        .filter(
            HRMSConnection.id == connection_id_value,
            HRMSConnection.provider == provider,
        )
        .first()
    )

    if not connection:
        return JSONResponse(status_code=400, content={"error": "Connection not found"})

    connector = get_hrms_connector(provider, connection, db, settings)
    token_data = connector.exchange_code_for_token(code)

    connection.access_token = token_data["access_token"]
    connection.refresh_token = token_data.get("refresh_token")
    connection.token_expiry = datetime.now(timezone.utc) + timedelta(
        seconds=token_data["expires_in"]
    )
    db.add(connection)
    db.commit()

    return {
        "provider": provider,
        "access_token": connection.access_token,
        "refresh_token": connection.refresh_token,
        "token_expiry": connection.token_expiry.isoformat(),
    }


# ===== NEW: BAMBOOHR API KEY CONNECTION =====
@router.post("/connect/")
def hrms_api_key_connect(
    provider: str | None = Query(default=None),
    api_key: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Direct API Key authentication for providers like BambooHR
    No OAuth flow needed
    """
    if not provider or not api_key:
        return JSONResponse(
            status_code=400,
            content={"error": "Provider and API Key required"},
        )

    # Validate API key with the provider
    connector = get_hrms_connector(provider, None, db, settings)
    
    try:
        # Test connection with provided API key
        is_valid = connector.validate_api_key(api_key)
        if not is_valid:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API Key"},
            )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Validation failed: {str(exc)}"},
        )

    # Create connection record (no refresh token needed for API key)
    connection = HRMSConnection(
        user_id=0,
        provider=provider,
        access_token=api_key,  # Store API key as access_token
        refresh_token=None,     # No refresh token for API key auth
        token_expiry=None,      # No expiry for API keys (unless set by provider)
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    return {
        "provider": provider,
        "connection_id": connection.id,
        "status": "Connected successfully",
        "message": "API Key stored securely",
    }


# ===== EMPLOYEE FETCH (MODIFIED) =====
@router.get("/employees/")
def hrms_employees(
    provider: str | None = Query(default=None),
    status: str | None = Query(default=None),
    lifecycle: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not provider:
        return JSONResponse(status_code=400, content={"error": "Provider required"})

    connection = (
        db.query(HRMSConnection)
        .filter(
            HRMSConnection.provider == provider,
            HRMSConnection.is_active.is_(True),
        )
        .order_by(desc(HRMSConnection.id))
        .first()
    )

    if not connection:
        return JSONResponse(
            status_code=400,
            content={"error": f"{provider} not connected"},
        )

    # Check if token/key is expired (OAuth only)
    if provider.lower() != "bamboohr" and connection.token_expiry:
        if datetime.now(timezone.utc) > connection.token_expiry:
            return JSONResponse(
                status_code=401,
                content={"error": "Token expired. Please reconnect."},
            )

    connector = get_hrms_connector(provider, connection, db, settings)

    if lifecycle:
        status = _map_lifecycle_to_status(lifecycle)

    try:
        employees = connector.fetch_employees(
            updated_after=connection.last_sync_at,
            status=status,
        )

        connection.last_sync_at = datetime.now(timezone.utc)
        db.add(connection)
        db.commit()

        return employees
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})
    
    