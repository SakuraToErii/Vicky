# Obsidian CLI Workflows

Run commands from the vault root. Existing notes should use `file=<slug>` so Obsidian resolves them like wikilinks. Exact destinations should use `path=wiki/<type>/<slug>.md`.

## Default Commands

| Task | Command |
|---|---|
| Read a note | `obsidian read file=<slug>` |
| Read a property | `obsidian property:read file=<slug> name=<field>` |
| Set a scalar property | `obsidian property:set file=<slug> name=<field> value=<value> type=text` |
| Set a plain list property | `obsidian property:set file=<slug> name=tags value="paper,attention" type=list` |
| Create a page | `obsidian create path="wiki/concepts/<slug>.md" template="Wiki_Concept"` |
| Append to a note | `obsidian append file=<slug> content="<markdown>"` |
| Prepend to a note | `obsidian prepend file=<slug> content="<markdown>"` |
| Rename a note | `obsidian rename file=<slug> name=<new-slug>` |
| Move a note | `obsidian move file=<slug> to="wiki/concepts/<slug>.md"` |
| Search text | `obsidian search query="<term>" path=wiki` |
| Search with context | `obsidian search:context query="<term>" path=wiki` |
| Outgoing links | `obsidian links file=<slug>` |
| Backlinks | `obsidian backlinks file=<slug>` |
| Outline | `obsidian outline file=<slug> format=json` |
| Unresolved links | `obsidian unresolved verbose format=json` |
| List wiki files | `obsidian files folder=wiki ext=md` |
| Wiki orphans | `./.venv/bin/python .tools/research_wiki.py query wiki orphans` |
| Wiki dead ends | `./.venv/bin/python .tools/research_wiki.py query wiki deadends` |

## Bases Workflows

Obsidian Bases live in `wiki/bases/`:

| Task | Target |
|---|---|
| Review the whole semantic graph | `wiki/bases/Semantic Relations.base#Semantic graph` |
| Find pages that need relation fields | `wiki/bases/Semantic Relations.base#Relation review` |
| Review source metadata | `wiki/bases/Semantic Relations.base#Sources` |
| Embed neighbors in a note | `![[Current Page Neighbors.base#Semantic neighbors]]` |

Bases read the same Markdown properties that Obsidian CLI writes with `obsidian property:set`. Use the CLI for reliable property writes and use Bases for browsing, filtering, sorting, and manual edits in Obsidian.

Use `.docs/semantic-relations.en.md` for the canonical relation field list, value format, and frozen schema rule.

`obsidian orphans` and `obsidian deadends` read the whole vault. Use the repo-local Python queries for `wiki/` health checks.

## Property Notes

`property:set type=list` stores comma-separated plain values as a YAML list:

```bash
obsidian property:set file=<slug> name=tags value="paper,attention" type=list
```

For a single wikilink relation, use:

```bash
obsidian property:set file=<slug> name=relation_derived_from value="[[source-slug]]"
```

For multi-target relation fields, preserve a wikilink list in frontmatter and verify with:

```bash
obsidian property:read file=<slug> name=relation_derived_from
```

## Python Boundary

Keep Python for:

- strict lint rules: `./.venv/bin/python .tools/lint.py --wiki-dir wiki --json`
- Semantic Scholar metadata: `./.venv/bin/python .tools/fetch_s2.py ...`
- setup, tests, and high-risk reset dry-runs

Use Obsidian CLI for normal vault reads, note creation, property edits, search, link checks, log appends, renames, and moves.
