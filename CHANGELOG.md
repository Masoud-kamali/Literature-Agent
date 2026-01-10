# Changelog

All notable changes to the Literature Agent project.

## [2.0.0] - 2026-01-10

### Added
- **Reddit Integration**: Added `reddit_client.py` to fetch tools/discussions from r/PlayCanvas and r/GaussianSplatting
- **Two-Agent Reflection System**: 
  - Critic Agent evaluates descriptions for conciseness, engagement, and precision
  - Reviser Agent improves text with engaging verbs and smooth transitions
- **Smart Description Formatting**: `_create_smooth_description()` method for flowing paragraphs
- **Configuration Options**: `OUTPUT_FORMAT` setting to choose 2 papers + 1 tool or 3 papers

### Changed
- **Description Format**: Changed from "We introduce..." academic style to "PaperName tackles..." engaging style
- **Output Structure**: Changed from 2 separate paragraphs to 3-sentence flowing paragraph
- **Sentence Transitions**: Added smooth connectors ("The approach...", "By...", "Experiments show...")
- **Results Precision**: Now requires specific metrics (%, times faster) instead of vague claims
- **Temperature Settings**: Lowered from 0.7 to 0.3 for more consistent, controlled output

### Improved
- **Prompt Engineering**: Added clear BEFORE/AFTER examples in prompts
- **Post-Processing**: Aggressive cleaning to remove "We/Our" and ensure proper flow
- **LinkedIn Format**: Tool displayed first, then papers (more engaging order)
- **Character Limits**: Papers <300 chars, Tools <150 chars per description

### Fixed
- Text cutting mid-word (now cuts at natural break points)
- Title repetition in descriptions (now uses short paper name once)
- Verbose academic language (now punchy and accessible)
- Disconnected sentences (now smooth transitions)

## [1.0.0] - 2025-12-30

### Initial Release
- Multi-source retrieval (arXiv, OpenAlex, CVF)
- Local LLM integration with vLLM
- Basic reflection agent
- Smart deduplication with CSV ledger
- Combined LinkedIn posts
- Australian English output

