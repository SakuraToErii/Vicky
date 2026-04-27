# Runtime Directory Structure

```text
wiki/
├── sources/        ← source pages generated from raw inputs
├── concepts/       ← cross-source concept pages
├── theorems/       ← formal notes: definitions, theorems, examples
├── foundations/    ← stable background notes
├── people/         ← authors and researchers
├── ideas/          ← developing questions and interpretations
├── topics/         ← map pages over a domain
├── outputs/        ← saved query results and syntheses
├── bases/          ← Obsidian Bases relation workbenches
└── log.md          ← append-only timeline

raw/
├── papers/         ← user-owned paper sources, already prepared as tex/md
├── web/            ← user-owned article/web exports
└── inbox/          ← temporary snippets and scratch inputs

templates/
├── Wiki_Source.md  ← Obsidian template for wiki/sources
├── Wiki_Concept.md
├── Wiki_Theorem.md
├── Wiki_Foundation.md
├── Wiki_Person.md
├── Wiki_Idea.md
├── Wiki_Topic.md
└── Wiki_Output.md
```

Hidden engineering directories live at the repository root: `.docs/`, `.tools/`, `.tests/`, and `.config/`.

## Reminders

- `raw/` is the source layer.
- `wiki/` is the maintained layer.
- `templates/` is the Obsidian template layer used by `obsidian create`.
- `wiki/bases/` is the Obsidian Bases layer used for relation browsing, filtering, and review.
- Obsidian CLI is the default interface for vault reads, creation, properties, search, links, and logs.
- `sources/` is the canonical home for per-source summaries.
- `outputs/` is the place for saved answers and comparison pages.
- `Semantic Relations.base` is the main relation table across the wiki.
- `Current Page Neighbors.base` is the embeddable local neighborhood view.
