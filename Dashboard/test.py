import pickle

MODEL_PATH = "models/sentiment/logistic_75k_calibrated.pkl"
VECTORIZER_PATH = "models/sentiment/tfidf_75k_vectorizer.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

with open(VECTORIZER_PATH, "rb") as f:
    vectorizer = pickle.load(f)


def predict_sentiment(review):

    review_tfidf = vectorizer.transform([review])

    prediction = model.predict(review_tfidf)[0]

    probabilities = model.predict_proba(review_tfidf)[0]

    classes = model.classes_

    probability_dict = {
        class_name: float(probability)
        for class_name, probability in zip(classes, probabilities)
    }

    confidence = max(probability_dict.values())

    return {
        "sentiment": prediction,
        "confidence": round(confidence * 100, 2),
        "probabilities": {
            "negative": round(
                probability_dict.get("negative", 0) * 100, 2
            ),
            "neutral": round(
                probability_dict.get("neutral", 0) * 100, 2
            ),
            "positive": round(
                probability_dict.get("positive", 0) * 100, 2
            )
        }
    }


while True:

    review = input("\nEnter review (or type exit): ")

    if review.lower() == "exit":
        break

    result = predict_sentiment(review)

    print("\n-----------------------------")
    print("Sentiment :", result["sentiment"])
    print("Confidence:", result["confidence"], "%")

    print("\nProbabilities:")
    print("Positive:", result["probabilities"]["positive"], "%")
    print("Neutral :", result["probabilities"]["neutral"], "%")
    print("Negative:", result["probabilities"]["negative"], "%")
    print("-----------------------------")