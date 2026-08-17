from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS

from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
import requests
import whisper
import subprocess
import shutil
import os
import tempfile
import uuid
import joblib
import numpy as np

# =========================================================
# ENVIRONMENT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = SECRET_KEY

CORS(
    app,
    supports_credentials=True
)


# =========================================================
# MONGODB
# =========================================================

client = None
db = None
users_collection = None
history_collection = None


try:

    if not MONGO_URI:
        raise ValueError(
            "MONGO_URI is missing from .env"
        )

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    print("MongoDB connected successfully!")

    db = client["flick_database"]

    users_collection = db["users"]

    history_collection = db["history"]


except Exception as e:

    print("MongoDB connection failed:")
    print(e)
# =========================================================
# AUTHENTICATION
# =========================================================

@app.route("/api/signup", methods=["POST"])
def signup():

    try:

        if users_collection is None:

            return jsonify({
                "success": False,
                "message": "Database connection is not available."
            }), 500


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

        if users_collection is None:

            return jsonify({
                "success": False,
                "message":
                    "Database connection is not available."
            }), 500


        data = request.get_json(silent=True) or {}


        email = str(
            data.get("email", "")
        ).strip().lower()


        password = str(
            data.get("password", "")
        )


        if not email or not password:

            return jsonify({
                "success": False,
                "message":
                    "Email and password are required."
            }), 400


        user = users_collection.find_one({
            "email": email
        })


        if user is None:

            return jsonify({
                "success": False,
                "message":
                    "Invalid email or password."
            }), 401


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
        # SESSION
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

                "name":
                    user["name"],

                "email":
                    user["email"]

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
                session.get("user_name", ""),

            "email":
                session.get("user_email", "")

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
# USER HISTORY
# =========================================================

@app.route("/api/history", methods=["GET", "POST"])
def history():

    # -----------------------------------------------------
    # CHECK LOGIN
    # -----------------------------------------------------

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401


    # =====================================================
    # SAVE REVIEW
    # =====================================================

    if request.method == "POST":

        try:

            data = request.get_json(
                silent=True
            ) or {}


            review = str(
                data.get("review", "")
            ).strip()


            sentiment = str(
                data.get("sentiment", "")
            ).strip()


            confidence = data.get(
                "confidence",
                None
            )


            prediction = str(
                data.get("prediction", sentiment)
            ).strip()

            movie_id = data.get("movie_id")

            movie_title = str(
                data.get("movie_title", "")
            ).strip()

            movie_poster = str(
                data.get("movie_poster", "")
            ).strip()


            # -------------------------------------------------
            # VALIDATION
            # -------------------------------------------------

            if not review:

                return jsonify({
                    "success": False,
                    "message": "Review is empty."
                }), 400


            if not sentiment:

                return jsonify({
                    "success": False,
                    "message": "Sentiment is missing."
                }), 400


            # -------------------------------------------------
            # CREATE HISTORY RECORD
            # -------------------------------------------------

            history_record = {

                "user_id":
                    session["user_id"],

                "user_email":
                    session["user_email"],

                "review":
                    review,

                "sentiment":
                    sentiment,

                "prediction":
                    prediction,

                "confidence":
                    confidence,

                "movie_id":
                    movie_id,

                "movie_title":
                    movie_title,

                "movie_poster":
                    movie_poster,

                "created_at":
                    datetime.utcnow()

            }


            # -------------------------------------------------
            # SAVE TO MONGODB
            # -------------------------------------------------

            history_collection.insert_one(
                history_record
            )


            return jsonify({

                "success": True,

                "message":
                    "Review saved to history."

            }), 201


        except Exception as e:

            print(
                "History save error:"
            )

            print(e)


            return jsonify({

                "success": False,

                "message":
                    "Could not save review history."

            }), 500


    # =====================================================
    # GET USER HISTORY
    # =====================================================

    try:

        records = history_collection.find(
            {
                "user_id":
                    session["user_id"]
            }
        ).sort(
            "created_at",
            -1
        )


        history_data = []


        for record in records:

            history_data.append({

                "id":
                    str(record["_id"]),

                "review":
                    record.get(
                        "review",
                        ""
                    ),

                "sentiment":
                    record.get(
                        "sentiment",
                        ""
                    ),

                "prediction":
                    record.get(
                        "prediction",
                        ""
                    ),

                "confidence":
                    record.get(
                        "confidence",
                        None
                    ),

                "movie_id":
                    record.get(
                        "movie_id",
                        None
                    ),

                "movie_title":
                    record.get(
                        "movie_title",
                        ""
                    ),

                "movie_poster":
                    record.get(
                        "movie_poster",
                        ""
                    ),

                "created_at":
                    record.get(
                        "created_at"
                    ).isoformat()
                    if record.get(
                        "created_at"
                    )
                    else None

            })


        return jsonify({

            "success": True,

            "history":
                history_data

        }), 200


    except Exception as e:

        print(
            "History fetch error:"
        )

        print(e)


        return jsonify({

            "success": False,

            "message":
                "Could not load history."

        }), 500
    # =========================================================
