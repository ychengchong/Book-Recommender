import unittest

from book_recommender.analysis import (
    EMOTION_LABELS,
    calculate_max_emotion_scores,
    predict_category,
)


class AnalysisTests(unittest.TestCase):
    def test_emotion_scores_follow_labels_in_any_order(self):
        first_sentence = []
        second_sentence = []
        for index, label in enumerate(EMOTION_LABELS):
            first_sentence.append({"label": label, "score": index / 10})
            second_sentence.append({"label": label, "score": (6 - index) / 10})
        second_sentence.reverse()

        result = calculate_max_emotion_scores([first_sentence, second_sentence])
        self.assertEqual(result["joy"], 0.3)
        self.assertEqual(result["neutral"], 0.6)
        self.assertEqual(result["sadness"], 0.4)
        self.assertEqual(result["surprise"], 0.5)

    def test_missing_emotions_are_reported(self):
        with self.assertRaisesRegex(ValueError, "No predictions"):
            calculate_max_emotion_scores([])

    def test_category_uses_the_highest_score(self):
        def classifier(description, categories):
            return {"labels": categories, "scores": [0.2, 0.8]}

        category = predict_category("An example", classifier, ["Fiction", "Nonfiction"])
        self.assertEqual(category, "Nonfiction")
