"""Load book data and turn search results into recommendations."""

import csv
import math
from pathlib import Path

MISSING_COVER = Path(__file__).parent / "assets" / "cover-not-found.svg"

TONE_COLUMNS = {
    "Happy": "joy",
    "Surprising": "surprise",
    "Angry": "anger",
    "Suspenseful": "fear",
    "Sad": "sadness",
}
REQUIRED_COLUMNS = {
    "isbn13",
    "title",
    "authors",
    "description",
    "thumbnail",
    "simple_categories",
    *TONE_COLUMNS.values(),
}


def load_catalogue(path):
    """Read the CSV and check for missing or invalid book data."""
    catalogue = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Catalogue missing columns: {', '.join(sorted(missing))}")

        for line, row in enumerate(reader, start=2):
            isbn = (row["isbn13"] or "").strip()
            if len(isbn) != 13 or not isbn.isascii() or not isbn.isdigit():
                raise ValueError(f"Invalid ISBN-13 at catalogue line {line}")
            if isbn in catalogue:
                raise ValueError(f"Duplicate ISBN-13 at catalogue line {line}")

            for field in ("title", "description", "simple_categories"):
                if not (row[field] or "").strip():
                    raise ValueError(f"Missing {field} at catalogue line {line}")
            row["authors"] = (row["authors"] or "").strip() or "Unknown author"
            # Emotion scores should be numbers between 0 and 1.
            for field in TONE_COLUMNS.values():
                try:
                    score = float(row[field])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid {field} at catalogue line {line}"
                    ) from exc
                if not math.isfinite(score) or not 0 <= score <= 1:
                    raise ValueError(f"Invalid {field} at catalogue line {line}")
                row[field] = score

            row["isbn13"] = isbn
            catalogue[isbn] = row

    if not catalogue:
        raise ValueError("Catalogue is empty")
    return catalogue


def get_document_isbn(document):
    """Each search document starts with the book's ISBN."""
    text = document.page_content.strip().strip('"')
    words = text.split(maxsplit=1)
    if not words:
        raise ValueError("Index document must begin with an ISBN-13")

    isbn = words[0]
    if len(isbn) != 13 or not isbn.isascii() or not isbn.isdigit():
        raise ValueError("Index document must begin with an ISBN-13")
    return isbn


def select_recommendations(catalogue, documents, category="All", tone="All", limit=16):
    """Filter the search results, sort by tone, and keep the requested number."""
    if limit < 1:
        raise ValueError("Recommendation limit must be positive")
    if tone not in (None, "All") and tone not in TONE_COLUMNS:
        raise ValueError(f"Unknown emotional tone: {tone}")
    selected = []
    seen = set()

    # Keep the search order instead of using the order of rows in the CSV.
    for document in documents:
        isbn = get_document_isbn(document)
        if isbn in seen or isbn not in catalogue:
            continue
        seen.add(isbn)

        book = catalogue[isbn]
        if category not in (None, "All") and book["simple_categories"] != category:
            continue
        selected.append(book)

    # Sort all matching candidates before choosing the final books.
    if tone not in (None, "All"):
        emotion = TONE_COLUMNS[tone]
        selected.sort(key=lambda book: book[emotion], reverse=True)
    return selected[:limit]


def gallery_items(recommendations):
    """Create a cover and caption for each recommended book."""
    results = []
    for book in recommendations:
        authors = (book.get("authors") or "").split(";")
        authors = [author.strip() for author in authors if author.strip()]
        if not authors:
            author_text = "Unknown author"
        elif len(authors) == 1:
            author_text = authors[0]
        elif len(authors) == 2:
            author_text = " and ".join(authors)
        else:
            author_text = f"{', '.join(authors[:-1])}, and {authors[-1]}"

        words = book["description"].split()
        description = " ".join(words[:30])
        if len(words) > 30:
            description += "..."

        thumbnail = (book.get("thumbnail") or "").strip()
        if thumbnail:
            if "?" in thumbnail:
                thumbnail += "&fife=w800"
            else:
                thumbnail += "?fife=w800"
        else:
            thumbnail = str(MISSING_COVER)

        caption = f"{book['title']} by {author_text}: {description}"
        results.append((thumbnail, caption))
    return results
