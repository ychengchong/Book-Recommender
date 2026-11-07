"""Gradio interface for the book recommender."""

import argparse
from pathlib import Path

from .recommendations import (
    TONE_COLUMNS,
    gallery_items,
    get_document_isbn,
    load_catalogue,
    select_recommendations,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_dashboard(data_dir=None):
    """Load the books, build the search index, and set up the page."""
    if data_dir is None:
        data_dir = PROJECT_ROOT
    data_dir = Path(data_dir)

    catalogue_path = data_dir / "books_with_emotions.csv"
    documents_path = data_dir / "tagged_description.txt"
    for path in (catalogue_path, documents_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"Required data missing: {path}. See README.md for preparation."
            )
    catalogue = load_catalogue(catalogue_path)

    # Import these here so the data checks can run without the app packages.
    import gradio as gr
    from dotenv import load_dotenv
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings

    load_dotenv(PROJECT_ROOT / ".env")
    documents = []
    with documents_path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            description = line.strip()
            if description:
                documents.append(Document(page_content=description))

    if not documents:
        raise ValueError("Tagged descriptions file is empty")

    # Both files need to contain the same books before we pay for embeddings.
    document_ids = []
    for document in documents:
        document_ids.append(get_document_isbn(document))
    if len(document_ids) != len(set(document_ids)) or set(document_ids) != set(
        catalogue
    ):
        raise ValueError(
            "Tagged descriptions must contain exactly one document per catalogue ISBN"
        )

    # This calls OpenAI and rebuilds the index each time the app starts.
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    database = Chroma.from_documents(documents, embeddings)

    def recommend(query, category, tone):
        if not query or not query.strip():
            return []
        search_results = database.similarity_search(
            query.strip(), k=min(50, len(catalogue))
        )
        books = select_recommendations(catalogue, search_results, category, tone)
        return gallery_items(books)

    book_categories = set()
    for book in catalogue.values():
        book_categories.add(book["simple_categories"])
    categories = ["All"] + sorted(book_categories)
    tones = ["All"] + list(TONE_COLUMNS)

    with gr.Blocks(theme=gr.themes.Glass()) as dashboard:
        gr.Markdown("# Semantic book recommender")
        with gr.Row():
            query = gr.Textbox(
                label="Please enter a description of a book:",
                placeholder="e.g., A story about forgiveness",
            )
            category = gr.Dropdown(
                choices=categories, label="Select a category:", value="All"
            )
            tone = gr.Dropdown(
                choices=tones, label="Select an emotional tone:", value="All"
            )
            submit = gr.Button("Find recommendations")
        gr.Markdown("## Recommendations")
        output = gr.Gallery(label="Recommended books", columns=8, rows=2)
        submit.click(fn=recommend, inputs=[query, category, tone], outputs=output)
    return dashboard


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    dashboard = create_dashboard(args.data_dir)
    dashboard.launch()


if __name__ == "__main__":
    main()
