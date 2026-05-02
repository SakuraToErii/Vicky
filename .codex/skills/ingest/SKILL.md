---
name: ingest
description: Use when the user wants to ingest one prepared source into the Vicky wiki, create the source page, and perform explicitly requested knowledge-page updates.
---

# Ingest

Turn one prepared source into a source page plus explicitly requested knowledge-page updates.

## Inputs

- `source`: a local `.tex`, `.md`, `.txt`, `.html`, or `.htm` path, usually under `raw/papers/` or `raw/web/`

## Outputs

- `wiki/sources/{slug}.md`
- explicit user-requested updates under `wiki/concepts/`, `wiki/theorems/`, `wiki/people/`, `wiki/ideas/`, `wiki/topics/`, or `wiki/foundations/`
- `wiki/log.md` entry and lint-clean completion

## References

- `AGENTS.md` for page homes, relation fields, and the new-page post-processing contract

## Template Map

Use `Wiki_Source` for source pages. Use the matching `Wiki_*` template for explicit knowledge-page targets.

## Workflow

1. Resolve the local source path. Derive `<title>` from the source filename, generate `{slug}` with `.venv/bin/python .codex/skills/ingest/scripts/slug.py "<title>"`, then run source duplicate and slug occupancy checks with `.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki source "<title>"` and `obsidian files folder=wiki ext=md | rg '(^|/){slug}\\.md$' || true`.
2. Create `wiki/sources/{slug}.md` with `obsidian create path="wiki/sources/{slug}.md" template="Wiki_Source"`. Ensure `source_path` points to the original source file.
3. Edit the markdown file directly for properties and body content. Fill source title, source kind, year, source path, summary (follow `references/source-summary.md`), and related links from the source. For sources under `raw/papers/`, use `.venv/bin/python .codex/skills/ingest/scripts/fetch_s2.py` for useful Semantic Scholar metadata.
4. For explicit knowledge-page targets, follow the `AGENTS.md` new-page post-processing contract: duplicate check for concepts/theorems/ideas, exact target path, matching template, relation properties, `## Relations`, reverse mentions, log entry, and lint. Finish one new page before starting another.
5. Verify changed pages with `git diff -- <exact-target-path>`, append `wiki/log.md` with `obsidian append file=log content="## [YYYY-MM-DD] ingest | ..."`, then run `.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json`.

## Constraints

- Treat `raw/` as source input.
- `wiki/sources/` is the canonical home for per-source summaries.
- `wiki/sources/` is the automatic citation anchor for raw files.
- Ingest creates the source page by default. Create or update knowledge pages only when the user explicitly names them.
- Treat lint-clean completion as the end of the page post-processing path.
- Use wikilinks for existing pages and user-approved new pages.
