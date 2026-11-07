# Book Recommender

A local Gradio app that retrieves books by description, filters by category,
and optionally ranks the retrieved candidates by emotional tone.

## Setup (PowerShell)

Use Python 3.11 and uv. The original dependency versions are retained during
cleanup; this is a local research application, not a reviewed public deployment.

```powershell
python -m pip install uv
uv sync --locked --python 3.11
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Do not commit that file. `pyproject.toml` defines
the app dependencies and optional notebook packages; `uv.lock` pins their resolved
versions. These are the only dependency files.

## Data preparation

The repository does not contain the catalogue or generated data. The existing
notebooks remain at the root so their relative paths continue to work. Install
the optional notebook packages when you need them:

```powershell
uv sync --locked --extra research --python 3.11
uv run --locked --extra research jupyter lab
```

The research option is included in the same lockfile, but has not been installed
or used to rerun models during cleanup. Transformers is
pinned to 4.46.3 because the original 4.47.1 requires a tokenizers version that
conflicts with Chroma 0.5.23. Model results must be revalidated before comparison.

Run notebooks from the repository root in this order:

1. `data-exploration.ipynb`: downloads `dylanjcastillo/7k-books-with-metadata`
   via KaggleHub and writes `books_cleaned.csv`.
2. `text-classification.ipynb`: maps categories and fills missing categories
   using `facebook/bart-large-mnli`; writes `books_with_categories.csv`.
3. `sentiment-analysis.ipynb`: computes emotion scores using
   `j-hartmann/emotion-english-distilroberta-base`; writes `books_with_emotions.csv`.
4. `vector-search.ipynb`: writes `tagged_description.txt` from the cleaned catalogue.
   Later cells build an OpenAI index and make paid requests; they are not required
   to export this file.

The classification notebooks currently select Apple's `mps` device. On Windows,
change it to `device=-1` for CPU, or an appropriate CUDA device if configured.
Downloads, model runs and paid calls are manual actions. Snapshot IDs and model
revisions have not been recorded by the original notebooks, so their historical
outputs are not reproducible evidence. Generated CSV/TXT files are ignored.

## Run locally

Only after preparing data and configuring the key:

```powershell
uv run --locked python gradio-dashboard.py
# Alternatively, keep the two input files in another directory:
uv run --locked python -m book_recommender.dashboard --data-dir "C:\path\to\data"
```

Startup sends the tagged book descriptions to OpenAI and rebuilds an in-memory
Chroma index using `text-embedding-ada-002`. Searches also call OpenAI. Restarting
rebuilds the index and incurs embedding cost again. Launch uses Gradio's local
defaults. Missing files and invalid catalogue/index contracts fail before indexing.

## Offline checks

These use synthetic records and do not require data, API keys or runtime packages:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m unittest discover -s tests -v
python -m compileall -q src tests gradio-dashboard.py
```

The UI construction test runs when app dependencies are installed and otherwise
is skipped. Its embeddings/index are mocked; it never launches a server.
These checks verify software behaviour, not recommendation quality. No retrieval
quality or classifier improvement claim has been established. See
[project goals](docs/problem.md), [architecture](docs/architecture.md), and
[applicable checks](docs/project-checks.md).

## Updating dependencies

Edit the app dependencies or `research` option in `pyproject.toml`, then regenerate
the single lockfile:

```powershell
uv lock --python 3.11
```

The resolution cutoff in `pyproject.toml` preserves the dependency era of the original December 2024
snapshot. A deliberate dependency upgrade should remove or advance that cutoff,
then validate the application with representative data before deployment.
