# Vicky

An Obsidian-first LLM wiki for reading papers, blogs, and technical notes with a persistent Markdown knowledge base.

Vicky turns source material in `raw/` into structured notes in `wiki/`. Obsidian is the browsing and editing surface. Codex skills and local tools maintain the schema, semantic relations, logs, support files, and checks.

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

Codex skills follow the standard package shape: each skill has `SKILL.md`, optional `agents/openai.yaml`, and executable helpers under `scripts/`. Shared repo-local helpers live in `.codex/lib/vicky/`.

## Workflow

1. Add source files to `raw/papers/`, `raw/web/`, or `raw/inbox/`.
2. Ask the agent to ingest the source into `wiki/sources/`.
3. Create or update user-approved concepts, theorems, foundations, people, ideas, topics, and outputs.
4. Review semantic edges in `wiki/bases/Semantic Relations.base`.
5. Ask questions against the maintained wiki through the repo-local `ask` skill.
6. Run lint when the vault structure changes.

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

The script checks required CLIs, creates `.venv`, installs dependencies, verifies Python packages, writes `.env` from `.config/.env.example`, and writes `.codex/settings.local.json` from the template.

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
.venv/bin/python .codex/skills/ask/scripts/frontmatter_find.py wiki concepts --maturity working
.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki concept "Gradient Descent"
```

## Legacy CLI Mapping

The old `.tools/research_wiki.py` surface is now split by skill: slug and near-duplicate checks live in `ingest/scripts/`, frontmatter lookup lives in `ask/scripts/`, reset lives in `reset/scripts/`, and graph diagnostics use Obsidian CLI plus Vicky path filters. Log appends, property reads, property writes, file listing, search, links, backlinks, outlines, renames, and moves use Obsidian CLI.

## Obsidian Notes

- Open the repository root as the Obsidian vault.
- Obsidian Templates use `templates/`, configured in `.obsidian/templates.json`.
- Obsidian Bases use `wiki/bases/`.
- New wiki pages can be created with `obsidian create path="wiki/concepts/<slug>.md" template="Wiki_Concept"`.
- Existing notes can usually be addressed by file name, such as `obsidian read file=<slug>` or `obsidian property:read file=<slug> name=title`.
- The vault is plain Markdown, so git history stays readable.