# DELETE ONE HISTORY ITEM
# =========================================================

@app.route("/api/history/<history_id>", methods=["DELETE"])
def delete_history(history_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    try:

        from bson import ObjectId

        result = history_collection.delete_one({
            "_id": ObjectId(history_id),
            "user_id": session["user_id"]
        })

        if result.deleted_count == 0:

            return jsonify({
                "success": False,
                "message": "History item not found."
            }), 404

        return jsonify({
            "success": True,
            "message": "History item deleted."
        }), 200

    except Exception as e:

        print("Delete history error:")
        print(e)

        return jsonify({
            "success": False,
            "message": "Could not delete history item."
        }), 500


# =========================================================
# CLEAR ALL USER HISTORY
# =========================================================

@app.route("/api/history/clear", methods=["DELETE"])
def clear_history():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    try:

        result = history_collection.delete_many({
            "user_id": session["user_id"]
        })

        return jsonify({
            "success": True,
            "message": "All history cleared.",
            "deleted": result.deleted_count
        }), 200

    except Exception as e:

        print("Clear history error:")
        print(e)

        return jsonify({
            "success": False,
            "message": "Could not clear history."
        }), 500

# =========================================================
# TMDB CONFIGURATION
# =========================================================

TMDB_BASE_URL = "https://api.themoviedb.org/3"


# =========================================================
# GET POPULAR MOVIES
# =========================================================

@app.route("/api/movies", methods=["GET"])
def get_movies():

    if not TMDB_API_KEY:

        return jsonify({
            "success": False,
            "message": "TMDB API key is not configured."
        }), 500


    try:

        page = request.args.get(
            "page",
            1,
            type=int
        )


        response = requests.get(

            f"{TMDB_BASE_URL}/movie/popular",

            params={
                "api_key": TMDB_API_KEY,
                "language": "en-US",
                "page": page
            },

            timeout=10

        )


        if not response.ok:

            return jsonify({
                "success": False,
                "message": "TMDB request failed."
            }), response.status_code


        data = response.json()


        return jsonify({

            "success": True,

            "page":
                data.get("page", 1),

            "total_pages":
                data.get("total_pages", 1),

            "movies":
                data.get("results", [])

        }), 200


    except requests.RequestException as e:

        print("TMDB request error:")
        print(e)

        return jsonify({

            "success": False,

            "message":
                "Could not connect to TMDB."

        }), 502


# =========================================================
# SEARCH MOVIES
# =========================================================

@app.route("/api/movies/search", methods=["GET"])
def search_movies():

    if not TMDB_API_KEY:

        return jsonify({
            "success": False,
            "message": "TMDB API key is not configured."
        }), 500


    query = request.args.get(
        "query",
        ""
    ).strip()


    if not query:

        return jsonify({

            "success": False,

            "message":
                "Search query is required."

        }), 400


    try:

        response = requests.get(

            f"{TMDB_BASE_URL}/search/movie",

            params={

                "api_key":
                    TMDB_API_KEY,

                "language":
                    "en-US",

                "query":
                    query,

                "include_adult":
                    "false",

                "page":
                    1

            },

            timeout=10

        )


        if not response.ok:

            return jsonify({

                "success": False,

                "message":
                    "TMDB search failed."

            }), response.status_code


        data =response.json()


        return jsonify({

            "success": True,

            "movies":
                data.get(
                    "results",
                    []
                )

        }), 200


    except requests.RequestException as e:

        print(
            "TMDB search error:"
        )

        print(e)


        return jsonify({

            "success": False,

            "message":
                "Could not connect to TMDB."

        }), 502


# =========================================================
# GET MOVIE DETAILS
# =========================================================

@app.route(
    "/api/movies/<int:movie_id>",
    methods=["GET"]
)
def get_movie_details(movie_id):

    if not TMDB_API_KEY:

        return jsonify({

            "success": False,

            "message":
                "TMDB API key is not configured."

        }), 500


    try:

        response = requests.get(

            f"{TMDB_BASE_URL}/movie/{movie_id}",

            params={

                "api_key":
                    TMDB_API_KEY,

                "language":
                    "en-US"

            },

            timeout=10

        )


        if response.status_code == 404:

            return jsonify({

                "success": False,

                "message":
                    "Movie not found."

            }), 404


        if not response.ok:

            return jsonify({

                "success": False,

                "message":
                    "TMDB request failed."

            }), response.status_code


        movie =response.json()


        return jsonify({

            "success": True,

            "movie":
                movie

        }), 200


    except requests.RequestException as e:

        print(
            "TMDB details error:"
        )

        print(e)


        return jsonify({

            "success": False,

            "message":
                "Could not connect to TMDB."

        }), 502
# =========================================================
# AUTH PAGES
# =========================================================

@app.route("/login.html", methods=["GET"])
def login_page():

    return send_from_directory(
        BASE_DIR,
        "login.html"
    )


@app.route("/signup.html", methods=["GET"])
def signup_page():

    return send_from_directory(
        BASE_DIR,
        "signup.html"
    )
# =========================================================
# SETTINGS
# =========================================================

FFMPEG = shutil.which("ffmpeg")

WHISPER_MODEL_NAME = "tiny"


# =========================================================
# FRONTEND FILE
# =========================================================

ANALYSIS_HTML = os.path.join(
    BASE_DIR,
    "analysis.html"
)


# =========================================================
# MODEL DIRECTORY
# =========================================================
#
# Put these TWO trained files in:
#
#   Dashboard/
#       app.py
#       models/
#           tfidf_vectorizer.pkl
#           sentiment_model.pkl
#
# sentiment_model.pkl = your FIRST uploaded calibrated
#                       Logistic Regression model
# tfidf_vectorizer.pkl = your uploaded TF-IDF vectorizer
#
# The model and vectorizer MUST be the matching pair used
# during training.
# =========================================================

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)


