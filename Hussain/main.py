import os
import secrets

import mysql.connector
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from auth_utils import get_identity, hash_password, revoke_session, start_session, verify_password
from sqlfunct import get_db_connection, insertdata
from worker_requests import router as worker_requests_router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "FRONTEND_ORIGINS",
            "http://127.0.0.1:5500,http://localhost:5500",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY") or secrets.token_urlsafe(48),
    session_cookie="pronto_session",
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
)
app.include_router(worker_requests_router)


def database_settings():
    password = os.environ.get("MYSQL_PASSWORD")
    if password is None:
        raise HTTPException(
            status_code=503,
            detail="Set the MYSQL_PASSWORD environment variable before using the API.",
        )
    return (
        os.environ.get("MYSQL_HOST", "localhost"),
        os.environ.get("MYSQL_USER", "root"),
        password,
        os.environ.get("MYSQL_DATABASE", "KAAMKAAJ"),
    )


def database_connection():
    try:
        return get_db_connection(*database_settings())
    except mysql.connector.Error as error:
        raise HTTPException(status_code=503, detail="The account database is unavailable.") from error


class UserLoginCredentials(BaseModel):
    email: str = Field(..., max_length=250)
    password: str = Field(..., max_length=128)


@app.post("/login")
def login_info(credentials: UserLoginCredentials, request: Request):
    connection = database_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT ID, username, email, phone_number, user_pass FROM user_data WHERE email=%s",
            (credentials.email,),
        )
        user_record = cursor.fetchone()
        if not user_record:
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")

        valid, needs_upgrade = verify_password(credentials.password, user_record[4])
        if not valid:
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        if needs_upgrade:
            cursor.execute(
                "UPDATE user_data SET user_pass=%s WHERE ID=%s",
                (hash_password(credentials.password), user_record[0]),
            )
            connection.commit()
        csrf_token = start_session(request, "user", user_record[0], user_record[1])
        return {
            "status": "success",
            "message": f"Welcome back {user_record[1]}",
            "name": user_record[1],
            "role": "user",
            "csrf_token": csrf_token,
        }
    except mysql.connector.Error as error:
        raise HTTPException(status_code=503, detail="The account database is unavailable.") from error
    finally:
        connection.close()


class UserSignupCredentials(BaseModel):
    username: str = Field(..., min_length=1, max_length=250)
    email: str = Field(..., min_length=3, max_length=250)
    phone_no: str = Field(..., min_length=1, max_length=10)
    password: str = Field(..., min_length=8, max_length=128)


@app.post("/signup")
def signup_info(credentials: UserSignupCredentials):
    try:
        insertdata(
            *database_settings(),
            "user_data",
            {
                "username": credentials.username,
                "email": credentials.email,
                "phone_number": credentials.phone_no,
                "user_pass": hash_password(credentials.password),
            },
        )
        return {
            "status": "success",
            "message": f"User {credentials.username} registered successfully!",
        }
    except mysql.connector.Error as error:
        if error.errno == 1062:
            raise HTTPException(
                status_code=409,
                detail="Email or phone number already registered!",
            ) from error
        raise HTTPException(status_code=503, detail="Could not save the user account.") from error


class WorkerLoginCredentials(BaseModel):
    phone_number: str = Field(..., max_length=10)
    worker_pass: str = Field(..., max_length=128)


@app.post("/worker-login")
def worker_login_info(credentials: WorkerLoginCredentials, request: Request):
    connection = database_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT ID, worker_name, phone_number, worker_pass FROM worker_data WHERE phone_number=%s",
            (credentials.phone_number,),
        )
        worker_record = cursor.fetchone()
        if not worker_record:
            raise HTTPException(status_code=401, detail="Phone number or password is incorrect.")

        valid, needs_upgrade = verify_password(credentials.worker_pass, worker_record[3])
        if not valid:
            raise HTTPException(status_code=401, detail="Phone number or password is incorrect.")
        if needs_upgrade:
            cursor.execute(
                "UPDATE worker_data SET worker_pass=%s WHERE ID=%s",
                (hash_password(credentials.worker_pass), worker_record[0]),
            )
            connection.commit()
        csrf_token = start_session(request, "worker", worker_record[0], worker_record[1])
        return {
            "status": "success",
            "message": f"Welcome back {worker_record[1]}",
            "name": worker_record[1],
            "role": "worker",
            "csrf_token": csrf_token,
        }
    except mysql.connector.Error as error:
        raise HTTPException(status_code=503, detail="The account database is unavailable.") from error
    finally:
        connection.close()


class WorkerSignupCredentials(BaseModel):
    worker_name: str = Field(..., min_length=1, max_length=250)
    phone_number: str = Field(..., min_length=1, max_length=10)
    worker_pass: str = Field(..., min_length=8, max_length=128)


@app.post("/worker-signup")
def worker_signup_info(credentials: WorkerSignupCredentials):
    try:
        insertdata(
            *database_settings(),
            "worker_data",
            {
                "worker_name": credentials.worker_name,
                "phone_number": credentials.phone_number,
                "worker_pass": hash_password(credentials.worker_pass),
            },
        )
        return {
            "status": "success",
            "message": f"Worker {credentials.worker_name} registered successfully!",
        }
    except mysql.connector.Error as error:
        if error.errno == 1062:
            raise HTTPException(status_code=409, detail="Phone number already registered!") from error
        raise HTTPException(status_code=503, detail="Could not save the worker account.") from error


@app.get("/auth/me")
def current_session(request: Request):
    identity = get_identity(request)
    return {
        "id": identity["id"],
        "role": identity["role"],
        "name": identity["name"],
        "csrf_token": identity["csrf_token"],
    }


@app.post("/logout")
def logout(request: Request):
    revoke_session(request.session.get("session_id", ""))
    request.session.clear()
    return {"status": "success"}


class ContactCredentials(BaseModel):
    name: str
    phone_number: str
    description: str


@app.post("/contact")
def contact_info(credentials: ContactCredentials):
    try:
        insertdata(
            *database_settings(),
            "contact_data",
            {
                "name": credentials.name,
                "phone_number": credentials.phone_number,
                "description": credentials.description,
            },
        )
        return {
            "status": "success",
            "message": "Thank you for contacting us! Your message has been saved.",
        }
    except mysql.connector.Error as error:
        raise HTTPException(status_code=503, detail="Could not save your message.") from error
