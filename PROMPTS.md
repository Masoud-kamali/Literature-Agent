# Prompt Templates Reference

This document contains all prompts used by the literature agent. All prompts are defined in [`src/llm/prompts.py`](src/llm/prompts.py).

---

## System Prompts

### Main System Prompt

**Used for**: All generation tasks (abstract rewrite, problem statement, LinkedIn post)

```
You are an expert academic writer specialising in computer vision and 3D graphics research. You write in Australian English with an academic tone, suitable for researchers and industry professionals. You are precise, factual, and avoid marketing language or hype.
```

### Critic System Prompt

**Used for**: Reflection agent critique phase

```
You are a rigorous academic reviewer. Your role is to critique generated text for factuality, specificity, novelty framing, and adherence to style guidelines. You identify concrete issues and suggest actionable revisions.
```

---

## Generation Prompts

### 1. Abstract Rewrite Prompt

**Purpose**: Generate technical abstract rewrite (1 paragraph, ~100-150 words)

**Template**:
```
Given the paper metadata and abstract below, write a technical abstract rewrite in one paragraph.

Requirements:
- Use Australian English spelling and grammar
- Maintain academic tone
- Highlight the key technical contribution
- Be concise (approximately 100-150 words)
- Do NOT add information not present in the original abstract
- Focus on methodology and results

Paper Title: {title}
Authors: {authors}
Venue: {venue}
Year: {year}

Original Abstract:
{abstract}

Write the abstract rewrite now:
```

**Variables**:
- `{title}`: Paper title
- `{authors}`: Comma or semicolon-separated author list
- `{venue}`: Venue name (e.g., "arXiv", "CVPR 2024")
- `{year}`: Publication year
- `{abstract}`: Original abstract text

---

### 2. Problem Statement Prompt

**Purpose**: Generate concise problem statement (2-4 sentences)

**Template**:
```
Given the paper metadata and abstract below, write a concise statement of the problem being solved.

Requirements:
- Use Australian English spelling and grammar
- Write 2 to 4 sentences
- Clearly explain what gap or challenge the paper addresses
- Use academic tone
- Do NOT speculate beyond what is stated in the abstract

Paper Title: {title}
Authors: {authors}
Venue: {venue}
Year: {year}

Abstract:
{abstract}

Write the problem statement now:
```

**Variables**: Same as Abstract Rewrite Prompt

---

### 3. LinkedIn Post Prompt

**Purpose**: Generate LinkedIn-ready post (120-180 words)

**Template**:
```
Given the paper metadata and abstract below, write a LinkedIn post suitable for academic and industry audiences.

Requirements:
- Use Australian English spelling and grammar
- Length: 120 to 180 words
- Include: paper title, venue, and year in the first line
- Explain "why it matters" for researchers or practitioners
- Use an engaging but professional tone
- Avoid excessive marketing language
- Include 2-3 relevant hashtags at the end
- Do NOT fabricate claims not supported by the abstract

Paper Title: {title}
Authors: {authors}
Venue: {venue}
Year: {year}

Abstract:
{abstract}

Write the LinkedIn post now:
```

**Variables**: Same as Abstract Rewrite Prompt

---

## Reflection Prompts

### 4. Critic Prompt

**Purpose**: Review generated outputs and provide structured critique

**Template**:
```
Review the generated outputs for the paper below and provide a structured critique.

Paper Metadata:
Title: {title}
Authors: {authors}
Venue: {venue}
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
{
  "abstract_rewrite_issues": ["issue 1", "issue 2", ...],
  "problem_solved_issues": ["issue 1", "issue 2", ...],
  "linkedin_post_issues": ["issue 1", "issue 2", ...],
  "revision_actions": ["action 1", "action 2", ...],
  "overall_score": 0-10
}

If overall_score >= 8, the outputs are acceptable. Otherwise, list specific revision actions.

Provide your critique now:
```

**Variables**:
- All from generation prompts, plus:
- `{abstract_rewrite}`: Generated abstract rewrite
- `{problem_solved}`: Generated problem statement
- `{linkedin_post}`: Generated LinkedIn post

