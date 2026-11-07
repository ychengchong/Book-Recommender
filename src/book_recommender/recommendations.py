"""Offline catalogue validation, recommendation ranking, and gallery formatting."""

import csv
import math
from pathlib import Path

MISSING_COVER = Path(__file__).parent / "assets" / "cover-not-found.svg"

TONE_COLUMNS = {
    "Happy": "joy", "Surprising": "surprise", "Angry": "anger",
    "Suspenseful": "fear", "Sad": "sadness",
}
REQUIRED_COLUMNS = {
    "isbn13", "title", "authors", "description", "thumbnail", "simple_categories",
    *TONE_COLUMNS.values(),
}


def load_catalogue(path):
    """Read unique ISBN records with finite emotion scores in [0, 1]."""
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
            for field in ("title", "authors", "description", "simple_categories"):
                if not (row[field] or "").strip():
                    raise ValueError(f"Missing {field} at catalogue line {line}")
            for field in TONE_COLUMNS.values():
                try:
                    score = float(row[field])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid {field} at catalogue line {line}") from exc
                if not math.isfinite(score) or not 0 <= score <= 1:
                    raise ValueError(f"Invalid {field} at catalogue line {line}")
                row[field] = score
            row["isbn13"] = isbn
            catalogue[isbn] = row
    if not catalogue:
        raise ValueError("Catalogue is empty")
    return catalogue


def select_recommendations(catalogue, documents, category="All", tone="All", limit=16):
    """Preserve retrieval order, filter category, rerank tone, then apply limit.

    Documents begin with ISBN-13. Unknown IDs and repeated hits are skipped.
    Malformed document IDs indicate an incompatible index and raise ValueError.
    """
    if limit < 1:
        raise ValueError("Recommendation limit must be positive")
    if tone not in (None, "All") and tone not in TONE_COLUMNS:
        raise ValueError(f"Unknown emotional tone: {tone}")
    selected, seen = [], set()
    for document in documents:
        parts = document.page_content.strip().strip('"').split(maxsplit=1)
        isbn = parts[0] if parts else ""
        if len(isbn) != 13 or not isbn.isascii() or not isbn.isdigit():
            raise ValueError("Index document must begin with an ISBN-13")
        if isbn in seen or isbn not in catalogue:
            continue
        seen.add(isbn)
        row = catalogue[isbn]
        if category in (None, "All") or row["simple_categories"] == category:
            selected.append(row)
    if tone not in (None, "All"):
        selected.sort(key=lambda row: row[TONE_COLUMNS[tone]], reverse=True)
    return selected[:limit]


def gallery_items(recommendations):
    results = []
    for row in recommendations:
        authors = [author.strip() for author in row["authors"].split(";")]
        if len(authors) == 1:
            author_text = authors[0]
        elif len(authors) == 2:
            author_text = " and ".join(authors)
        else:
            author_text = f"{', '.join(authors[:-1])}, and {authors[-1]}"
        words = row["description"].split()
        description = " ".join(words[:30]) + ("..." if len(words) > 30 else "")
        thumbnail = (row.get("thumbnail") or "").strip()
        if thumbnail:
            thumbnail += ("&" if "?" in thumbnail else "?") + "fife=w800"
        results.append((thumbnail or str(MISSING_COVER),
                        f"{row['title']} by {author_text}: {description}"))
    return results
