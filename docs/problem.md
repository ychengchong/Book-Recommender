# Project brief

The existing project helps a reader discover books from a natural-language
description, optional category, and emotional tone in a local Gradio interface.
Cleanup preserves that workflow and keeps the exploratory notebooks intact.

The baseline is the existing OpenAI embedding/Chroma nearest-neighbour retrieval
over tagged descriptions, with 50 candidates and at most 16 displayed books.
Category filtering precedes optional emotion reranking. Semantic order breaks
emotion ties. This cleanup fixes accidental CSV ordering and limiting before
emotion ranking; those are correctness changes, not measured quality improvements.

Data originates from the KaggleHub dataset named in the README. Licensing,
snapshot identity and redistribution permissions have not been verified. Keep
downloaded and generated data local. Descriptions and search text are sent to
OpenAI when the app is explicitly started and used.

Acceptance for cleanup: imports have no external effects, ranking and catalogue
validation have offline regression checks, setup has a resolved dependency lock,
and missing data/access requirements are documented.

Recommendation quality remains unevaluated. Before claiming improvement, record
a corpus snapshot and development queries, compare retrieval-only and tone-ranked
results on identical cases, review category/tone slices, measure relevance@16 and
coverage, then reserve separate confirmation queries. Human-reviewed thresholds
and labels must be agreed before that experiment. No latency or spending target
has been supplied.

Out of scope: training, downloads, paid evaluation, deployment, publication, and
committing or pushing changes. The repository maintainer owns dataset preparation
and the quality evaluation. No separate task tracker is configured.
