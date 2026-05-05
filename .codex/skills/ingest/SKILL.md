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
- lint-clean completion

## References

- `AGENTS.md` for page homes, relation fields, and the new-page post-processing contract

## Template Map

Use `Wiki_Source` for source pages. Use the matching `Wiki_*` template for explicit knowledge-page targets.

## Workflow

Process approved knowledge pages one at a time.

1. Resolve the local source path. Derive `<title>` from the source content:
   - for sources under `raw/papers/`, use the paper title in the raw file
   - for other sources, use the first level-1 heading in the raw file
   - normalize surrounding markdown/title punctuation only as needed to recover the clean human title
   Generate `{slug}` with `.venv/bin/python .codex/skills/ingest/scripts/slug.py "<title>"`, then run source duplicate and slug occupancy checks with `.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki source "<title>"` and `obsidian files folder=wiki ext=md | rg '(^|/){slug}\\.md$' || true`.
2. Create `wiki/sources/{slug}.md` with `obsidian create path="wiki/sources/{slug}.md" template="Wiki_Source"`. Ensure `source_path` points to the original source file.
3. Edit the markdown file directly for properties and body content. Fill source title with the same `<title>` used for slug generation, then fill source kind, year, source path, summary (follow `references/source-summary.md`), and source relations. In `## Relations`, write the raw source entry as `- Raw source: [[<source_path>]]` with no extra description. For knowledge-page links such as foundations or concepts, use the actual relation label from the source-page matrix and explain the concrete role in the same sentence. Example: `- Raw source: [[raw/papers/TRPO/TRPO.md]]`. Example: `- Uses: [[total-variation-distance]] formalizes the divergence TRPO uses in its policy-improvement bound and its KL relaxation step.` For sources under `raw/papers/`, use `.venv/bin/python .codex/skills/ingest/scripts/fetch_s2.py` for useful Semantic Scholar metadata.
4. For explicit knowledge-page targets, follow the `AGENTS.md` new-page post-processing contract: duplicate check for concepts/theorems/ideas, exact target path, matching template, relation properties, `## Relations`, reverse mentions, and lint. Run the exact duplicate command for the target type, including `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki idea "<title>"` for ideas. In `## Relations`, write one bullet per target page. Start the bullet with the semantic field label such as `Derived from`, `Extends`, `Uses`, or `Compares with`, then explain the concrete role in the same sentence. A single bullet should carry both the relation type and the usage context. Example: `- Uses: [[markov-decision-process]] provides the state-transition setup needed for the discounted occupancy definition.` Finish one new page before starting another.
5. For people pages, add or confirm `key_sources`.
6. Verify changed pages with `git diff -- <exact-target-path>`.
7. Run `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json` as the completion signal.

## Constraints

- Treat `raw/` as source input.
- `wiki/sources/` is the canonical home for per-source summaries.
- `wiki/sources/` is the automatic citation anchor for raw files.
- Source slug generation follows source content titles: paper title for `raw/papers/`, first level-1 heading for other sources.
- Ingest creates the source page by default. Create or update knowledge pages only when the user explicitly names them.
- Treat lint-clean completion as the end of the page post-processing path.
- Use wikilinks for existing pages and user-approved new pages.
- Keep relation semantics exact. Use `relation_derived_from` for source-backed origin, `relation_extends` for knowledge-line continuation, and `relation_uses` for definitions, theorems, methods, or tools the page depends on. Mirror that choice in the matching `## Relations` bullet.
