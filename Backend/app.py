from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from pathlib import Path
import os


# =========================================================
# LOAD .ENV FILE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = SECRET_KEY

CORS(
    app,
    supports_credentials=True
)


# =========================================================
# CHECK ENVIRONMENT VARIABLES
# =========================================================

if not MONGO_URI:
    print("ERROR: MONGO_URI was not found.")
    print("Expected .env location:")
    print(ENV_FILE)

if not SECRET_KEY:
    print("WARNING: SECRET_KEY was not found in .env.")


# =========================================================
# MONGODB CONNECTION
# =========================================================

client = None
db = None
users_collection = None


try:

    if not MONGO_URI:
        raise ValueError("MONGO_URI is missing from .env")

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    # Test connection
    client.admin.command("ping")

    print("MongoDB connected successfully!")

    # Database
    db = client["flick_database"]

    # Users collection
    users_collection = db["users"]


except Exception as e:

    print("MongoDB connection failed:")
    print(e)


# =========================================================
# HOME / TEST API
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "success": True,

        "message": "FLICK backend is running!"

    })


# =========================================================
# SIGNUP
# =========================================================

@app.route("/api/signup", methods=["POST"])
def signup():

    try:

        # Check database
        if users_collection is None:

            return jsonify({

                "success": False,

                "message": "Database connection is not available."

            }), 500


        # Get JSON data
        data = request.get_json(silent=True) or {}


        name = str(
            data.get("name", "")
        ).strip()


        email = str(
            data.get("email", "")
        ).strip().lower()


        password = str(
            data.get("password", "")
        )


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not name:

            return jsonify({

                "success": False,

                "message": "Full name is required."

            }), 400


        if not email:

            return jsonify({

                "success": False,

                "message": "Email address is required."

            }), 400


        if not password:

            return jsonify({

                "success": False,

                "message": "Password is required."

            }), 400


        if len(password) < 8:

            return jsonify({

                "success": False,

                "message":
                "Password must contain at least 8 characters."

            }), 400


        # -------------------------------------------------
        # CHECK EXISTING USER
        # -------------------------------------------------

        existing_user = users_collection.find_one({

            "email": email

        })


        if existing_user:

            return jsonify({

                "success": False,

                "message":
                "An account with this email already exists."

            }), 409


        # -------------------------------------------------
        # HASH PASSWORD
        # -------------------------------------------------

        hashed_password = generate_password_hash(
            password
        )


        # -------------------------------------------------
        # CREATE USER
        # -------------------------------------------------

        new_user = {

            "name": name,

            "email": email,

            "password": hashed_password

        }


        users_collection.insert_one(
            new_user
        )


        return jsonify({

            "success": True,

            "message":
            "Account created successfully."

        }), 201


    except Exception as e:

        print("Signup error:")
        print(e)


        return jsonify({

            "success": False,

            "message":
            "Server error. Please try again."

        }), 500


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        # Check database
        if users_collection is None:

            return jsonify({

                "success": False,

                "message":
                "Database connection is not available."

            }), 500


        # Get JSON data
        data = request.get_json(silent=True) or {}


        email = str(
            data.get("email", "")
        ).strip().lower()


        password = str(
            data.get("password", "")
        )


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not email or not password:

            return jsonify({

                "success": False,

                "message":
                "Email and password are required."

            }), 400


        # -------------------------------------------------
        # FIND USER
        # -------------------------------------------------

        user = users_collection.find_one({

            "email": email

        })


        if user is None:

            return jsonify({

                "success": False,

                "message":
                "Invalid email or password."

            }), 401


        # -------------------------------------------------
        # CHECK PASSWORD
        # -------------------------------------------------

        password_correct = check_password_hash(

            user["password"],

            password

        )


        if not password_correct:

            return jsonify({

                "success": False,

                "message":
                "Invalid email or password."

            }), 401


        # -------------------------------------------------
        # CREATE LOGIN SESSION
        # -------------------------------------------------

        session["user_id"] = str(
            user["_id"]
        )

        session["user_name"] = user["name"]

        session["user_email"] = user["email"]


        return jsonify({

            "success": True,

            "message":
            "Login successful.",

            "user": {

                "name": user["name"],

                "email": user["email"]

            }

        }), 200


    except Exception as e:

        print("Login error:")
        print(e)


        return jsonify({

            "success": False,

            "message":
            "Server error. Please try again."

        }), 500


# =========================================================
# CHECK CURRENT USER
# =========================================================

@app.route("/api/me", methods=["GET"])
def current_user():

    if "user_id" not in session:

        return jsonify({

            "loggedIn": False

        }), 401


    return jsonify({

        "loggedIn": True,

        "user": {

            "name":
            session["user_name"],

            "email":
            session["user_email"]

        }

    }), 200


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()


    return jsonify({

        "success": True,

        "message":
        "Logged out successfully."

    }), 200


# =========================================================
# RUN FLASK SERVER
# =========================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print("        FLICK BACKEND SERVER")
    print("======================================")
    print()

    print("Backend folder:")
    print(BASE_DIR)

    print()

    print("Environment file:")
    print(ENV_FILE)

    print()

    if MONGO_URI:

        print("MONGO_URI loaded successfully.")

    else:

        print("MONGO_URI NOT FOUND.")

    print()

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )