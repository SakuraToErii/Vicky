# Ask Search-First Without `index.md`

Historical migration note for the shift from `wiki/index.md` to search-first retrieval.

## Goal

Remove `wiki/index.md` as a maintained support file and make `ask` retrieval start from Obsidian CLI search plus semantic relation expansion.

## Rationale

The vault already has two stronger entry points:

- Obsidian CLI for machine retrieval: `search`, `search:context`, `property:read`, `links`, `backlinks`, and `outline`.
- Obsidian Bases for human browsing and relation review.

`wiki/index.md` duplicated metadata that can be discovered from Markdown files and properties.

## Implementation Checklist

1. Done: delete `wiki/index.md`.
2. Done: remove `index.md` from required support files in lint.
3. Done: remove `INDEX_TEMPLATE` and `rebuild-index` from `.tools/research_wiki.py`.
4. Done: remove `index.md` reset and dry-run behavior from `.tools/reset_wiki.py`.
5. Done: change `ask` to:
   - derive search terms first from the user question;
   - read `wiki/bases/Semantic Relations.base` second to confirm relation fields and views;
   - run `obsidian search` and `obsidian search:context`;
   - expand strong candidates through relation-property search;
   - expand strong candidates through `links`, `backlinks`, `property:read`, and `outline`;
   - use `obsidian files folder=wiki ext=md` only as a fallback for broad or sparse queries.
6. Done: remove index rebuild steps from `ingest`, `edit`, `init`, and saved output workflows.
7. Done: update docs and README so Bases are relation workbenches and Obsidian CLI search is the primary retrieval entry.
8. Done: update tests around lint, reset, and wiki initialization.
9. Done: remove `wiki/index.md` from `.gitattributes`.
10. Done: verify:
    - live docs and skills are clear of `wiki/index.md` requirements;
    - `.venv/bin/python -m pytest`: 58 passed;
    - `.venv/bin/python .tools/lint.py --wiki-dir wiki --json`: 0 issues;
    - `git diff --check`: clean.

## Retrieval Contract

`ask` should build candidate pages from content and metadata, then use semantic links to expand context. Bases define the relation workbench and frozen relation fields. Markdown pages remain the source of truth.

## Rollback

Restore `wiki/index.md` by reintroducing `INDEX_TEMPLATE`, `rebuild-index`, lint support-file validation, reset behavior, and the old `ask` catalog-read step.
