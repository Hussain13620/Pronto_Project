import os

from sqlfunct import createtable

host = os.environ.get("MYSQL_HOST", "localhost")
user = os.environ.get("MYSQL_USER", "root")
password = os.environ.get("MYSQL_PASSWORD")
database = os.environ.get("MYSQL_DATABASE", "KAAMKAAJ")

if password is None:
    raise RuntimeError("Set the MYSQL_PASSWORD environment variable before creating tables.")

table_1="user_data"
schema_1={
    "ID":"INT AUTO_INCREMENT PRIMARY KEY",
    "username":"VARCHAR(250)",
    "email":"VARCHAR(250) UNIQUE",
    "phone_number":"VARCHAR(10)",
    "user_pass":"VARCHAR(100)" 
}
createtable(host,user,password,database,table_1,schema_1)
table_2="worker_data"
schema_2={
    "ID":"INT AUTO_INCREMENT PRIMARY KEY",
    "worker_name":"VARCHAR(250)",
    "phone_number":"VARCHAR(10) UNIQUE",
    "worker_pass":"VARCHAR(250)"
}
createtable(host,user,password,database,table_2,schema_2)

table_3="contact_data"
schema_3={
    "sr_no":"INT AUTO_INCREMENT PRIMARY KEY",
    "name":"VARCHAR(250)",
    "phone_number":"VARCHAR(250)",
    "description":"TEXT"
}
createtable(host,user,password,database,table_3,schema_3)
