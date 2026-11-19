import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

from fastapi import HTTPException, Request


_HASH_PREFIX = "scrypt$"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_HASH_BYTES = 32
_SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7


def _session_database():
    database_path = Path(
        os.environ.get(
            "PRONTO_REQUESTS_DB",
            str(Path(__file__).with_name("worker_service_requests.sqlite3")),
        )
    )
    connection = sqlite3.connect(database_path, timeout=10)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS auth_sessions (
            session_id TEXT PRIMARY KEY,
            expires_at TEXT NOT NULL
        )
        """
    )
    return connection


def _session_is_active(session_id: str) -> bool:
    connection = _session_database()
    try:
        row = connection.execute(
            "SELECT 1 FROM auth_sessions WHERE session_id = ? AND expires_at > CURRENT_TIMESTAMP",
            (session_id,),
        ).fetchone()
        return row is not None
    finally:
        connection.close()


def _register_session(session_id: str) -> None:
    connection = _session_database()
    try:
        with connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE expires_at <= CURRENT_TIMESTAMP"
            )
            connection.execute(
                """
                INSERT INTO auth_sessions (session_id, expires_at)
                VALUES (?, datetime('now', ?))
                """,
                (session_id, f"+{_SESSION_MAX_AGE_SECONDS} seconds"),
            )
    finally:
        connection.close()


def revoke_session(session_id: str) -> None:
    if not session_id:
        return
    connection = _session_database()
    try:
        with connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE session_id = ?",
                (session_id,),
            )
    finally:
        connection.close()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_HASH_BYTES,
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    hash_text = base64.urlsafe_b64encode(password_hash).decode("ascii").rstrip("=")
    return f"{_HASH_PREFIX}{salt_text}${hash_text}"


def verify_password(password: str, stored_password: str) -> tuple[bool, bool]:
    if not stored_password.startswith(_HASH_PREFIX):
        return hmac.compare_digest(password.encode("utf-8"), stored_password.encode("utf-8")), True

    try:
        _, salt_text, hash_text = stored_password.split("$", 2)
        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        expected_hash = base64.urlsafe_b64decode(hash_text + "=" * (-len(hash_text) % 4))
    except (ValueError, TypeError):
        return False, False
    if len(salt) != 16 or len(expected_hash) != _HASH_BYTES:
        return False, False

    actual_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=len(expected_hash),
    )
    return hmac.compare_digest(actual_hash, expected_hash), False


def get_identity(request: Request, role: str | None = None) -> dict:
    identity = request.session
    if (
        not identity.get("id")
        or not identity.get("role")
        or not identity.get("session_id")
        or not _session_is_active(identity["session_id"])
    ):
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    if role and identity["role"] != role:
        raise HTTPException(status_code=403, detail="You are not allowed to perform this action.")
    return identity


def verify_csrf(request: Request) -> None:
    expected = request.session.get("csrf_token", "")
    supplied = request.headers.get("x-csrf-token", "")
    if not expected or not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=403, detail="The security token is missing or invalid.")


def start_session(request: Request, role: str, identity: str, name: str) -> str:
    csrf_token = secrets.token_urlsafe(32)
    session_id = secrets.token_urlsafe(32)
    _register_session(session_id)
    request.session.clear()
    request.session.update(
        {
            "id": str(identity),
            "role": role,
            "name": name,
            "csrf_token": csrf_token,
            "session_id": session_id,
        }
    )
    return csrf_token
