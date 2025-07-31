from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
import os, requests, json

server = Flask(__name__)

server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))
mysql = MySQL(server)

AUTH_SVC_ADDRESS = os.environ.get("AUTH_SVC_ADDRESS")

def validate_token(req):
    """Validate JWT using the auth service."""
    token = req.headers.get("Authorization")
    if not token:
        return None, ("Missing credentials", 401)

    try:
        response = requests.post(
            f"http://{AUTH_SVC_ADDRESS}/validate",
            headers={"Authorization": token}
        )
    except requests.exceptions.RequestException as e:
        return None, ("Auth service unreachable", 503)

    if response.status_code == 200:
        return response.json(), None
    else:
        return None, (response.text, response.status_code)


@server.route("/setpreference/<preference>", methods=['POST'])
def set_preference(preference):
    user, err = validate_token(request)
    if err:
        return err

    email = user.get("username")
    if not email or not preference:
        return "Missing data", 400
    
    try:

        cur = mysql.connection.cursor()
        res = cur.execute("SELECT * FROM preference WHERE user_email = %s", (email,))
        if res > 0:
            cur.execute("UPDATE preference SET preference = %s WHERE user_email = %s", (preference, email))
            mysql.connection.commit()
            cur.close()
            return "Preference updated successfully", 200

        cur.execute("INSERT INTO preference (user_email, preference) VALUES (%s, %s)", (email, preference))
        mysql.connection.commit()
        cur.close()
        return "Preference set successfully", 201
    
    except Exception as e:
        return f"error occured  while setting preference: ${e}",500
    
    finally:
        cur.close()
 


@server.route("/getpreference", methods=["GET"])
def get_preference():
    user, err = validate_token(request)
    if err:
        return err

    email = user.get("username")
    if not email:
        return "Missing email", 400
    
    try:

        cur = mysql.connection.cursor()
        res = cur.execute("SELECT preference FROM preference WHERE user_email = %s", (email,))
        if res > 0:
            preference = cur.fetchone()[0]
            return jsonify({"email": email, "preference": preference}), 200
        else:
            return "No preference set for user", 404
        
    except Exception as e:
        return f"error occured while getting preference: ${e}",500


if __name__ == "__main__":
    server.run(host='0.0.0.0', port=5050)
