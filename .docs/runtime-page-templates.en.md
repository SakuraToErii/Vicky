# Runtime Page Templates

Canonical page templates live in the Obsidian template folder:

- `templates/Wiki_Source.md`
- `templates/Wiki_Concept.md`
- `templates/Wiki_Theorem.md`
- `templates/Wiki_Foundation.md`
- `templates/Wiki_Person.md`
- `templates/Wiki_Idea.md`
- `templates/Wiki_Topic.md`
- `templates/Wiki_Output.md`

Obsidian CLI examples:

```bash
obsidian templates
obsidian create path="wiki/concepts/<slug>.md" template="Wiki_Concept"
obsidian template:read name="Wiki_Concept"
```

Use `.docs/obsidian-cli-workflows.en.md` for read, property, search, link, rename, move, and log commands.

Use this page as a compact index:

- `sources/{slug}.md`: summary, key points, evidence, formal objects, relations, notes
- `concepts/{slug}.md`: definition, intuition, variants, connections, open questions
- `theorems/{slug}.md`: statement, conditions, proof sketch, consequences, examples
- `foundations/{slug}.md`: definition, motivation, standard form, related notes
- `people/{slug}.md`: overview, key works, related pages
- `ideas/{slug}.md`: prompt, motivation, supporting sources, open questions, next step
- `topics/{slug}.md`: overview, core concepts, sources, theorems, people, open questions
- `outputs/{slug}.md`: question, answer, relations, sources used, follow-up

Follow `.docs/semantic-relations.en.md` for the canonical relation field list and frozen schema rule.

Each relation value should be an Obsidian wikilink string. Mirror every stable relation in a `## Relations` bullet with a short explanation. Use relation fields on generated wiki pages that keep a `## Relations` section, including saved outputs.

Open `wiki/bases/Semantic Relations.base` after writing relation properties. Use the `Relation review` view to find pages that need semantic edges and the grouped table views to inspect cross-page connections.

Use `.docs/semantic-relations.en.md` for the local neighborhood embed pattern.

Use `.docs/runtime-support-files.en.md` for the short explanation of `wiki/log.md` and `wiki/bases/*.base`.
