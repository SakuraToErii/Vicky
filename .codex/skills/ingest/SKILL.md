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

## References

- `references/wiki-update-templates.md`
- `templates/`
- `.docs/semantic-relations.en.md`

## Workflow

1. Resolve the local path exactly as given by the user.
2. Run `obsidian templates` and confirm the `Wiki_*` templates are available.
3. Read `references/wiki-update-templates.md` for the template-name map.
4. Read the source with `obsidian read path="<source-path>"` and extract title, source type, authors, year, and main ideas. Use a local text read for raw formats that Obsidian cannot read cleanly.
5. Generate a lowercase hyphenated slug from the title in the agent, following the vault slug convention.
6. Create a missing source page with `obsidian create path="wiki/sources/{slug}.md" template="Wiki_Source"`.
7. Fill source frontmatter with `obsidian property:set file=<slug> name=<field> value=<value> type=<type>`. Keep `source_path` pointing at the raw file.
8. Detect user intent for non-source knowledge pages:
   - If the user names target concepts, theorems, people, ideas, topics, or foundations, create or update only those pages.
   - If the user gives a reading question or interpretation, create or update only the pages needed to support that stated direction.
   - If the user only asks to ingest the source, produce candidate page proposals and wait for the next user message before creating or updating non-source pages.
9. Format candidate page proposals with `target path`, `template`, `why create`, `source evidence`, and `priority`.
10. Use `./.venv/bin/python .tools/fetch_s2.py` when you need metadata support from Semantic Scholar.
11. Maintain semantic relation properties with `obsidian property:set file=<slug> name=<relation_field> value="[[target-slug]]"` for single relation targets. For multi-target relation fields, update the frontmatter list and verify with `obsidian property:read`.
12. Maintain matching `## Relations` bullets for user-approved non-source pages. Use `obsidian read file=<slug>` before body edits and verify after the edit.
13. Use `wiki/bases/Semantic Relations.base#Relation review` as the review surface for pages with empty relation fields.
14. Append one log line with `obsidian append file=log content="## [YYYY-MM-DD] ingest | ..."`. Include `proposed: <paths>` when the ingest stops at proposals.

## Constraints

- `raw/` is read-only.
- `wiki/sources/` is the canonical home for per-source summaries.
- `wiki/sources/` is the automatic citation anchor for raw files.
- Create or update non-source knowledge pages only when the user has named the target or approved the proposal.
- Maintain backlinks from approved concepts, theorems, and people through `key_sources`.
- Use `relation_*` properties for machine-searchable semantic edges and `## Relations` for human-readable evidence.
- Follow `.docs/semantic-relations.en.md` for the frozen relation field contract.
- Use Bases for relation browsing, filtering, and manual review.
- Use `obsidian create path=... template=...` for new wiki pages when the template exists.
- Use `obsidian property:set` for scalar properties and single relation targets.
- Use wikilinks only for existing pages or user-approved new pages.
