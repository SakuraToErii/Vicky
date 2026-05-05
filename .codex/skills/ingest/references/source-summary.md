# Source Summary Guide

Use this guide when writing the main prose body for an academic paper source page.

## Default Mode

Write in academic style unless the user explicitly asks for another style. Use precise terminology, stable concepts from the paper, and Markdown prose that can live as a long-term wiki note.

Use `no-code` by default. Use `with-code` when the paper ships a code repository and the user explicitly wants implementation analysis. In `with-code` mode, inspect the repository, quote only the smallest useful snippets, and explain how the code realizes the paper's method.

## Page Shape

The page body uses specific content headings. The body opens with `## TL;DR` or `## 摘要` and then continues with content-shaped headings such as:

1. `## TL;DR` 
2. `## Motivation`
3. `## Background`
4. `## Core Contribution`
5. `## Formula Explanation`
6. `## Experiments`
7. `## Deeper Analysis`
8. `## Reflection`

Use these headings as the default structure for research papers. Merge adjacent sections when the source is short, while keeping the heading names specific to the content. Keep headings short, concrete, and semantic. A heading names what the section does.

## TL;DR

The source page frontmatter already carries metadata such as title, authors, venue, year, source kind, and source path. The body opens with a concise high-signal abstract section instead.

Use `## TL;DR` for one or two short paragraphs that answer three questions immediately:

1. what problem the paper solves
2. what method or idea it introduces
3. what result or practical takeaway matters most

## Writing Principles

Write natural paragraphs with durable wording. Explain the paper as if you understand the author's actual argument, not as a template summary.

Use the paper's real problem, method, equations, figures, tables, and conclusions. Explain the figures or tables that carry the method, the main result, the ablation, or the mechanism.

Keep the tone rigorous and readable. Favor clear verbs and concrete nouns. Use the paper's own terms when they are the right technical labels.

## Formula Policy

Reader-facing prose includes the actual formula when the formula is central to the method.

Write important equations directly in display math, then explain them immediately:

1. write the formula itself
2. name each variable and symbol
3. state what the formula computes
4. connect the formula to the method's intuition or training procedure

Use equation labels from the source paper only as lookup support during drafting. The final wiki prose should present the formula itself instead of relying on references such as `Equation (2)` or `(12)` as the main explanation.

Prefer readable mathematical prose over raw LaTeX narration. Keep symbols that carry meaning. Translate long chains of notation into sentences that tell the reader what changes, what stays fixed, and what quantity is optimized or constrained.

## Academic Style Structure

Write the page as a coherent article with this flow:

### TL;DR

Start with one or two compact paragraphs that capture the paper's problem, method, and main payoff. This section gives the reader the whole point before the deeper explanation starts.

### Motivation

Use two or three paragraphs to explain the problem, why it matters, and what pressure or limitation in earlier methods created room for this paper.

### Background

Use three or four paragraphs to explain the prior methods, definitions, or mathematical setup that the reader needs before the new method makes sense. Simple examples are useful when they shorten the distance to the main idea.

### Core Contribution

Use four or five paragraphs to state the central idea, the method design, and the technical innovations. This section carries the author's main claim.

### Formula Explanation

Select the equations that define the method, the objective, the constraint, the estimator, or the theorem. Show the formulas directly. Explain variables, quantities, and intuition in full sentences right after each formula.

### Experiments

Use two or three paragraphs covering the benchmark setting, comparison baselines, decisive figures or tables, and the strongest empirical evidence.

### Deeper Analysis

Use two or three paragraphs for ablations, sensitivity, mechanism analysis, optimization behavior, or theoretical interpretation that explains why the method works.

### Reflection

Use one or two paragraphs for the core insight, limitations, and likely next directions.

## Storytelling Style

Use this style only when the user explicitly asks for `storytelling`.

Open with a concrete question, scene, or simple example that makes the problem visible. Introduce the historical background before the new method so the reader sees why the paper's idea became necessary. Reuse one simple example through the article when that helps. End with one crisp sentence that captures the paper's central insight.

## Output Rules

The user sees only the final article-style summary. The page contains the final writing and no analysis process.

Prefer paragraphs over bullet lists. Use lists for compact comparisons, variables, or tightly structured observations when the list structure improves readability.

Each section should earn its space. Explain the equations that matter, the figures that matter, and the claims that matter.
