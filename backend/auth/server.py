import jwt,os
from datetime import datetime, timedelta, timezone
from flask import Flask, request
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash


server=Flask(__name__)

server.config["MYSQL_HOST"]=os.environ.get("MYSQL_HOST")
server.config["MYSQL_PASSWORD"]=os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"]=os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"]=int(os.environ.get("MYSQL_PORT"))
mysql=MySQL(server)

@server.route("/login",methods=["POST"])
def login():
    auth=request.authorization
    if not auth:
        return "missing credentials",401
    cur=mysql.connection.cursor()
    res=cur.execute(
        "SELECT email, password FROM user WHERE email=%s",(auth.username,)
    )
    if res>0:
        user_row=cur.fetchone()
        password=user_row[1]
        cur.close()
        if not check_password_hash(password, auth.password):
            return "invalid credentials", 401
        

        else:
            cur.close()
            return create_jwt(auth.username,os.environ.get("JWT_SECRET"),True)
    else:
        cur.close()
        return "invalid credentials",401
    

    
    
@server.route("/register", methods=["POST"])
def register():
    email = request.form.get('email')
    password = request.form.get('password')

    cur = mysql.connection.cursor()

    res = cur.execute("SELECT email FROM user WHERE email = %s", (email,))
    if res > 0:
        cur.close()
        return "User already registered", 409

    hashed_password = generate_password_hash(password)
    cur.execute("INSERT INTO user(email, password) VALUES(%s, %s)", (email, hashed_password))
    
    mysql.connection.commit()

    cur.close()
    return "user registered successfully", 201





@server.route("/validate",methods=["POST"])
def validate():
    encoded_jwt=request.headers.get("Authorization")
    if not encoded_jwt:
        return "missing credentials",401
    encoded_jwt=encoded_jwt.split(" ")[1]
    try:
        decoded=jwt.decode(
            encoded_jwt,os.environ.get("JWT_SECRET"),algorithms=["HS256"]
        )
    except:
        return "not authorized",403
    return decoded,200


def create_jwt(username,secret,authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
            "iat": datetime.now(timezone.utc),
            "admin": authz
        },
        secret,
        algorithm="HS256",
    )


if __name__=="__main__":
    server.run(host='0.0.0.0',port=3000)

