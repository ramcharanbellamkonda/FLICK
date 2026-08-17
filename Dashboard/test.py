import joblib

MODEL_PATH = "models/sentiment_model.pkl"
VECTORIZER_PATH = "models/tfidf_vectorizer.pkl"

print("Loading Logistic Regression model...")

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

print("Model loaded successfully!")
print("TF-IDF loaded successfully!")

reviews = [
    "The movie was boring and completely disappointing.",
    "The movie was okay, nothing particularly special.",
    "The acting was amazing and the story was fantastic."
]

for review in reviews:

    X = vectorizer.transform([review])

    prediction = model.predict(X)[0]

    # Model already returns:
    # negative / neutral / positive
    sentiment = str(prediction).capitalize()

    print()
    print("Review:", review)
    print("Sentiment:", sentiment)

print()
print("All model tests completed successfully!")