import csv
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from book_recommender.recommendations import (
    REQUIRED_COLUMNS,
    gallery_items,
    load_catalogue,
    select_recommendations,
)


def book(isbn, category="Fiction", joy=0.1):
    return {
        "isbn13": isbn,
        "title": "Example",
        "authors": "A;B",
        "description": "A short story.",
        "thumbnail": "",
        "simple_categories": category,
        "joy": joy,
        "surprise": 0.2,
        "anger": 0.3,
        "fear": 0.4,
        "sadness": 0.5,
    }


def docs(*isbns):
    return [
        SimpleNamespace(page_content=f"{isbn} Example description") for isbn in isbns
    ]


class RecommendationsTests(unittest.TestCase):
    def setUp(self):
        books = [
            book("9780000000001"),
            book("9780000000002", joy=0.9),
            book("9780000000003", category="Nonfiction"),
        ]
        self.catalogue = {}
        for row in books:
            self.catalogue[row["isbn13"]] = row

    def test_retrieval_order_and_duplicate_hits(self):
        result = select_recommendations(
            self.catalogue,
            docs("9780000000002", "9780000000001", "9780000000002", "9780000000099"),
        )
        self.assertEqual(
            [row["isbn13"] for row in result], ["9780000000002", "9780000000001"]
        )

    def test_category_filter_and_tone_sort_before_limit(self):
        result = select_recommendations(
            self.catalogue,
            docs(*self.catalogue),
            category="Fiction",
            tone="Happy",
            limit=1,
        )
        self.assertEqual([row["isbn13"] for row in result], ["9780000000002"])

    def test_invalid_document_is_explicit(self):
        with self.assertRaisesRegex(ValueError, "ISBN-13"):
            select_recommendations(self.catalogue, docs("not-an-isbn"))

    def test_missing_cover_and_author_formatting(self):
        image, caption = gallery_items([self.catalogue["9780000000001"]])[0]
        self.assertTrue(Path(image).is_file())
        self.assertEqual(caption, "Example by A and B: A short story.")

    def test_missing_authors_can_be_loaded_and_displayed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "books.csv"
            for authors in (None, "", "   ", "; ;"):
                with self.subTest(authors=authors):
                    row = book("9780000000001")
                    row["authors"] = authors
                    with path.open("w", encoding="utf-8", newline="") as handle:
                        writer = csv.DictWriter(
                            handle, fieldnames=sorted(REQUIRED_COLUMNS)
                        )
                        writer.writeheader()
                        writer.writerow(row)

                    catalogue = load_catalogue(path)
                    self.assertEqual(len(catalogue), 1)
                    _, caption = gallery_items(list(catalogue.values()))[0]
                    self.assertEqual(
                        caption, "Example by Unknown author: A short story."
                    )

    def test_csv_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "books.csv"

            def write(rows):
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=sorted(REQUIRED_COLUMNS))
                    writer.writeheader()
                    writer.writerows(rows)

            rows = list(self.catalogue.values())
            write(rows)
            self.assertEqual(set(load_catalogue(path)), set(self.catalogue))
            write([rows[0], rows[0]])
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_catalogue(path)
            write([{**rows[0], "joy": "nan"}])
            with self.assertRaisesRegex(ValueError, "Invalid joy"):
                load_catalogue(path)
            write([{**rows[0], "title": ""}])
            with self.assertRaisesRegex(ValueError, "Missing title"):
                load_catalogue(path)

    def test_missing_data_fails_before_external_imports(self):
        from book_recommender.dashboard import create_dashboard

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, "Required data missing"):
                create_dashboard(directory)

    @unittest.skipUnless(
        importlib.util.find_spec("gradio"), "App environment not installed"
    )
    def test_dashboard_and_missing_cover_with_mocked_embeddings(self):
        from book_recommender.dashboard import create_dashboard

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"GRADIO_ANALYTICS_ENABLED": "False"}),
        ):
            directory = Path(directory)
            rows = list(self.catalogue.values())
            with (directory / "books_with_emotions.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=sorted(REQUIRED_COLUMNS))
                writer.writeheader()
                writer.writerows(rows)
            (directory / "tagged_description.txt").write_text(
                "\n".join(f"{row['isbn13']} {row['description']}" for row in rows),
                encoding="utf-8",
            )
            with (
                patch("langchain_chroma.Chroma.from_documents") as build,
                patch("langchain_openai.OpenAIEmbeddings"),
            ):
                dashboard = create_dashboard(directory)
                self.assertTrue(dashboard.config["components"])
                build.assert_called_once()
            import gradio as gr

            gallery = gr.Gallery().postprocess(gallery_items([rows[0]]))
            self.assertEqual(
                gallery.root[0].caption, "Example by A and B: A short story."
            )


if __name__ == "__main__":
    unittest.main()
