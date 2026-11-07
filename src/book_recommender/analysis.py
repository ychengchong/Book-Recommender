"""Small helpers used by the classification notebooks."""

EMOTION_LABELS = ["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]


def predict_category(description, classifier, categories):
    """Return the category with the highest model score."""
    prediction = classifier(description, categories)
    best_score = max(prediction["scores"])
    best_index = prediction["scores"].index(best_score)
    return prediction["labels"][best_index]


def calculate_max_emotion_scores(predictions):
    """Keep the highest sentence score for each emotion in a description."""
    scores = {}
    for label in EMOTION_LABELS:
        scores[label] = []

    for sentence_predictions in predictions:
        for prediction in sentence_predictions:
            label = prediction["label"]
            scores[label].append(prediction["score"])

    max_scores = {}
    for label in EMOTION_LABELS:
        if not scores[label]:
            raise ValueError(f"No predictions for emotion: {label}")
        max_scores[label] = max(scores[label])
    return max_scores
