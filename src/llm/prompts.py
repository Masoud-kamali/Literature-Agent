"""Prompt templates for LLM generation and reflection."""

# ============================================================================
# GENERATION PROMPTS (Australian English, Academic Tone)
# ============================================================================

SYSTEM_PROMPT = """You are an expert academic writer specialising in computer vision and 3D graphics research. You write in Australian English with an academic tone, suitable for researchers and industry professionals. You are precise, factual, and avoid marketing language or hype."""


ABSTRACT_REWRITE_PROMPT = """Given the paper metadata and abstract below, write a technical abstract rewrite in one paragraph.

Requirements:
- Use Australian English spelling and grammar
- Maintain academic tone
- Highlight the key technical contribution
- Be concise (approximately 100-150 words)
- Do NOT add information not present in the original abstract
- Focus on methodology and results

Paper Title: {title}
Authors: {authors}
Year: {year}

Original Abstract:
{abstract}

Write the abstract rewrite now:"""


PROBLEM_STATEMENT_PROMPT = """Given the paper metadata and abstract below, write a concise statement of the problem being solved.

Requirements:
- Use Australian English spelling and grammar
- Write 2 to 4 sentences
- Clearly explain what gap or challenge the paper addresses
- Use academic tone
- Do NOT speculate beyond what is stated in the abstract

Paper Title: {title}
Authors: {authors}
Year: {year}

Abstract:
{abstract}

Write the problem statement now:"""


LINKEDIN_POST_PROMPT = """Given the paper metadata and abstract below, write a LinkedIn post suitable for academic and industry audiences.

Requirements:
- Use Australian English spelling and grammar
- Length: 120 to 180 words
- Include: paper title and year in the first line (NO venue/source information)
- Explain "why it matters" for researchers or practitioners
- Use an engaging but professional tone
- Avoid excessive marketing language
- Include 2-3 relevant hashtags at the end
- Do NOT fabricate claims not supported by the abstract

Paper Title: {title}
Authors: {authors}
Year: {year}

Abstract:
{abstract}

Write the LinkedIn post now:"""


COMBINED_LINKEDIN_POST_PROMPT = """Given the list of papers below, create a SINGLE combined LinkedIn post featuring all papers together.

Requirements:
- Use Australian English spelling and grammar
- Total length: 250-350 words
- Format the post as follows:

## Paper 1: [Title]
**Authors**: [Authors list]
**URL**: [URL]

### Technical Abstract
[1-2 sentences describing the key contribution]

### Problem Addressed
[1-2 sentences explaining what problem it solves]

## Paper 2: [Title]
...

## Paper 3: [Title]
...

- End with 3-5 relevant hashtags
- Do NOT include venue or source information
- Keep each paper section concise
- Use engaging but professional academic tone

Papers:
{papers_data}

Write the combined LinkedIn post now:"""


# ============================================================================
# REFLECTION PROMPTS (Critique and Revision)
# ============================================================================

CRITIC_SYSTEM_PROMPT = """You are a rigorous academic reviewer. Your role is to critique generated text for factuality, specificity, novelty framing, and adherence to style guidelines. You identify concrete issues and suggest actionable revisions."""


CRITIC_PROMPT = """Review the generated outputs for the paper below and provide a structured critique.

Paper Metadata:
Title: {title}
Authors: {authors}
Year: {year}

Original Abstract:
{abstract}

Generated Outputs:
1. Abstract Rewrite:
{abstract_rewrite}

2. Problem Statement:
{problem_solved}

3. LinkedIn Post:
{linkedin_post}

Evaluation Criteria:
1. Factuality: Does the text claim anything not present in the original abstract?
2. Specificity: Are technical details preserved? Is language precise?
3. Novelty Framing: Is the contribution clearly articulated?
4. Style: Does it follow Australian English and academic tone?
5. Length Constraints: Abstract rewrite ~100-150 words, problem statement 2-4 sentences, LinkedIn post 120-180 words

Provide your critique in the following JSON format:
{{
  "abstract_rewrite_issues": ["issue 1", "issue 2", ...],
  "problem_solved_issues": ["issue 1", "issue 2", ...],
  "linkedin_post_issues": ["issue 1", "issue 2", ...],
  "revision_actions": ["action 1", "action 2", ...],
  "overall_score": 0-10
}}

If overall_score >= 8, the outputs are acceptable. Otherwise, list specific revision actions.

Provide your critique now:"""


REVISER_PROMPT = """Given the critique below, revise the generated outputs for the paper.

Paper Metadata:
Title: {title}
Authors: {authors}
Year: {year}

Original Abstract:
{abstract}

Previous Outputs:
1. Abstract Rewrite:
{abstract_rewrite}

2. Problem Statement:
{problem_solved}

3. LinkedIn Post:
{linkedin_post}

Critique:
{critique}

Revision Actions:
{revision_actions}

Apply the revision actions and produce improved outputs. Maintain all original requirements (Australian English, academic tone, length constraints).

Provide the revised outputs in JSON format:
{{
  "abstract_rewrite": "...",
  "problem_solved": "...",
  "linkedin_post": "..."
}}

Write the revised outputs now:"""
