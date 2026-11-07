# Applicable checks

Run the offline commands in the README after editing selection, formatting or
startup validation. Synthetic fixtures cover semantic order, duplicate/unknown
hits, category filtering, tone ranking before truncation, malformed index IDs,
CSV validation, missing images and missing data. They do not measure model quality.

Before a real local smoke test, prepare aligned catalogue and document files and
configure provider access. Check a query with no filter, each category/tone,
blank text, missing image, and an empty result. Confirm displayed IDs correspond
to retrieval hits. Starting the app embeds the corpus and costs money; it is not
part of offline checks.

Before quality comparisons, define cases and criteria in the problem brief's
evaluation process. Record dataset hashes, model revisions, embedding model,
source revision, dependency lock, query set, filters and output IDs. Keep selection
queries separate from final confirmation. Do not silently omit failed cases.

No release, streaming, fraud or multi-tenant checklist is applicable to the current
local research app. Full model execution and provider integration are unverified
until a data-backed run is recorded.