**Expected Output**: JSON object with critique and score

**Scoring**:
- **8-10**: Outputs accepted as-is
- **0-7**: Proceed to revision step

---

### 5. Reviser Prompt

**Purpose**: Apply critique feedback to produce improved outputs

**Template**:
```
Given the critique below, revise the generated outputs for the paper.

Paper Metadata:
Title: {title}
Authors: {authors}
Venue: {venue}
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
{
  "abstract_rewrite": "...",
  "problem_solved": "...",
  "linkedin_post": "..."
}

Write the revised outputs now:
```

**Variables**:
- All previous variables, plus:
- `{critique}`: Full critique JSON from critic
- `{revision_actions}`: Bulleted list of actions (e.g., "- Remove speculative claim about performance\n- Add specific technical detail about Gaussian primitives")

**Expected Output**: JSON object with revised outputs

---

## Prompt Engineering Notes

### Australian English Enforcement

All prompts explicitly require "Australian English spelling and grammar" to ensure:
- "optimised" not "optimized"
- "whilst" not "while"
- "summarise" not "summarize"
- "colour" not "color"

### Factuality Constraints

Key phrases used across prompts:
- "Do NOT add information not present in the original abstract"
- "Do NOT fabricate claims not supported by the abstract"
- "Do NOT speculate beyond what is stated in the abstract"

These prevent hallucination and ensure all claims are grounded in source material.

### Tone Guidance

**Academic tone characteristics**:
- Precise technical language
- Avoid hype and marketing speak
- Professional but accessible
- Focus on methodology and contribution

**LinkedIn tone balance**:
- "Engaging but professional"
- Includes "why it matters" framing for broader audience
- Allows emoji sparingly (in practice, models use 1-2 relevant emoji)

### Length Constraints

Enforced across all prompts:
- **Abstract rewrite**: ~100-150 words (one paragraph)
- **Problem statement**: 2-4 sentences
- **LinkedIn post**: 120-180 words

The reflection critic specifically checks these constraints.

### Temperature Settings

- **Generation**: 0.7 (default, creative but controlled)
- **Critique**: 0.3 (low, consistent evaluation)
- **Revision**: 0.7 (same as generation)

Defined in [`src/config.py`](src/config.py).

---

## Customisation Guide

### Modifying Prompts

To customise prompts for your domain:

1. **Edit** [`src/llm/prompts.py`](src/llm/prompts.py)
2. **Adjust** requirements section in each prompt
3. **Test** with sample papers
4. **Iterate** based on output quality

### Adding New Outputs

To add a fourth output type (e.g., "Key Findings"):

1. **Create prompt** in `prompts.py`:
   ```python
   KEY_FINDINGS_PROMPT = """..."""
   ```

2. **Update** `pipeline.py` `generate_outputs()` to call new prompt

3. **Update** `reflection.py` critic to evaluate new output

4. **Update** ledger schema in `ledger.py` to store new field

### Domain Adaptation

For other research areas (e.g., NLP, biology):

1. **System prompt**: Change "computer vision and 3D graphics" to your domain
2. **Search keywords**: Update in `config.py`
3. **Venue lists**: Adjust CVF venues or add new data sources
4. **Terminology**: Ensure prompts use domain-appropriate language

---

## Prompt Testing

Test individual prompts:

```python
from src.llm.vllm_chat import VLLMChatClient
from src.llm.prompts import ABSTRACT_REWRITE_PROMPT, SYSTEM_PROMPT
import asyncio

async def test_prompt():
    client = VLLMChatClient()

    test_data = {
        "title": "Test Paper",
        "authors": "Author A, Author B",
        "venue": "CVPR",
        "year": 2024,
        "abstract": "This paper presents a novel approach to...",
    }

    result = await client.generate_with_system(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=ABSTRACT_REWRITE_PROMPT.format(**test_data),
    )

    print(result)

asyncio.run(test_prompt())
```

---

## Version History

- **v0.1.0** (2024-01): Initial prompts with Australian English, reflection agent
- Future versions may refine based on user feedback

---

For implementation details, see [`src/llm/prompts.py`](src/llm/prompts.py).
