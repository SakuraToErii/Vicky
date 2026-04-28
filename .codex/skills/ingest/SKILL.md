---
name: ingest
description: Use when the user wants to ingest one prepared source into the Vicky wiki, create the source page, and propose or perform user-approved knowledge-page updates.
---

# Ingest

Turn one prepared source into a source page plus user-approved knowledge-page updates.

## Inputs

- `source`: a local `.tex`, `.md`, `.txt`, `.html`, or `.htm` path, usually under `raw/papers/` or `raw/web/`

## Outputs

- `wiki/sources/{slug}.md`
- candidate page proposals when the user has not named target knowledge pages
- user-approved updates to `wiki/concepts/*.md`
- user-approved updates to `wiki/theorems/*.md`
- user-approved updates to `wiki/people/*.md`
- user-approved updates to `wiki/ideas/*.md`
- user-approved updates to `wiki/topics/*.md`
- user-approved updates to `wiki/foundations/*.md`
- relation review through `wiki/bases/Semantic Relations.base`
- updated `wiki/log.md`
- one-page-at-a-time post-processing with lint-clean completion

## References

- `templates/`

## Template Map

| Wiki path | Obsidian template | Use |
|---|---|---|
| `wiki/sources/{slug}.md` | `Wiki_Source` | per-source summary |
| `wiki/concepts/{slug}.md` | `Wiki_Concept` | reusable concepts |
| `wiki/theorems/{slug}.md` | `Wiki_Theorem` | definitions, lemmas, propositions, theorems, examples, algorithms, formal notes |
| `wiki/people/{slug}.md` | `Wiki_Person` | meaningful author or researcher nodes |
| `wiki/ideas/{slug}.md` | `Wiki_Idea` | open directions or synthesis ideas |
| `wiki/topics/{slug}.md` | `Wiki_Topic` | domain maps and source clusters |
| `wiki/foundations/{slug}.md` | `Wiki_Foundation` | stable background knowledge |
| `wiki/outputs/{slug}.md` | `Wiki_Output` | saved answers and syntheses |

## Target Path Rules

- source page: `wiki/sources/{slug}.md`
- concept page: `wiki/concepts/{slug}.md`
- theorem page: `wiki/theorems/{slug}.md`
- person page: `wiki/people/{slug}.md`
- idea page: `wiki/ideas/{slug}.md`
- topic page: `wiki/topics/{slug}.md`
- foundation page: `wiki/foundations/{slug}.md`
- output page: `wiki/outputs/{slug}.md`

## Relation Fields

- `relation_derived_from`
- `relation_extends`
- `relation_supports`
- `relation_contradicts`
- `relation_uses`
- `relation_compares_with`

## Workflow

1. Resolve the local path exactly as given by the user.
2. Run `obsidian templates` and confirm the `Wiki_*` templates are available.
3. Read the source with `obsidian read path="<source-path>"` and extract title, source type, authors, year, and main ideas. Use a local text read for raw formats that Obsidian cannot read cleanly.
4. Generate a lowercase hyphenated slug from the title with `./.venv/bin/python .codex/skills/ingest/scripts/slug.py "<title>"`.
5. Check slug occupancy with `obsidian files folder=wiki ext=md | rg '(^|/){slug}\\.md$' || true`.
6. If the slug already exists, read the existing page and ask the user whether this source should update that page or use a different slug.
7. Resolve the exact target path from the rules above and create the missing source page with `obsidian create path="wiki/sources/{slug}.md" template="Wiki_Source"`.
8. Fill source frontmatter with `obsidian property:set file=<slug> name=<field> value=<value> type=<type>`. Keep `source_path` pointing at the raw file.
9. After template creation, edit the exact target file directly for body content. Treat the template as the scaffold and the file edit as the main writing step.
10. Detect user intent for non-source knowledge pages:
   - If the user names target concepts, theorems, people, ideas, topics, or foundations, create or update only those pages.
   - If the user gives a reading question or interpretation, create or update only the pages needed to support that stated direction.
   - If the user only asks to ingest the source, produce candidate page proposals and wait for the next user message before creating or updating non-source pages.
11. Format candidate page proposals with `target path`, `template`, `why create`, `source evidence`, and `priority`.
12. Before proposing or creating a concept, theorem, or idea page, run `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki concept "<title>"`, `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki theorem "<title>"`, or `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki idea "<title>"`.
13. When the duplicate check returns a strong candidate, resolve the target page first. Continue through the update path or get user approval for a new page.
14. Process approved knowledge pages one at a time. Resolve the exact target path first, create the page from its template when needed, then edit that file directly and finish the full post-processing checklist before starting the next new page.
15. Use `./.venv/bin/python .codex/skills/ingest/scripts/fetch_s2.py` when you need metadata support from Semantic Scholar.
16. Maintain semantic relation properties with `obsidian property:set file=<slug> name=<relation_field> value="[[target-slug]]"` for single relation targets. For multi-target relation fields, update the frontmatter list and verify with `obsidian property:read`.
17. Mirror every stable relation property in `## Relations` with a short evidence sentence.
18. Complete the reverse update immediately after writing the page:
   - add or confirm `key_sources`
   - add the reverse source mention or related-page mention in body text or a related section
   - confirm the source or related page points back to the new page when that page type expects a reverse update
19. Verify the body edit with `git diff -- <exact-target-path>` instead of rereading the whole file when the page was created in this turn.
20. Use `wiki/bases/Semantic Relations.base#Relation review` as the review surface for pages with empty relation fields.
21. Verify discoverability with `obsidian search query="<new concept or source title>" path=wiki` and `obsidian search:context query="<new concept or source title>" path=wiki`.
22. Append one log line with `obsidian append file=log content="## [YYYY-MM-DD] ingest | ..."`. Include `proposed: <paths>` when the ingest stops at proposals.
23. Run `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json` as the completion signal after page creation or update.

## Constraints

- `raw/` is read-only.
- `wiki/sources/` is the canonical home for per-source summaries.
- `wiki/sources/` is the automatic citation anchor for raw files.
- Create or update non-source knowledge pages only when the user has named the target or approved the proposal.
- Maintain backlinks from approved concepts, theorems, and people through `key_sources`.
- Use `relation_*` properties for machine-searchable semantic edges and `## Relations` for human-readable evidence.
- Treat the six listed `relation_*` fields as the frozen relation contract.
- Use Bases for relation browsing, filtering, and manual review.
- Finish one new page completely before moving to the next new page in the same turn.
- Treat lint-clean completion as the end of the page post-processing path.
- Use `obsidian create path=... template=...` for new wiki pages when the template exists.
- Use `obsidian property:set` for scalar properties and single relation targets.
- After template creation, prefer direct edits to the exact target markdown file for body writing.
- For newly created pages in the current turn, prefer `git diff -- <exact-target-path>` over a full reread for post-edit verification.
- Use wikilinks only for existing pages or user-approved new pages.
