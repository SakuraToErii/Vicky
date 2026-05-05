# Source Summary Guide

Use this guide when writing the Summary section for an academic paper source page.

## Default Mode

Write in **academic** style unless the user explicitly asks for another style. Use precise terminology, rigorous phrasing, and the paper's original concepts. The output should be Markdown prose that works as a durable wiki note.

Use `no-code` by default. Use `with-code` only when the paper provides a GitHub repository and the user asks for code analysis. In `with-code` mode, inspect the repository, quote only key source snippets, and explain how the implementation corresponds to the paper.

## Paper Information

Start the summary by identifying the paper title, link, authors or team, venue/year when available, and source kind. Prefer metadata from the source file and Semantic Scholar when available.

## Writing Principles

Avoid generic AI phrasing such as "delves into", "crucial", "in the field of", or inflated transitions. Avoid mechanical section titles inside the summary. Avoid raw LaTeX syntax in prose; explain formulas in readable language and keep mathematical symbols only when they are necessary.

Use natural paragraphs. Explain every key figure or table that matters for understanding the paper. Select the figures that carry the method, experiments, ablations, or mechanism analysis.

## Academic Style Structure

Write the summary as a coherent article with this flow:

1. **Paper information**: title, link, authors or team.
2. **Motivation**: two or three paragraphs explaining the problem, why it matters, and why existing methods leave room for this work.
3. **Background**: three or four paragraphs explaining the necessary prior methods or concepts, with simple examples when helpful.
4. **Core contribution**: four or five paragraphs stating the central idea, the method design, and the main technical innovations.
5. **Formula explanation**: explain important equations in detail. Name each variable, describe what the equation computes, and connect the formula to the method's intuition.
6. **Experiments**: two or three paragraphs covering key results, comparison baselines, important figures or tables, and the strongest empirical evidence.
7. **Deeper analysis**: two or three paragraphs covering mechanism analysis, ablations, sensitivity studies, or why the method works.
8. **Reflection**: one or two paragraphs stating the core insight, limitations, and likely future directions.

## Storytelling Style

Use this style only when the user explicitly asks for `storytelling`.

Start from intuition rather than technique. Open with a concrete question, scene, or simple example that exposes the problem. Introduce the historical background before the new method, so the reader understands why the paper's idea was needed. Reuse one simple example throughout the article. Use vivid analogies when they make an abstract mechanism concrete. Move from simple problem to harder problem to solution. End with one crisp sentence that captures the paper's central insight.

## Output Rules

The user should see only the final article-style summary. Do not include the analysis process. Prefer paragraphs over bullet lists. Use lists only for paper metadata or compact comparisons where prose would be less readable.
