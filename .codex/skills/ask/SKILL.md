---
name: ask
description: Use when the user asks questions against the Vicky wiki and wants a cited answer or an explicitly requested saved output.
---

# Ask

Answer questions from the maintained wiki with citations.

## Inputs

- `question`
- optional explicit save-back request

## Outputs

- a concise cited answer
- `wiki/outputs/{slug}.md` when the user requests saving

## References

- `AGENTS.md` for page homes, relation fields, and tool boundaries
- `templates/Wiki_Output.md`
- `.codex/skills/ask/scripts/retrieve.py`

## Workflow

1. Generate 3-5 English candidate terms from the user's question. Include the original term, likely slug, common aliases, and abbreviations.
2. Run `./.venv/bin/python .codex/skills/ask/scripts/retrieve.py wiki "<term-1>" "<term-2>" ...`.
3. `retrieve.py` scans `wiki/**/*.md` and only uses each page's `slug` and `aliases` to rank seeds.
4. `retrieve.py` scores the candidate terms and returns at most 5 seed candidates. Slug matches rank above alias matches.
5. `retrieve.py` reverse-scans frontmatter `relation_*` for one-hop neighbors. The seed page's own `relation_*` are outgoing edges. Other pages whose `relation_*` point to the seed are incoming edges.
6. `retrieve.py` reads `## Relations` from each seed-side relation page and returns a candidate package with:
   - top seeds
   - each seed's incoming neighbors and outgoing neighbors
   - each edge's `relation_field`
   - the matching `## Relations` sentence
   - each file's `path` and `page_type`
7. Use the candidate package to choose the full reads:
   - randomly pick 3 seeds from the returned top seeds
   - for each seed, pick at most 3 one-hop neighbors
   - order neighbors by `relation_derived_from`, `relation_uses`, `relation_extends`, `relation_compares_with`, `relation_contradicts`
8. Read the full Markdown of the selected seeds and neighbors.
9. Answer with a concise synthesis and explicit `[[slug]]` citations.
10. If `retrieve.py` returns no seeds, run `obsidian search:context query="<candidate-term>" path=wiki` for the step-1 terms, answer from those results, and explicitly tell the user that no seed page exists yet.
11. For explicit save requests, create `wiki/outputs/{slug}.md` from `Wiki_Output` and write the answer.

## Constraints

- Ground every important claim in wiki pages.
- Use `retrieve.py` as the primary retrieval path.
- Read full Markdown only after seed and neighbor selection.
- Keep default graph expansion to one hop.
