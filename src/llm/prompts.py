"""Prompt templates for LLM generation and reflection."""

# ============================================================================
# GENERATION PROMPTS (Australian English, Academic Tone)
# ============================================================================

SYSTEM_PROMPT = """You are an expert academic writer specialising in computer vision and 3D graphics research. You write in Australian English with an academic tone, suitable for researchers and industry professionals. You are precise, factual, and avoid marketing language or hype."""


ABSTRACT_REWRITE_PROMPT = """Write EXACTLY 3 short sentences about this paper in ONE PARAGRAPH.

❌ WRONG (verbose):
"We introduce OceanSplat, a novel 3D Gaussian Splatting-based approach for accurately representing 3D geometry in underwater scenes. Our method addresses multi-view inconsistencies caused by underwater optical degradation..."

✅ CORRECT (concise & connected paragraph):
OceanSplat tackles underwater 3D reconstruction with trinocular view consistency. The approach enforces geometric constraints via inverse warping and depth regularization. Experiments demonstrate 30% fewer artifacts and superior reconstruction quality compared to existing methods.

RULES:
- EXACTLY 3 sentences in ONE flowing paragraph (8-12 words each)
- Start with paper name: "{title}"
- NEVER use "We" or "Our" or "This paper"
- Make it punchy and attractive with smooth transitions
- Sentence 1: What innovation does (paper name + problem)
- Sentence 2: How method works (use transition: "The approach...", "By...")
- Sentence 3: PRECISE results with metrics/improvements (not vague!)

Paper: {title}
Authors: {authors}
Abstract: {abstract}

Write 3 sentences as one paragraph (paper name first, NO "We"):"""


PROBLEM_STATEMENT_PROMPT = """Given the paper metadata and abstract below, write a brief 1-line tagline capturing why this matters.

Requirements:
- Use Australian English spelling and grammar
- Write EXACTLY 1 sentence (10-20 words)
- Explain the practical impact or significance
- Make it engaging and accessible
- Do NOT speculate beyond what is stated in the abstract

Paper Title: {title}
Authors: {authors}
Year: {year}

Abstract:
{abstract}

Write the 1-line tagline now:"""


# Special prompts for Reddit posts/tools
REDDIT_DESCRIPTION_PROMPT = """Write EXACTLY 3 short sentences about this tool/discussion in ONE PARAGRAPH.

❌ WRONG (calls it "paper"):
"This paper presents an exploration of synthetic 3DGS from games..."

✅ CORRECT (flowing paragraph):
Community guide for generating 3DGS from game engines. Covers camera arrays, AI tools, and synthetic videos.

RULES:
- EXACTLY 3 sentences in ONE flowing paragraph (6-10 words each)
- This is a TOOL/RESOURCE/DISCUSSION - NOT a paper!
- Make it punchy and attractive
- Sentence 1: What it is
- Sentence 2: Why useful

Title: {title}
From: {venue}
Content: {abstract}

Write 3 sentences as one paragraph (NOT "paper"):"""


REDDIT_TAGLINE_PROMPT = """Given the Reddit post metadata below, write a brief 1-line tagline.

Requirements:
- Use Australian English spelling and grammar
- Write EXACTLY 1 sentence (8-15 words)
- Capture the essence or value proposition
- Make it catchy and relevant

Post Title: {title}
Content: {abstract}

Write the 1-line tagline now:"""


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
[1-3 sentences describing the key contribution]

### Problem Addressed
[1-3 sentences explaining what problem it solves]

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


CRITIC_PROMPT = """Review the generated outputs and score based on CONCISENESS, INTERACTIVITY, and STYLE.

Paper: {title}
Abstract: {abstract}

Generated Output:
{abstract_rewrite}

Evaluation Criteria (strict scoring):
1. **CONCISENESS**: Is each line under 85 chars? Total under 300 chars? (Critical!)
2. **INTERACTIVITY**: Uses engaging verbs (tackles, enables, achieves vs introduces, presents)?
3. **NO VERBOSITY**: No "We/Our/This paper" starts? No "Furthermore/Additionally"?
4. **LINE FORMAT**: Exactly 3 separate lines (not paragraph)?
5. **FACTUALITY**: Claims only from abstract?
6. **ENGAGING**: Compelling for LinkedIn audience?

SCORING:
- 9-10: Perfect (short, engaging, well-formatted)
- 7-8: Good but needs minor tweaks
- <7: Too long, boring, or poorly formatted (MUST revise)

Provide JSON critique:
{{
  "description_issues": ["Too long (>300 chars)", "Uses 'We introduce'", "Not 3 lines"],
  "revision_actions": ["Cut 50% of words", "Use 'tackles' instead of 'introduces'", "Split into 3 lines"],
  "overall_score": 6
}}

Score strictly - most outputs need revision to be SHORT and ENGAGING.

Provide your critique now:"""


REVISER_PROMPT = """Your job: Make these descriptions SHORT, CONCISE, and INTERACTIVE for LinkedIn.

Paper: {title}
Authors: {authors}

Original Abstract: {abstract}

Current Outputs (TOO LONG):
{abstract_rewrite}

Critique: {critique}
Actions: {revision_actions}

REVISION RULES:
1. **SHORTEN AGGRESSIVELY**: Cut 50% of words, keep only key points
2. **MAKE INTERACTIVE**: Use engaging language ("tackles", "enables", "achieves")
3. **REMOVE VERBOSITY**: No "We introduce", "Our method", "Furthermore"
4. **START WITH NAME**: Use paper name (first 2 words of title)
5. **SMOOTH TRANSITIONS**: Connect sentences naturally ("The approach...", "By...", "Experiments show...")
6. **PRECISE RESULTS**: Include specific metrics (%, times faster, accuracy improvements)
7. **3 PUNCHY SENTENCES IN ONE PARAGRAPH**: Each sentence 8-12 words max
   - Sentence 1: What innovation does (start with paper name)
   - Sentence 2: How it works with transition (method/technique)
   - Sentence 3: SPECIFIC results with numbers (not vague!)

EXAMPLE TRANSFORMATION:
❌ BEFORE (verbose): "We introduce OceanSplat, a novel 3D Gaussian Splatting-based approach for accurately representing 3D geometry in underwater scenes. Our method addresses multi-view inconsistencies caused by underwater optical degradation by enforcing trinocular view consistency through rendering horizontally and vertically translated camera views..."

✅ AFTER (concise, connected & precise): 
"OceanSplat tackles underwater 3D reconstruction with trinocular consistency. The approach enforces geometric constraints via inverse warping and depth regularization. Experiments demonstrate 30% fewer artifacts and superior reconstruction quality compared to baseline methods."

Now revise to be SHORT, CONCISE, and INTERACTIVE:

Return JSON:
{{
  "abstract_rewrite": "Sentence 1. Sentence 2. Sentence 3.",
  "problem_solved": "One catchy tagline",
  "linkedin_post": ""
}}

Write revised SHORT version now:"""