TFIDF_PATH = os.path.join(
    MODEL_DIR,
    "tfidf_vectorizer.pkl"
)


SENTIMENT_MODEL_PATH = os.path.join(
    MODEL_DIR,
    "sentiment_model.pkl"
)


# =========================================================
# CHECK ANALYSIS.HTML
# =========================================================

if not os.path.exists(
    ANALYSIS_HTML
):

    print()
    print("WARNING: analysis.html was not found!")
    print()
    print(
        "Expected location:"
    )
    print(
        ANALYSIS_HTML
    )
    print()


# =========================================================
# LOAD WHISPER
# =========================================================


whisper_model = None



# =========================================================
# LOAD TRAINED SENTIMENT MODELS
# =========================================================

print(
    "======================================"
)

print(
    "Loading trained sentiment models..."
)

print(
    "======================================"
)


# Check TF-IDF

if not os.path.exists(
    TFIDF_PATH
):

    raise FileNotFoundError(

        "tfidf_vectorizer.pkl was not found.\n\n"
        "Expected location:\n"
        + TFIDF_PATH

    )


# Check sentiment model

if not os.path.exists(
    SENTIMENT_MODEL_PATH
):

    raise FileNotFoundError(

        "sentiment_model.pkl was not found.\n\n"
        "Expected location:\n"
        + SENTIMENT_MODEL_PATH

    )


# Load TF-IDF

tfidf_vectorizer = joblib.load(
    TFIDF_PATH
)


# Load trained sentiment model

sentiment_model = joblib.load(
    SENTIMENT_MODEL_PATH
)


