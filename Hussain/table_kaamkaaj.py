from sqlfunct import createtable
host="localhost"
user="root"
password="Hussain13620_root"
database="KAAMKAAJ"
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
    "phone_number":"VARCHAR(10)",
    "worker_pass":"VARCHAR(250)"
}
createtable(host,user,password,database,table_2,schema_2)
