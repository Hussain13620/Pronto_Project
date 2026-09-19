from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlfunct import insertdata
from sqlfunct import get_db_connection
import mysql.connector

app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class user_login_credentials(BaseModel):
    email: str
    password: str
@app.post("/login")
def login_info(credentials: user_login_credentials):
    host="localhost"
    user="root"
    password="Hussain13620_root"
    database="KAAMKAAJ"
    table="user_data"
    conn=get_db_connection(host,user,password,database)
    query=f"SELECT * FROM {table} WHERE email=%s AND user_pass=%s"
    values=(credentials.email,credentials.password)
    cursor=conn.cursor()
    cursor.execute(query,values)
    user_record=cursor.fetchone()
    cursor.close()
    conn.close()
    if user_record:
        return{
            "status":"success","message":f"Welcome back {user_record[1]}"
        }
    else:
        return{
            "status":"error","message":f"User not found ! Please signup"
        }
    
    
class user_signup_credentials(BaseModel):
    username: str
    email: str
    phone_no: str
    password: str
@app.post("/signup")
def signup_info(credentials: user_signup_credentials):
    host="localhost"
    user="root"
    password="Hussain13620_root"
    database="KAAMKAAJ"
    table="user_data"
    user_data_dict={
        "username":credentials.username,
        "email":credentials.email,
        "phone_number":credentials.phone_no,
        "user_pass":credentials.password
    }
    try:
        insertdata(host, user, password, database, table, user_data_dict)
        return {
            "status": "success",
            "message": f"User {credentials.username} registered successfully!"
        }
    except mysql.connector.Error as err:
        # Error code 1062 handles duplicate entry violations in MySQL
        if err.errno == 1062:
            return {
                "status": "error",
                "message": "Email or phone number already registered!"
            }
        else:
            return {
                "status": "error",
                "message": f"Database error: {err.msg}"
            }
class worker_login_credentials(BaseModel):
    phone_number:str
    worker_pass:str
@app.post("/worker-login")
def worker_login_info(credentials:worker_login_credentials ):
    host="localhost"
    user="root"
    password="Hussain13620_root"
    database="KAAMKAAJ"
    table="worker_data"
    conn=get_db_connection(host,user,password,database)
    query=f"SELECT * FROM {table} WHERE phone_number=%s AND worker_pass=%s"
    values=(credentials.phone_number,credentials.worker_pass)
    cursor=conn.cursor()
    cursor.execute(query,values)
    worker_record=cursor.fetchone()
    print("DEBUG: worker_record fetched from DB ->", worker_record)
    print("EXECUTING QUERY:", query)
    print("WITH VALUES:", values)
    cursor.close()
    conn.close()
    if worker_record:
        return{
                "status":"success","message":f"Welcome back {worker_record[1]}"
        }
    else:
        return{
                "status":"error","message":f"Worker not found ! Please signup"
        }
class worker_signup_credentials(BaseModel):
    worker_name:str
    phone_number:str
    worker_pass:str
@app.post("/worker-signup")
def worker_signup_info(credentials:worker_signup_credentials):
    host="localhost"
    user="root"
    password="Hussain13620_root"
    database="KAAMKAAJ"
    table="worker_data"
    worker_data_dict={
        "worker_name":credentials.worker_name,
        "phone_number":credentials.phone_number,
        "worker_pass":credentials.worker_pass
    }
    try:
        insertdata(host, user, password, database, table, worker_data_dict)
        return {
            "status": "success",
            "message": f"Worker {credentials.worker_name} registered successfully!"
        }
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return {
                "status": "error",
                "message": "Phone number already registered!"
            }
        else:
            return {
                "status": "error",
                "message": f"Database error: {err.msg}"
            }


