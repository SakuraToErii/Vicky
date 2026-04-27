# Wiki Update Template Catalog

Use Obsidian templates when ingesting one prepared source into the Vicky wiki. The source page is the automatic anchor. Non-source knowledge pages are created or updated after explicit user intent or approval.

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

Default relation review surfaces:

| Base file | Use |
|---|---|
| `wiki/bases/Semantic Relations.base#Relation review` | find newly created pages with empty relation fields |
| `wiki/bases/Semantic Relations.base#Semantic graph` | review all semantic edges grouped by page type |
| `wiki/bases/Current Page Neighbors.base#Semantic neighbors` | embed a local relation neighborhood in a note |

## Commands

List templates:

```bash
obsidian templates
```

Create a source page:

```bash
obsidian create path="wiki/sources/<slug>.md" template="Wiki_Source"
```

Create a user-approved related page:

```bash
obsidian create path="wiki/concepts/<slug>.md" template="Wiki_Concept"
```

Read a template before making a structural edit:

```bash
obsidian template:read name="Wiki_Concept"
```

Read and update properties:

```bash
obsidian read file=<slug>
obsidian property:read file=<slug> name=source_path
obsidian property:set file=<slug> name=source_path value="raw/papers/<file>.md" type=text
obsidian property:set file=<slug> name=tags value="paper,attention" type=list
obsidian property:set file=<slug> name=relation_derived_from value="[[source-paper-a]]"
```

For list values without wikilinks, pass comma-separated values with `type=list`. For multi-target relation fields, preserve wikilink list frontmatter and verify with `obsidian property:read`.

## User-intent gate

Create `wiki/sources/{slug}.md` during ingest. It is the structured citation node for the raw file.

For `concepts`, `theorems`, `people`, `ideas`, `topics`, and `foundations`, use this gate:

1. User names a target page or concept: create or update that page.
2. User gives a reading question or interpretation: create or update the smallest set of pages that supports that direction.
3. User only asks to ingest a source: create the source page, then propose candidate pages and wait for the next user message.

Candidate proposal format:

```markdown
- target path: `wiki/concepts/<slug>.md`
  template: `Wiki_Concept`
  why create: <one sentence tied to the user's reading goal>
  source evidence: <short pointer to the source section>
  priority: high | medium | low
```

Use wikilinks only for existing pages or user-approved new pages.

## Relation schema

Relation properties are machine-searchable semantic edges. Use Obsidian wikilink strings as values:

```yaml
relation_derived_from:
  - "[[source-paper-a]]"
relation_extends:
  - "[[concept-b]]"
relation_supports:
  - "[[theorem-c]]"
relation_contradicts: []
relation_uses: []
relation_compares_with: []
```

Mirror every stable relation property in the page body:

```markdown
## Relations

- Derived from [[source-paper-a]]: uses its proof setup and relaxes the boundedness assumption.
- Extends [[concept-b]]: generalizes the finite case to the stochastic setting.
```

Use relation properties as the graph index and `## Relations` as the evidence context.

The six `relation_*` fields are a frozen schema. Add a new relation field only after proving the existing six fields cannot express the relation.

After writing relation properties, use `wiki/bases/Semantic Relations.base` as the review table. The `Relation review` view surfaces pages whose semantic relation fields are empty, and the grouped views make cross-page edges easier to inspect before running strict lint.

## Search and log

Use Obsidian CLI search to verify discoverability after ingest:

```bash
obsidian files folder=wiki ext=md
obsidian search query="<new concept or source title>" path=wiki
obsidian search:context query="<new concept or source title>" path=wiki
```

Append one parseable log entry:

```markdown
## [YYYY-MM-DD] ingest | added sources/<slug> | updated: concepts/<slug>, theorems/<slug>, people/<slug>, ideas/<slug>, topics/<slug>
## [YYYY-MM-DD] ingest | updated sources/<slug> | updated: concepts/<slug>, topics/<slug>
## [YYYY-MM-DD] ingest | added sources/<slug> | proposed: concepts/<slug>, theorems/<slug>
```

Append the entry with:

```bash
obsidian append file=log content="## [YYYY-MM-DD] ingest | added sources/<slug> | proposed: concepts/<slug>"
```
