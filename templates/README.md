# Templates

This directory contains templates used by the literature agent.

## LinkedIn Post Template

[linkedin_post_template.md](linkedin_post_template.md) - Template for LinkedIn posts about 3D Gaussian Splatting papers.

### Usage

The template is automatically used by the `OutputWriter` class when generating weekly reports. When you run:

```bash
python scripts/run_weekly.py
```

The generated weekly report (`output/week_YYYY_MM_DD/weekly_report.md`) will include a "Combined LinkedIn Post" section formatted according to this template.

### Manual Usage

You can also manually copy and fill in the template:

1. Copy the template content
2. Replace placeholders:
   - `[Paper Title]` → actual paper title
   - `[Author Names]` → comma-separated author names
   - `[arXiv PDF URL]` → paper PDF link
   - `[1-2 sentences...]` → your summaries
3. Post to LinkedIn

### Format

The template uses emoji icons for visual structure:
- 🔍 Main header
- 🧩 Paper title
- 👥 Authors
- 🔗 PDF link
- 💡 Core Idea (main contribution)
- 🎯 Why It Matters (significance)
