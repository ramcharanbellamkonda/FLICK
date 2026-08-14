from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import whisper
import subprocess
import os
import tempfile
import uuid
import joblib
import numpy as np


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# BASE DIRECTORY
# =========================================================

# This automatically finds the folder containing app.py

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================================================
# SETTINGS
# =========================================================

FFMPEG = r"C:\Users\sruja\Downloads\ffmpeg-9.0.1-essentials_build\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe"

WHISPER_MODEL_NAME = "base"


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

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)


# =========================================================
# TRAINED MODEL PATHS
# =========================================================

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

print(
    "======================================"
)

print(
    "Loading Whisper model..."
)

print(
    "======================================"
)


whisper_model = whisper.load_model(
    WHISPER_MODEL_NAME
)


print(
    "Whisper model loaded successfully!"
)


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

# Your trained model uses:
#
# 0 = Negative
# 1 = Neutral
# 2 = Positive

LABELS = {

    0: "Negative",

    1: "Neutral",

    2: "Positive"

}


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

@app.route(
    "/",
    methods=["GET"]
)

def home():

    return send_from_directory(

        BASE_DIR,

        "analysis.html"

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

def transcribe(
    wav_file
):


    print()
    print(
        "Transcribing English speech..."
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

            "No English speech "
            "could be detected."

        )


    print()
    print(
        "Transcript:"
    )

    print(
        text
    )

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


        # -------------------------------------------------
        # GET JSON
        # -------------------------------------------------

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({

                "success": False,

                "error":
                    "No review data was received."

            }), 400


        # -------------------------------------------------
        # GET TEXT
        # -------------------------------------------------

        text = data.get(
            "text",
            ""
        )


        if not isinstance(
            text,
            str
        ):

            text = str(
                text
            )


        text = text.strip()


        if not text:

            return jsonify({

                "success": False,

                "error":
                    "Review text is empty."

            }), 400


        print()
        print(
            "======================================"
        )

        print(
            "SENTIMENT ANALYSIS"
        )

        print(
            "======================================"
        )

        print(
            "Review:"
        )

        print(
            text
        )


        # -------------------------------------------------
        # TF-IDF
        # -------------------------------------------------

        text_vector = (

            tfidf_vectorizer.transform(

                [text]

            )

        )


        # -------------------------------------------------
        # TRAINED MODEL
        # -------------------------------------------------

        prediction = (

            sentiment_model.predict(

                text_vector

            )[0]

        )


        prediction = int(
            prediction
        )


        # -------------------------------------------------
        # LABEL
        # -------------------------------------------------

        sentiment = LABELS.get(

            prediction,

            "Unknown"

        )


        # -------------------------------------------------
        # DECISION FUNCTION
        # -------------------------------------------------

        confidence = None

        decision_score = None


        if hasattr(

            sentiment_model,

            "decision_function"

        ):


            scores = (

                sentiment_model
                .decision_function(
                    text_vector
                )

            )


            scores = np.asarray(
                scores
            )


            # -------------------------------------------------
            # MULTI-CLASS
            # -------------------------------------------------

            if scores.ndim == 2:


                row = scores[0]


                decision_score = float(

                    np.max(
                        np.abs(row)
                    )

                )


                # Relative score
                # NOT a true probability

                shifted = (

                    row -

                    np.max(row)

                )


                exp_scores = np.exp(
                    shifted
                )


                probabilities = (

                    exp_scores /

                    np.sum(
                        exp_scores
                    )

                )


                confidence = float(

                    np.max(
                        probabilities
                    )

                )


            # -------------------------------------------------
            # BINARY
            # -------------------------------------------------

            else:


                decision_score = float(

                    scores[0]

                )


        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        print()
        print(
            "Prediction:",
            prediction
        )

        print(
            "Sentiment:",
            sentiment
        )

        print(
            "Confidence:",
            confidence
        )

        print(
            "======================================"
        )

        print()


        # -------------------------------------------------
        # SEND TO FRONTEND
        # -------------------------------------------------

        return jsonify({

            "success": True,

            "prediction":
                prediction,

            "sentiment":
                sentiment,

            "confidence":
                confidence,

            "decision_score":
                decision_score,

            "text":
                text

        })


    except Exception as e:


        print()
        print(
            "PREDICTION ERROR:"
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
        "======================================"
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