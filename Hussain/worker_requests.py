import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, validator

from auth_utils import get_identity, verify_csrf


router = APIRouter()
DATABASE_PATH = Path(
    os.environ.get(
        "PRONTO_REQUESTS_DB",
        str(Path(__file__).with_name("worker_service_requests.sqlite3")),
    )
)

ALLOWED_SERVICES = {
    "sweeping",
    "mopping",
    "washing_vessels",
    "laundry",
    "dusting",
    "balcony_cleaning",
    "ironing_and_folding",
    "kitchen_prep",
}
ALLOWED_PROPERTY_TYPES = {
    "1_bhk",
    "2_bhk",
    "3_bhk",
    "4_bhk",
    "penthouse",
    "villa",
    "studio",
    "other",
}


class ServiceRequestCreate(BaseModel):
    services: list[str] = Field(..., min_length=1, max_length=8)
    property_type: str | None = Field(default=None, max_length=32)

    @validator("services")
    def validate_services(cls, services):
        if len(set(services)) != len(services):
            raise ValueError("Services must not contain duplicates")
        if any(service not in ALLOWED_SERVICES for service in services):
            raise ValueError("One or more selected services are not supported")
        return services

    @validator("property_type")
    def validate_property_type(cls, property_type):
        if property_type is not None and property_type not in ALLOWED_PROPERTY_TYPES:
            raise ValueError("Property type is not supported")
        return property_type


class WorkerAvailability(BaseModel):
    online: bool


def connect_database():
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            services TEXT NOT NULL,
            property_type TEXT,
            assigned_worker_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(service_requests)").fetchall()
    }
    if "user_id" not in columns:
        connection.execute("ALTER TABLE service_requests ADD COLUMN user_id TEXT")
    if "assigned_worker_id" not in columns:
        connection.execute("ALTER TABLE service_requests ADD COLUMN assigned_worker_id TEXT")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS worker_presence (
            worker_id TEXT PRIMARY KEY,
            online INTEGER NOT NULL,
            last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return connection


@contextmanager
def database_connection():
    connection = connect_database()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def require_online_worker(connection, worker_id: str) -> None:
    presence = connection.execute(
        """
        SELECT online
        FROM worker_presence
        WHERE worker_id = ?
          AND last_seen >= datetime('now', '-45 seconds')
        """,
        (worker_id,),
    ).fetchone()
    if not presence or not presence["online"]:
        raise HTTPException(status_code=409, detail="Go online before receiving requests.")


@router.post("/service-requests", status_code=201)
def create_service_request(
    request_data: ServiceRequestCreate,
    request: Request,
):
    identity = get_identity(request, "user")
    verify_csrf(request)

    with database_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO service_requests (user_id, services, property_type)
            VALUES (?, ?, ?)
            """,
            (identity["id"], json.dumps(request_data.services), request_data.property_type),
        )
        request_id = cursor.lastrowid

    return {"id": request_id, "status": "pending"}


@router.post("/worker/availability")
def set_worker_availability(availability: WorkerAvailability, request: Request):
    identity = get_identity(request, "worker")
    verify_csrf(request)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO worker_presence (worker_id, online, last_seen)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(worker_id) DO UPDATE SET
                online = excluded.online,
                last_seen = CURRENT_TIMESTAMP
            """,
            (identity["id"], int(availability.online)),
        )
    return {"online": availability.online}


@router.get("/worker/service-requests")
def list_worker_service_requests(request: Request):
    identity = get_identity(request, "worker")
    with database_connection() as connection:
        require_online_worker(connection, identity["id"])
        connection.execute(
            """
            UPDATE worker_presence
            SET last_seen = CURRENT_TIMESTAMP
            WHERE worker_id = ?
            """,
            (identity["id"],),
        )
        rows = connection.execute(
            """
            SELECT id, services, property_type, requested_at
            FROM service_requests
            WHERE status = 'pending' AND assigned_worker_id IS NULL
            ORDER BY id DESC
            """
        ).fetchall()

    return {
        "requests": [
            {
                "id": row["id"],
                "services": json.loads(row["services"]),
                "property_type": row["property_type"],
                "requested_at": row["requested_at"],
            }
            for row in rows
        ]
    }


@router.post("/worker/service-requests/{request_id}/claim")
def claim_service_request(request_id: int, request: Request):
    identity = get_identity(request, "worker")
    verify_csrf(request)
    with database_connection() as connection:
        require_online_worker(connection, identity["id"])
        result = connection.execute(
            """
            UPDATE service_requests
            SET assigned_worker_id = ?, status = 'assigned'
            WHERE id = ? AND status = 'pending' AND assigned_worker_id IS NULL
            """,
            (identity["id"], request_id),
        )
        if result.rowcount == 0:
            raise HTTPException(
                status_code=409,
                detail="This request is no longer available.",
            )
    return {"id": request_id, "status": "assigned"}
