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
7. Create a missing source page with `obsidian create path="wiki/sources/{slug}.md" template="Wiki_Source"`.
8. Fill source frontmatter with `obsidian property:set file=<slug> name=<field> value=<value> type=<type>`. Keep `source_path` pointing at the raw file.
9. Detect user intent for non-source knowledge pages:
   - If the user names target concepts, theorems, people, ideas, topics, or foundations, create or update only those pages.
   - If the user gives a reading question or interpretation, create or update only the pages needed to support that stated direction.
   - If the user only asks to ingest the source, produce candidate page proposals and wait for the next user message before creating or updating non-source pages.
10. Format candidate page proposals with `target path`, `template`, `why create`, `source evidence`, and `priority`.
11. Before proposing or creating a concept or theorem page, run `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki concept "<title>"` or `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki theorem "<title>"`.
12. Use `./.venv/bin/python .codex/skills/ingest/scripts/fetch_s2.py` when you need metadata support from Semantic Scholar.
13. Maintain semantic relation properties with `obsidian property:set file=<slug> name=<relation_field> value="[[target-slug]]"` for single relation targets. For multi-target relation fields, update the frontmatter list and verify with `obsidian property:read`.
14. Mirror every stable relation property in `## Relations` with a short evidence sentence.
15. Use `wiki/bases/Semantic Relations.base#Relation review` as the review surface for pages with empty relation fields.
16. Verify discoverability with `obsidian search query="<new concept or source title>" path=wiki` and `obsidian search:context query="<new concept or source title>" path=wiki`.
17. Append one log line with `obsidian append file=log content="## [YYYY-MM-DD] ingest | ..."`. Include `proposed: <paths>` when the ingest stops at proposals.

## Constraints

- `raw/` is read-only.
- `wiki/sources/` is the canonical home for per-source summaries.
- `wiki/sources/` is the automatic citation anchor for raw files.
- Create or update non-source knowledge pages only when the user has named the target or approved the proposal.
- Maintain backlinks from approved concepts, theorems, and people through `key_sources`.
- Use `relation_*` properties for machine-searchable semantic edges and `## Relations` for human-readable evidence.
- Treat the six listed `relation_*` fields as the frozen relation contract.
- Use Bases for relation browsing, filtering, and manual review.
- Use `obsidian create path=... template=...` for new wiki pages when the template exists.
- Use `obsidian property:set` for scalar properties and single relation targets.
- Use wikilinks only for existing pages or user-approved new pages.
