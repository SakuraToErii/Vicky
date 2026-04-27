# Vicky

An Obsidian-first LLM wiki for reading papers, blogs, and technical notes with a persistent Markdown knowledge base.

Vicky turns source material in `raw/` into structured notes in `wiki/`. Obsidian is the browsing and editing surface. Codex skills and local tools maintain the schema, semantic relations, logs, indexes, and checks.

## Repository Layout

```text
raw/
├── papers/        # paper sources prepared as tex/md
├── web/           # web clips, exported markdown, or html
└── inbox/         # temporary snippets and prompts

wiki/
├── sources/       # one page per source
├── concepts/      # reusable technical concepts
├── theorems/      # definitions, lemmas, propositions, theorems, examples
├── foundations/   # stable background knowledge
├── people/        # researcher and author pages
├── ideas/         # open questions and developing thoughts
├── topics/        # higher-level maps over sources and concepts
├── outputs/       # saved answers, comparisons, and syntheses
├── bases/         # Obsidian Bases workbenches
└── log.md         # append-only activity log

templates/
├── Wiki_Source.md
├── Wiki_Concept.md
├── Wiki_Theorem.md
├── Wiki_Foundation.md
├── Wiki_Person.md
├── Wiki_Idea.md
├── Wiki_Topic.md
└── Wiki_Output.md
```

Engineering support directories stay hidden at the vault root: `.docs/`, `.tools/`, `.tests/`, `.config/`, `.codex/`, `.obsidian/`, and `.github/`.

## Workflow

1. Add source files to `raw/papers/`, `raw/web/`, or `raw/inbox/`.
2. Ask the agent to ingest the source into `wiki/sources/`.
3. Create or update related concepts, theorems, foundations, people, ideas, topics, and outputs.
4. Review semantic edges in `wiki/bases/Semantic Relations.base`.
5. Ask questions against the maintained wiki through the repo-local `ask` skill.
6. Run lint when the vault structure changes.

## Semantic Graph

Semantic edges live in Markdown properties:

```yaml
relation_derived_from:
  - "[[source-paper-a]]"
relation_extends:
  - "[[concept-b]]"
```

The six relation fields are a frozen schema:

- `relation_derived_from`
- `relation_extends`
- `relation_supports`
- `relation_contradicts`
- `relation_uses`
- `relation_compares_with`

Add a new relation field only after proving the existing six fields cannot express the relation.

`wiki/bases/Semantic Relations.base` is the main semantic relation workbench. Use it to scan pages, filter missing relations, group by page type, and review relation fields.

`wiki/bases/Current Page Neighbors.base` is a local context panel. Embed it in a note with:

```markdown
![[Current Page Neighbors.base#Semantic neighbors]]
```

`ask` retrieval starts from Obsidian CLI search, then expands candidates through relation properties, links, backlinks, properties, and outlines. Bases remain the human-facing relation workbench.

## Setup

Requirements:

- Python 3.9+
- Codex CLI

Bootstrap:

```bash
chmod +x setup.sh
./setup.sh
```

The script creates `.venv`, installs dependencies, writes `.env` from `.config/.env.example`, and writes `.codex/settings.local.json` from the template.

`SEMANTIC_SCHOLAR_API_KEY` is optional and useful for source metadata enrichment.

## Checks

Run the strict vault lint:

```bash
.venv/bin/python .tools/lint.py --wiki-dir wiki --json
```

Run the test suite:

```bash
.venv/bin/python -m pytest
```

Useful Obsidian CLI diagnostics:

```bash
obsidian unresolved
obsidian orphans
obsidian deadends
obsidian properties
obsidian files
```

## Obsidian Notes

- Open the repository root as the Obsidian vault.
- Obsidian Templates use `templates/`, configured in `.obsidian/templates.json`.
- Obsidian Bases use `wiki/bases/`.
- New wiki pages can be created with `obsidian create path="wiki/concepts/<slug>.md" template="Wiki_Concept"`.
- Existing notes can usually be addressed by file name, such as `obsidian read file=<slug>` or `obsidian property:read file=<slug> name=title`.
- The vault is plain Markdown, so git history stays readable.
