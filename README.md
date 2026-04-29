# Vicky

A lightweight, Obsidian-native LLM wiki for reading papers, blogs, and technical notes.

Vicky turns source material in `raw/` into long-lived Markdown notes in `wiki/`. It is built for two readers: you, writing and studying in Obsidian; and Codex, maintaining schema, semantic relations, logs, support files, and checks through local skills.

Vicky follows Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern: raw sources feed a maintained Markdown wiki, the schema lives in `AGENTS.md`, and the core loop is ingest, ask, and check. Vicky adapts that pattern for an Obsidian-first personal research workflow with Bases, Obsidian CLI, and lightweight repo-local scripts.

The name `Vicky` nods to `wiki` and gives the project a warm, memorable identity.

## What Vicky Optimizes For

- Lightweight vault shape: plain Markdown, Obsidian properties, Bases, Codex skills, and a small set of Python helpers.
- Human-first knowledge work: notes stay readable, editable, and useful for daily study inside Obsidian.
- AI-assisted maintenance: Codex handles repeatable structure, semantic relation checks, duplicate checks, and lint.
- Obsidian-native operations: reads, writes, property edits, search, links, backlinks, outlines, and graph diagnostics use Obsidian CLI wherever possible.
- Durable semantic graph: six frozen `relation_*` fields keep relationships searchable while `## Relations` keeps evidence readable.

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

Engineering support stays under `.codex/`, `.tests/`, `.config/`, `.obsidian/`, and `.github/`.

Codex skills follow the standard package shape: each skill has `SKILL.md`, optional `agents/openai.yaml`, and executable helpers under `scripts/`. Shared repo-local helpers live in `.codex/lib/`.

## Workflow

1. Add source files to `raw/papers/`, `raw/web/`, or `raw/inbox/`.
2. Ask the agent to ingest the source into `wiki/sources/`.
3. Create or update user-approved concepts, theorems, foundations, people, ideas, topics, and outputs.
4. Review semantic edges in `wiki/bases/Semantic Relations.base`.
5. Ask questions against the maintained wiki through the repo-local `ask` skill.
6. Run lint when the vault structure changes.

New concept, theorem, and idea pages follow a fixed post-processing path: run duplicate checks before writing, finish one page at a time, fill source ancestry through `relation_derived_from`, add the reverse source or related-page mention, append `wiki/log.md`, then finish with a clean lint run. People pages keep source ancestry in `key_sources`.

## Semantic Graph

Semantic edges live in Markdown properties and stay aligned with `## Relations` evidence blocks. The six frozen fields are `relation_derived_from`, `relation_extends`, `relation_supports`, `relation_contradicts`, `relation_uses`, and `relation_compares_with`.

## Setup

Requirements:

- Python 3.9+
- Codex CLI
- Obsidian CLI (`obsidian`) and ripgrep (`rg`) for vault diagnostics and filtered graph checks

`setup.sh` checks these CLIs before creating or reusing `.venv`, then verifies the required Python packages inside the environment.

Bootstrap:

```bash
chmod +x setup.sh
./setup.sh
```

The script checks required CLIs, creates `.venv`, installs runtime and test dependencies, verifies Python packages, writes `.env` from `.config/.env.example`, and writes `.codex/settings.local.json` from the template.

`SEMANTIC_SCHOLAR_API_KEY` is optional and useful for source metadata enrichment.

## Checks

Run the strict vault lint:

```bash
.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json
```

Run the test suite:

```bash
.venv/bin/python -m pytest
```

Useful Obsidian CLI diagnostics:

```bash
obsidian unresolved
obsidian properties
obsidian files
```

Repo-local graph diagnostics:

```bash
obsidian orphans | rg '^wiki/(sources|concepts|theorems|foundations|people|ideas|topics|outputs)/' | rg -v '^wiki/outputs/' || true
obsidian deadends | rg '^wiki/(sources|concepts|theorems|foundations|people|ideas|topics|outputs)/' | rg -v '^wiki/outputs/' || true
```

Other useful skill scripts:

```bash
.venv/bin/python .codex/skills/ingest/scripts/slug.py "Flash Attention"
.venv/bin/python .codex/skills/ask/scripts/frontmatter_find.py wiki ideas --priority '<3'
.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki concept "Gradient Descent"
.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki idea "Open Question"
```

## Command Surface

- Obsidian CLI handles note reads, writes, property edits, search, links, backlinks, outlines, log appends, renames, and moves.
- `ingest/scripts/` handles slugging, duplicate checks, and Semantic Scholar metadata.
- `ask/scripts/` handles frontmatter lookup.
- `check/scripts/` handles strict wiki lint.
- `reset/scripts/` handles reset planning and reset execution.

## Obsidian Notes

- Open the repository root as the Obsidian vault.
- Obsidian Templates use `templates/`, configured in `.obsidian/templates.json`.
- Obsidian Bases use `wiki/bases/`.
- `wiki/bases/Semantic Relations.base` is the main semantic review table.
- `wiki/bases/Current Page Neighbors.base` can be embedded inside notes for local graph context.
- Embed the local graph panel with `![[Current Page Neighbors.base#Semantic neighbors]]`.
- New wiki pages can be created with `obsidian create path="wiki/concepts/<slug>.md" template="Wiki_Concept"`.
- Existing notes can usually be addressed by file name, such as `obsidian read file=<slug>` or `obsidian property:read file=<slug> name=title`.
- The vault is plain Markdown, so git history stays readable.