print(
    "TF-IDF vectorizer loaded!"
)

print(
    "Sentiment model loaded!"
)


# =========================================================
# MODEL INFORMATION
# =========================================================

try:

    print(
        "Model classes:",
        sentiment_model.classes_
    )

except Exception:

    print(
        "Model classes could not be read."
    )


try:

    print(
        "TF-IDF features:",
        len(
            tfidf_vectorizer.vocabulary_
        )
    )

except Exception:

    print(
        "TF-IDF feature count could not be read."
    )


# =========================================================
# SENTIMENT LABELS
# =========================================================
#
# Prefer the labels stored inside the trained model.
# This is important because a calibrated Logistic Regression
# model may store string classes such as:
#
#   ['negative', 'neutral', 'positive']
#
# rather than integer labels 0, 1, 2.
# =========================================================

def normalize_sentiment_label(label):

    value = str(label).strip().lower()

    if value in ("positive", "pos", "2"):
        return "Positive"

    if value in ("negative", "neg", "0"):
        return "Negative"

    if value in ("neutral", "neu", "1"):
        return "Neutral"

    return str(label).strip().capitalize()


def get_model_classes():

    if hasattr(sentiment_model, "classes_"):
        return list(sentiment_model.classes_)

    return []


# =========================================================
# CHECK FFMPEG
# =========================================================

if not os.path.exists(
    FFMPEG
):

    print()
    print(
        "WARNING: FFmpeg was NOT found!"
    )

    print(
        FFMPEG
    )

    print()

else:

    print(
        "FFmpeg found successfully!"
    )


# =========================================================
# ROUTE: HOME
# =========================================================

# IMPORTANT:
#
# When you open:
#
# http://127.0.0.1:5000/
#
# Flask will now open analysis.html
# instead of returning JSON.

# =========================================================
# ROUTE: HOME
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    # User is NOT logged in
    if "user_id" not in session:

        return send_from_directory(
            BASE_DIR,
            "login.html"
        )

    # User IS logged in
    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# =========================================================
# ROUTE: ANALYSIS PAGE
# =========================================================

# You can also open:
#
# http://127.0.0.1:5000/analysis

@app.route(
    "/analysis",
    methods=["GET"]
)

def analysis_page():

    return send_from_directory(

        BASE_DIR,

        "analysis.html"

    )



# =========================================================
# SERVE CSS / JS / IMAGES
# =========================================================

# This allows analysis.html to load:
#
# style.css
# BMT.jpeg
# other frontend files
#
# from the same folder.

@app.route(
    "/<path:filename>",
    methods=["GET"]
)

def serve_frontend_file(
    filename
):

    file_path = os.path.join(
        BASE_DIR,
        filename
    )


    # Prevent accessing files
    # outside BASE_DIR

    if not os.path.abspath(
        file_path
    ).startswith(
        os.path.abspath(
            BASE_DIR
        )
    ):

        return jsonify({

            "success": False,

            "error":
                "Invalid file path."

        }), 403


    if os.path.isfile(
        file_path
    ):

        return send_from_directory(

            BASE_DIR,

            filename

        )


    return jsonify({

        "success": False,

        "error":
            "File not found."

    }), 404


# =========================================================
# CONVERT AUDIO / VIDEO TO WAV
# =========================================================

def convert_to_wav(
    input_file,
    output_file
):


    command = [

        FFMPEG,

        "-y",

        "-i",
        input_file,

        "-vn",

        "-ac",
        "1",

        "-ar",
        "16000",

        "-c:a",
        "pcm_s16le",

        output_file

    ]


    result = subprocess.run(

        command,

        stdout=subprocess.PIPE,

        stderr=subprocess.PIPE,

        text=True

    )


    if result.returncode != 0:

        print()
        print(
            "FFmpeg ERROR:"
        )

        print(
            result.stderr
        )

        raise Exception(

            "Could not extract audio "
            "from the uploaded file."

        )


    if not os.path.exists(
        output_file
    ):

        raise Exception(

            "Audio extraction failed."

        )


    if os.path.getsize(
        output_file
    ) < 1000:

        raise Exception(

            "The file does not contain "
            "usable audio."

        )


