# Architecture and contracts

Offline notebooks produce cleaned metadata, mapped categories, emotion scores,
and ISBN-prefixed description lines. Online startup reads the final catalogue,
validates index IDs, embeds descriptions, builds an in-memory Chroma collection,
and creates the Gradio interface. A query retrieves up to 50 documents, filters
category, optionally sorts by tone, then displays at most 16 books.

`src/book_recommender/recommendations.py` owns the catalogue contract and pure
selection/formatting code. `dashboard.py` owns file access, provider initialization,
index state and the UI. The root script delegates to the package. Imports do not
read data, build indexes or launch a server.

`analysis.py` contains the notebooks' category prediction and emotion aggregation
helpers. Emotion scores are matched by label name, not output position. The
notebooks use CPU by default and keep model runs separate from data inspection.
Saved notebook outputs are cleared. The vector notebook exports one whitespace-
normalized description per line and reuses the app's recommendation selection.

The authoritative CSV field set is `REQUIRED_COLUMNS` in the recommendations
module. ISBNs are unique 13-digit ASCII strings. Title, description and category
are nonempty. Missing authors display as "Unknown author"; five consumed emotion
scores are finite values in [0, 1].
Extra research columns are permitted. Missing thumbnails use a bundled SVG cover
placeholder. Authors are separated by semicolons. Descriptions are truncated
to 30 words for captions.

Each nonblank tagged-description line starts with ISBN-13 and contains description
text. The startup file must contain exactly one document per catalogue ISBN.
Malformed IDs, duplicates, missing files, missing fields and invalid scores stop
startup. Retrieval skips duplicate or unknown IDs, preserves similarity order,
filters category, then stably reranks tone before truncating. An empty query returns
no results and makes no search API call. Provider failures propagate; no retry or
fallback service is implemented by this project.

Index and catalogue are shared read-only after initialization. The index is not
persisted. Restart loses it and re-embeds the descriptions. Upstream corpus or
embedding changes require a new index. No tenant isolation, access-controlled
corpus, release manifest, deployed service or measured operational target exists.
Environment configuration is `.env`; actual secrets stay outside Git. Hosted
embedding behaviour can vary even with a fixed model identifier. The code and
lockfile alone do not establish exact model or data reproducibility.
