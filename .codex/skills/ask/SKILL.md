---
name: ask
description: Use when the user asks questions against the Vicky wiki and may want the answer cited and optionally saved into `wiki/outputs/`.
---

# Ask

Query the maintained wiki.

## Inputs

- `question`
- optional save-back intent from the user

## Outputs

- a cited answer
- optional `wiki/outputs/{slug}.md`
- optional `wiki/log.md` update

## References

- `templates/Wiki_Output.md`
- `wiki/bases/Semantic Relations.base` for the maintained relation workbench

## Relation Fields

- `relation_derived_from`
- `relation_extends`
- `relation_supports`
- `relation_contradicts`
- `relation_uses`
- `relation_compares_with`

## Workflow

1. Expand the question into 3-8 search terms: original wording, likely slugs, synonyms, abbreviations, and related formal names.
2. Read the relation workbench syntax at `wiki/bases/Semantic Relations.base` to confirm the active relation fields and review views.
3. Run lexical search with Obsidian CLI:
   - `obsidian search query="<term>" path=wiki`
   - `obsidian search:context query="<term>" path=wiki`
4. Extract candidate slugs and page paths from search results. Prefer pages whose title, slug, headings, or context snippets match the question.
5. Run property relation search for strong candidate slugs:
   - Query both raw slug values and wikilink-string values, e.g. `[relation_derived_from:<slug>]` and `[relation_derived_from:[[<slug>]]]`.
   - Repeat this for `relation_derived_from`, `relation_extends`, `relation_supports`, `relation_contradicts`, `relation_uses`, and `relation_compares_with`.
6. For each strong candidate, expand one hop with `obsidian links file=<slug>` and `obsidian backlinks file=<slug>`.
7. Read properties for top candidates with `obsidian property:read file=<slug> name=<field>` where useful. Include title/name, tags, status/maturity, key_sources, source_path, and relation fields.
8. Read outlines for long candidates with `obsidian outline file=<slug> format=json`.
9. Use `obsidian files folder=wiki ext=md` as the broad-query fallback when search returns too few candidates or the user asks for a whole-vault map.
10. Rerank candidates using this priority: title/slug match, `search:context` match, relation-property match, one-hop link neighbor, page type, source recency or maturity fields when available.
11. Read the selected 5-12 pages with `obsidian read file=<slug>`. Use `path=wiki/<type>/<slug>.md` when a slug is ambiguous.
12. Answer with explicit `[[slug]]` citations.
13. When the answer is worth preserving, create `wiki/outputs/{slug}.md` with `obsidian create path="wiki/outputs/{slug}.md" template="Wiki_Output"` and fill the answer.
14. Append a log line with `obsidian append file=log content="## [YYYY-MM-DD] ask | <question-slug> | saved: outputs/<slug>"`.

## Constraints

- Ground every important claim in wiki pages.
- Preserve useful analyses by saving them into `wiki/outputs/`.
- Prefer Obsidian CLI for retrieval and page reads.
- Treat Bases as relation map metadata for retrieval planning.
- Treat the six listed `relation_*` fields as the frozen relation contract.
- Use `file=<slug>` for existing notes and `path=` for ambiguous slugs or exact destinations.
- Keep link expansion to one hop unless the user explicitly asks for a broader map.