# =========================================================
# WHISPER TRANSCRIPTION
# =========================================================
def transcribe(wav_file):

    global whisper_model

    print()
    print("Transcribing English speech...")

    # Load Whisper only when transcription is actually requested
    if whisper_model is None:

        print()
        print("Loading Whisper model...")

        whisper_model = whisper.load_model(
            WHISPER_MODEL_NAME
        )

        print(
            "Whisper model loaded successfully!"
        )

    result = whisper_model.transcribe(

        wav_file,

        language="en",

        task="transcribe",

        fp16=False,

        temperature=0,

        condition_on_previous_text=False

    )

    text = result.get(
        "text",
        ""
    ).strip()

    if not text:

        raise Exception(
            "No English speech could be detected."
        )

    print()
    print("Transcript:")
    print(text)
    print()

    return text

# =========================================================
# AUDIO / VIDEO → TEXT
# =========================================================

@app.route(
    "/transcribe",
    methods=["POST"]
)

def transcribe_file():


    temp_dir = None


    try:


        # -------------------------------------------------
        # CHECK FILE
        # -------------------------------------------------

        if "file" not in request.files:

            return jsonify({

                "success": False,

                "error":
                    "No audio or video file "
                    "was received."

            }), 400


        uploaded_file = (
            request.files["file"]
        )


        if uploaded_file.filename == "":

            return jsonify({

                "success": False,

                "error":
                    "No file was selected."

            }), 400


        # -------------------------------------------------
        # TEMP DIRECTORY
        # -------------------------------------------------

        temp_dir = tempfile.mkdtemp(

            prefix="flick_"

        )


        unique_id = str(
            uuid.uuid4()
        )


        original_name = (
            uploaded_file.filename
        )


        extension = os.path.splitext(
            original_name
        )[1].lower()


        if not extension:

            extension = ".webm"


        input_file = os.path.join(

            temp_dir,

            unique_id + extension

        )


        wav_file = os.path.join(

            temp_dir,

            unique_id + ".wav"

        )


        # -------------------------------------------------
        # SAVE UPLOADED FILE
        # -------------------------------------------------

        uploaded_file.save(
            input_file
        )


        print()
        print(
            "======================================"
        )

        print(
            "Received file:"
        )

        print(
            original_name
        )

        print(
            "======================================"
        )


        # -------------------------------------------------
        # EXTRACT AUDIO
        # -------------------------------------------------

        convert_to_wav(

            input_file,

            wav_file

        )


        # -------------------------------------------------
        # WHISPER
        # -------------------------------------------------

        text = transcribe(
            wav_file
        )


        # -------------------------------------------------
        # RETURN TEXT
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "text":
                text

        })


    except Exception as e:


        print()
        print(
            "TRANSCRIPTION ERROR:"
        )

        print(
            str(e)
        )

        print()


        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500


    finally:


        # -------------------------------------------------
        # DELETE TEMP FILES
        # -------------------------------------------------

        if (

            temp_dir

            and

            os.path.exists(
                temp_dir
            )

        ):

            try:


                for filename in os.listdir(
                    temp_dir
                ):


                    file_path = os.path.join(

                        temp_dir,

                        filename

                    )


                    if os.path.isfile(
                        file_path
                    ):

                        os.remove(
                            file_path
                        )


                os.rmdir(
                    temp_dir
                )


            except Exception:

                pass


