"""Explicit application startup; importing this module does not build an index."""

import argparse
from pathlib import Path

from .recommendations import TONE_COLUMNS, gallery_items, load_catalogue, select_recommendations

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_dashboard(data_dir=None):
    data_dir = Path(data_dir) if data_dir is not None else PROJECT_ROOT
    catalogue_path = data_dir / "books_with_emotions.csv"
    documents_path = data_dir / "tagged_description.txt"
    for path in (catalogue_path, documents_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required data missing: {path}. See README.md for preparation.")
    catalogue = load_catalogue(catalogue_path)

    import gradio as gr
    from dotenv import load_dotenv
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    from langchain_openai import OpenAIEmbeddings

    load_dotenv(PROJECT_ROOT / ".env")
    with documents_path.open(encoding="utf-8-sig") as handle:
        documents = [Document(page_content=line.strip()) for line in handle if line.strip()]
    # Validate index inputs before starting an embedding request.
    select_recommendations(catalogue, documents, limit=1)
    if not documents:
        raise ValueError("Tagged descriptions file is empty")
    document_ids = [doc.page_content.strip('"').split(maxsplit=1)[0] for doc in documents]
    if len(document_ids) != len(set(document_ids)) or set(document_ids) != set(catalogue):
        raise ValueError("Tagged descriptions must contain exactly one document per catalogue ISBN")
    # Retain the original in-memory index lifecycle; startup makes paid API calls.
    database = Chroma.from_documents(
        documents, OpenAIEmbeddings(model="text-embedding-ada-002")
    )

    def recommend(query, category, tone):
        if not query or not query.strip():
            return []
        documents = database.similarity_search(query.strip(), k=min(50, len(catalogue)))
        return gallery_items(select_recommendations(catalogue, documents, category, tone))

    categories = ["All"] + sorted({row["simple_categories"] for row in catalogue.values()})
    with gr.Blocks(theme=gr.themes.Glass()) as dashboard:
        gr.Markdown("# Semantic book recommender")
        with gr.Row():
            query = gr.Textbox(label="Please enter a description of a book:",
                               placeholder="e.g., A story about forgiveness")
            category = gr.Dropdown(choices=categories, label="Select a category:", value="All")
            tone = gr.Dropdown(choices=["All", *TONE_COLUMNS],
                               label="Select an emotional tone:", value="All")
            submit = gr.Button("Find recommendations")
        gr.Markdown("## Recommendations")
        output = gr.Gallery(label="Recommended books", columns=8, rows=2)
        submit.click(fn=recommend, inputs=[query, category, tone], outputs=output)
    return dashboard


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    create_dashboard(args.data_dir).launch()


if __name__ == "__main__":
    main()
