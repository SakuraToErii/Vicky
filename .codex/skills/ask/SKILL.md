---
name: ask
description: Use when the user asks questions against the Vicky wiki and wants a cited answer or an explicitly requested saved output.
---

# Ask

Query the maintained wiki.

## Inputs

- `question`
- optional explicit save-back request

## Outputs

- a cited answer
- `wiki/outputs/{slug}.md` and `wiki/log.md` entry when the user requests saving

## References

- `AGENTS.md` for page homes, relation fields, and tool boundaries
- `templates/Wiki_Output.md`
- `wiki/bases/Semantic Relations.base` for the maintained relation workbench

## Workflow

1. Expand the question into search terms: original wording, likely slugs, synonyms, abbreviations, and related formal names.
2. Search with `obsidian search query="<term>" path=wiki` and `obsidian search:context query="<term>" path=wiki`; use `obsidian files folder=wiki ext=md` for whole-vault maps.
3. For strong candidate slugs, search relation properties with raw slug values and wikilink strings. Use `./.venv/bin/python .codex/skills/ask/scripts/frontmatter_find.py wiki <page-type> --<field> <value>` for deterministic frontmatter filters.
4. Expand strong candidates one hop with `obsidian links file=<slug>` and `obsidian backlinks file=<slug>`. Read useful properties and outlines before selecting pages.
5. Rerank by title/slug match, context match, relation-property match, one-hop neighbor, page type, source recency, and fields such as `priority` or `theorem_kind`.
6. Read the selected 5-12 pages with `obsidian read file=<slug>` or exact `path=wiki/<type>/<slug>.md`, then answer with explicit `[[slug]]` citations.
7. For explicit save requests, create `wiki/outputs/{slug}.md` from `Wiki_Output`, write the answer, and append `wiki/log.md`.

## Constraints

- Ground every important claim in wiki pages.
- Save analyses into `wiki/outputs/` from explicit save requests.
- Prefer Obsidian CLI for retrieval and page reads.
- Treat Bases as relation map metadata for retrieval planning.
- Use `file=<slug>` for existing notes and `path=` for ambiguous slugs or exact destinations.
- Keep normal link expansion to one hop; broaden it for explicit whole-vault maps.