# =========================================================
# SENTIMENT PREDICTION
# =========================================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    try:

        data = request.get_json(silent=True) or {}

        text = data.get(
            "text",
            data.get("review", "")
        )

        text = str(text).strip()

        if not text:

            return jsonify({
                "success": False,
                "error": "Review text is empty."
            }), 400

        movie_id = data.get("movie_id")

        movie_title = str(
            data.get("movie_title", "")
        ).strip()

        movie_poster = str(
            data.get("movie_poster", "")
        ).strip()

        print()
        print("======================================")
        print("SENTIMENT ANALYSIS")
        print("======================================")
        print("Review:")
        print(text)
        print("Movie:")
        print(movie_title if movie_title else "No movie selected")

        text_vector = tfidf_vectorizer.transform([text])

        raw_prediction = sentiment_model.predict(
            text_vector
        )[0]

        sentiment = normalize_sentiment_label(
            raw_prediction
        )

        confidence = None

        probabilities_output = {
            "negative": 0.0,
            "neutral": 0.0,
            "positive": 0.0
        }

        if hasattr(sentiment_model, "predict_proba"):

            probabilities = sentiment_model.predict_proba(
                text_vector
            )[0]

            classes = get_model_classes()

            for class_name, probability in zip(
                classes,
                probabilities
            ):

                normalized = normalize_sentiment_label(
                    class_name
                )

                key = normalized.lower()

                if key in probabilities_output:

                    probabilities_output[key] = round(
                        float(probability) * 100,
                        2
                    )

            # Relative score = probability of the sentiment
            # predicted by Logistic Regression.
            predicted_key = sentiment.lower()
            confidence = round(
                float(
                    probabilities_output.get(
                        predicted_key,
                        max(probabilities_output.values())
                    )
                ),
                2
            )

        if confidence is None:

            confidence = 0.0

            if hasattr(sentiment_model, "decision_function"):

                scores = np.asarray(
                    sentiment_model.decision_function(
                        text_vector
                    )
                )

                if scores.ndim == 2:

                    row = scores[0]
                    shifted = row - np.max(row)
                    exp_scores = np.exp(shifted)
                    fallback_probs = (
                        exp_scores / np.sum(exp_scores)
                    )

                    confidence = round(
                        float(np.max(fallback_probs)) * 100,
                        2
                    )

                else:

                    confidence = round(
                        float(
                            1 / (
                                1 + np.exp(
                                    -abs(float(scores[0]))
                                )
                            )
                        ) * 100,
                        2
                    )

        history_saved = False

        if (
            "user_id" in session
            and history_collection is not None
        ):

            history_collection.insert_one({

                "user_id": session["user_id"],

                "user_email": session.get(
                    "user_email",
                    ""
                ),

                "review": text,

                "sentiment": sentiment,

                "prediction": sentiment,

                "confidence": confidence,

                "probabilities": probabilities_output,

                "movie_id": movie_id,

                "movie_title": movie_title,

                "movie_poster": movie_poster,

                "created_at": datetime.utcnow()

            })

            history_saved = True

            print("Review history saved.")

        else:

            print(
                "Review history NOT saved - user is not logged in "
                "or database connection is unavailable."
            )

        print("Prediction:", sentiment)
        print("Confidence:", confidence, "%")
        print("Probabilities:", probabilities_output)
        print("History saved:", history_saved)
        print("======================================")
        print()

        return jsonify({

            "success": True,

            "prediction": sentiment,

            "sentiment": sentiment,

            "confidence": confidence,

            "relative_score": confidence,

            "probabilities": probabilities_output,

            "text": text,

            "movie": {
                "id": movie_id,
                "title": movie_title,
                "poster": movie_poster
            },

            "history_saved": history_saved

        })

    except Exception as e:

        print()
        print("PREDICTION ERROR:")
        print(str(e))
        print()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# API STATUS
# =========================================================

@app.route(
    "/api/status",
    methods=["GET"]
)

def api_status():


    return jsonify({

        "success": True,

        "status":
            "FLICK AI backend is running",

        "services": [

            "English Audio to Text",

            "English Video to Text",

            "Movie Sentiment Analysis"

        ],

        "endpoints": [

            "/transcribe",

            "/predict"

        ]

    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":


    print()
    print(
        "======================================"
    )

    print(
        "          FLICK AI BACKEND"
    )

    print(
        "================="
        "====================="
    )

    print(
        "Whisper       : READY"
    )

    print(
        "TF-IDF        : READY"
    )

    print(
        "Sentiment     : READY"
    )

    print(
        "Model classes  : "
        + str(get_model_classes())
    )

    print(
        "FFmpeg        : READY"
    )

    print(
        "Frontend      : READY"
    )

    print(
        "======================================"
    )

    print(
        "FLICK WEBSITE:"
    )

    print(
        "http://127.0.0.1:5000/"
    )

    print(
        "======================================"
    )

    print(
        "API STATUS:"
    )

    print(
        "http://127.0.0.1:5000/api/status"
    )

    print(
        "======================================"
    )


    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )