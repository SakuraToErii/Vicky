# Wiki Bootstrap Template Catalog

The canonical page templates live in the Obsidian template folder:

| Wiki path | Obsidian template |
|---|---|
| `wiki/sources/{slug}.md` | `Wiki_Source` |
| `wiki/concepts/{slug}.md` | `Wiki_Concept` |
| `wiki/theorems/{slug}.md` | `Wiki_Theorem` |
| `wiki/foundations/{slug}.md` | `Wiki_Foundation` |
| `wiki/people/{slug}.md` | `Wiki_Person` |
| `wiki/ideas/{slug}.md` | `Wiki_Idea` |
| `wiki/topics/{slug}.md` | `Wiki_Topic` |
| `wiki/outputs/{slug}.md` | `Wiki_Output` |

Default Bases live in `wiki/bases/`:

| Base file | Use |
|---|---|
| `wiki/bases/Semantic Relations.base` | whole-vault semantic graph table and relation review queue |
| `wiki/bases/Current Page Neighbors.base` | embeddable current-page neighborhood table |

## Obsidian CLI

List available templates:

```bash
obsidian templates
```

Read a template:

```bash
obsidian template:read name="Wiki_Concept"
```

Create a page from a template:

```bash
obsidian create path="wiki/concepts/<slug>.md" template="Wiki_Concept"
```

Use `overwrite` only when the user explicitly asks to replace an existing page.

## Support files

`wiki/log.md` and `wiki/bases/*.base` are support files. Create missing files with Obsidian CLI or `.tools/research_wiki.py init`:

```bash
obsidian create path="wiki/log.md" content="# Vicky Log\n\n"
```

Restore default Base files from `.tools/_schemas.py` with:

```bash
./.venv/bin/python .tools/research_wiki.py init wiki
```

Use Obsidian CLI search for page discovery after page creation:

```bash
obsidian files folder=wiki ext=md
obsidian search query="<term>" path=wiki
obsidian search:context query="<term>" path=wiki
```

Append log entries with:

```bash
obsidian append file=log content="## [YYYY-MM-DD] init | wiki initialized"
```
