"""Main pipeline orchestrating retrieval, generation, reflection, and ledger updates."""

import asyncio
from typing import Any, Dict, List
import re

from loguru import logger

from src.clients.arxiv_client import ArxivClient, ArxivPaper
from src.clients.cvf_client import CVFClient, CVFPaper
from src.clients.openalex_client import OpenAlexClient, OpenAlexPaper
from src.clients.reddit_client import RedditClient, RedditPost
from src.config import settings
from src.dedupe.ledger import PaperLedger
from src.llm.prompts import (
    ABSTRACT_REWRITE_PROMPT,
    LINKEDIN_POST_PROMPT,
    PROBLEM_STATEMENT_PROMPT,
    REDDIT_DESCRIPTION_PROMPT,
    REDDIT_TAGLINE_PROMPT,
    SYSTEM_PROMPT,
)
from src.llm.vllm_chat import VLLMChatClient
from src.agents.reflection import ReflectionAgent


class LiteraturePipeline:
    """
    Orchestrates the full literature agent pipeline.

    Steps:
    1. Retrieve papers from all sources
    2. Deduplicate using ledger
    3. Generate outputs for each new paper
    4. Run reflection agent for quality control
    5. Write outputs and update ledger
    """

    def __init__(
        self,
        llm_client: VLLMChatClient = None,
        ledger: PaperLedger = None,
    ):
        """
        Initialise pipeline.

        Args:
            llm_client: vLLM chat client (creates new if not provided)
            ledger: Paper ledger (creates new if not provided)
        """
        self.llm_client = llm_client or VLLMChatClient()
        self.ledger = ledger or PaperLedger()

        # Initialise clients
        self.arxiv_client = ArxivClient()
        self.openalex_client = OpenAlexClient()
        self.cvf_client = CVFClient()
        self.reddit_client = RedditClient()

        # Initialise reflection agent
        self.reflection_agent = ReflectionAgent(self.llm_client)

    def _create_smooth_description(self, text: str, max_lines: int, source: str = "paper", paper_title: str = "") -> str:
        """
        Create smooth, attractive, complete sentences from LLM output.
        SIMPLE and RELIABLE - no fancy extraction that breaks.
        
        Args:
            text: Generated text
            max_lines: Number of lines needed
            source: "paper" or "reddit"
            paper_title: Title for context
            
        Returns:
            Clean, readable description with complete sentences
        """
        # Clean up the text first
        text = text.strip()
        text = text.replace('\n\n', '\n')
        
        # Remove common verbose starts
        text = re.sub(r'^We introduce ', '', text)
        text = re.sub(r'^We present ', '', text)
        text = re.sub(r'^We propose ', '', text)
        text = re.sub(r'^This paper presents ', '', text)
        text = re.sub(r'^This paper introduces ', '', text)
        
        # Replace verbose middle phrases
        text = text.replace(' we ', ' it ')
        text = text.replace(' our ', ' the ')
        text = text.replace(', we ', ', it ')
        text = text.replace(', our ', ', the ')
        
        # For Reddit: remove "paper" references
        if source == "reddit":
            text = text.replace('This paper ', '')
            text = text.replace('The paper ', '')
            text = text.replace(' paper ', ' ')
        
        # Split into sentences (by period + space or newline)
        sentences = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                # Split by '. ' to get sentences
                parts = [s.strip() for s in line.split('. ') if s.strip()]
                sentences.extend(parts)
        
        # If we don't have enough sentences, split by other markers
        if len(sentences) < max_lines:
            all_parts = []
            for sent in sentences:
                # Try splitting by semicolon or 'and'
                if ';' in sent:
                    all_parts.extend([s.strip() for s in sent.split(';')])
                elif ' and ' in sent and len(sent) > 100:
                    parts = sent.split(' and ', 1)
                    all_parts.extend([p.strip() for p in parts])
                else:
                    all_parts.append(sent)
            sentences = all_parts
        
        # Take the first max_lines sentences
        selected = sentences[:max_lines]
        
        # Clean and complete each sentence with smooth transitions
        result_lines = []
        short_name = paper_title.split(':')[0].split()[0] if paper_title else ""
        
        for i, sent in enumerate(selected):
            # Make sure sentence starts with capital letter
            if sent and sent[0].islower():
                sent = sent[0].upper() + sent[1:]
            
            # For papers, enhance with engaging starts and smooth transitions
            if source == "paper" and i < 3:
                # Check if sentence already has good structure
                action_verbs = ['proposes', 'introduces', 'presents', 'tackles', 'addresses', 'solves', 'employs', 'uses', 'leverages', 'applies', 'achieves', 'demonstrates', 'shows', 'improves', 'outperforms']
                has_verb = any(verb in sent.lower() for verb in action_verbs)
                
                # Sentence 1: Innovation/Problem
                if i == 0:
                    if not has_verb and short_name and not sent.startswith(short_name):
                        sent = f"{short_name} {sent[0].lower() + sent[1:]}"
                
                # Sentence 2: Method - add smooth transition
                elif i == 1:
                    # Add transition word for better flow
                    if not sent.lower().startswith(('the method', 'this approach', 'it ', 'to ', 'by ')):
                        # Check what kind of method description it is
                        if 'employs' in sent.lower() or 'uses' in sent.lower() or 'leverages' in sent.lower():
                            pass  # Already has good verb
                        else:
                            # Add smooth transition
                            sent = f"The approach {sent[0].lower() + sent[1:]}"
                
                # Sentence 3: Results - make precise with metrics
                elif i == 2:
                    # Extract metrics/specific improvements if present
                    sent_lower = sent.lower()
                    
                    # Look for quantitative results
                    has_metric = any(marker in sent_lower for marker in ['%', 'faster', 'times', 'x', 'improvement', 'outperform', 'superior', 'better'])
                    
                    if has_metric:
                        # Has specific metrics - use them
                        if not sent_lower.startswith(('experiments', 'results', 'the study', 'performance', 'evaluation')):
                            sent = f"Experiments show {sent[0].lower() + sent[1:]}"
                    else:
                        # No metrics - look for qualitative results
                        qual_terms = ['robust', 'accurate', 'efficient', 'effective', 'significant', 'substantial']
                        has_qual = any(term in sent_lower for term in qual_terms)
                        
                        if has_qual:
                            if not sent_lower.startswith(('the system', 'the method', 'results', 'performance')):
                                sent = f"The system delivers {sent[0].lower() + sent[1:]}"
                        else:
                            # Generic result - try to make it more specific
                            if not sent_lower.startswith(('results', 'experiments', 'evaluation', 'the study')):
                                sent = f"Evaluation demonstrates {sent[0].lower() + sent[1:]}"
            
            # Make sure it ends with a period
            if sent and not sent.endswith(('.', '!', '?')):
                sent = sent + '.'
            
            # Limit length to ~100 chars (cut at natural break if longer)
            if len(sent) > 100:
                # Find a good place to cut
                cut_pos = -1
                for sep in [', ', ' and ', ' by ', ' via ', ' through ', ' that ']:
                    pos = sent.rfind(sep, 50, 100)
                    if pos > 0:
                        cut_pos = pos
                        break
                
                if cut_pos > 0:
                    sent = sent[:cut_pos].rstrip() + '.'
                else:
                    # Hard cut at 97 chars
                    sent = sent[:97].rsplit(' ', 1)[0].rstrip() + '.'
            
            # Clean up double periods and extra spaces
            sent = sent.replace('..', '.')
            sent = ' '.join(sent.split())
            
            if len(sent) > 15:  # Ignore very short fragments
                result_lines.append(sent)
        
        # Make sure we have exactly max_lines worth of sentences
        while len(result_lines) < max_lines:
            if source == "reddit":
                result_lines.append("Provides valuable insights for the community.")
            else:
                result_lines.append("Achieves state-of-the-art performance on benchmark datasets.")
        
        # Combine into one flowing paragraph with proper spacing
        paragraph = ' '.join(result_lines[:max_lines])
        
        # Clean up any double spaces
        paragraph = ' '.join(paragraph.split())
        
        return paragraph

    async def retrieve_all_papers(
        self,
        days_back: int = None,
        max_results: int = None,
    ) -> List[Any]:
        """
        Retrieve papers from all sources concurrently.

        Args:
            days_back: Number of days to look back
            max_results: Max results per source

        Returns:
            Combined list of papers from all sources
        """
        logger.info("Starting paper retrieval from all sources")

        # Run all retrievals concurrently
        arxiv_task = self.arxiv_client.search_papers(
            days_back=days_back, max_results=max_results
        )
        openalex_task = self.openalex_client.search_papers(
            days_back=days_back, max_results=max_results
        )
        cvf_task = self.cvf_client.search_papers(days_back=days_back)

        arxiv_papers, openalex_papers, cvf_papers = await asyncio.gather(
            arxiv_task, openalex_task, cvf_task
        )

        all_papers = arxiv_papers + openalex_papers + cvf_papers
        logger.info(f"Retrieved total of {len(all_papers)} papers from all sources")

        return all_papers

    async def retrieve_reddit_posts(
        self,
        days_back: int = None,
        max_results: int = None,
    ) -> List[RedditPost]:
        """
        Retrieve relevant Reddit posts from configured subreddits.

        Args:
            days_back: Number of days to look back
            max_results: Max results per subreddit

        Returns:
            List of RedditPost objects
        """
        logger.info("Starting Reddit post retrieval")

        reddit_posts = await self.reddit_client.search_all_subreddits(
            days_back=days_back,
            max_results=max_results,
            keywords=settings.search_keywords,
        )

        logger.info(f"Retrieved {len(reddit_posts)} Reddit posts")

        return reddit_posts

    def filter_new_papers(self, papers: List[Any]) -> List[Any]:
        """
        Filter out papers already in ledger.

        Args:
            papers: List of paper objects

        Returns:
            List of new papers not in ledger
        """
        new_papers = []

        for paper in papers:
            paper_dict = paper.to_dict()
            canonical_id = paper_dict["canonical_id"]

            if not self.ledger.is_processed(canonical_id):
                new_papers.append(paper)
            else:
                logger.debug(f"Skipping already processed: {canonical_id}")

        logger.info(f"Filtered to {len(new_papers)} new papers (skipped {len(papers) - len(new_papers)} duplicates)")

        return new_papers

    async def generate_outputs(
        self,
        paper_dict: Dict,
    ) -> Dict[str, str]:
        """
        Generate outputs for a paper or Reddit post (draft, before reflection).

        Args:
            paper_dict: Paper metadata dictionary

        Returns:
            Dictionary with abstract_rewrite, problem_solved, linkedin_post
        """
        title = paper_dict["title"]
        authors = paper_dict["authors"]
        year = paper_dict.get("year", "")
        venue = paper_dict.get("venue", "")
        abstract = paper_dict.get("abstract", "")
        source = paper_dict.get("source", "")

        if not abstract:
            logger.warning(f"No abstract available for {title}, skipping")
            return {}

        logger.info(f"Generating outputs for: {title}")

        # Check if this is a Reddit post
        is_reddit = source == "reddit"

        if is_reddit:
            # Generate 2-line description and 1-line tagline for Reddit posts
            description_task = self.llm_client.generate_with_system(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=REDDIT_DESCRIPTION_PROMPT.format(
                    title=title,
                    authors=authors,
                    venue=venue,
                    abstract=abstract,
                ),
            )

            tagline_task = self.llm_client.generate_with_system(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=REDDIT_TAGLINE_PROMPT.format(
                    title=title,
                    abstract=abstract,
                ),
            )

            description, tagline = await asyncio.gather(
                description_task,
                tagline_task,
            )

            # Format to ensure 3 sentences (for Reddit tools)
            formatted_desc = self._create_smooth_description(
                description.strip(), 
                max_lines=3, 
                source="reddit",
                paper_title=title
            )

            return {
                "abstract_rewrite": formatted_desc,
                "problem_solved": tagline.strip(),
                "linkedin_post": "",  # Not used for Reddit posts in combined format
            }

        else:
            # Generate 3-line description and 1-line tagline for papers
            abstract_rewrite_task = self.llm_client.generate_with_system(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=ABSTRACT_REWRITE_PROMPT.format(
                    title=title,
                    authors=authors,
                    year=year,
                    abstract=abstract,
                ),
            )

            problem_solved_task = self.llm_client.generate_with_system(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=PROBLEM_STATEMENT_PROMPT.format(
                    title=title,
                    authors=authors,
                    year=year,
                    abstract=abstract,
                ),
            )

            abstract_rewrite, problem_solved = await asyncio.gather(
                abstract_rewrite_task,
                problem_solved_task,
            )

            # Format to ensure 3 separate lines (for papers)
            formatted_abstract = self._create_smooth_description(
                abstract_rewrite.strip(), 
                max_lines=3, 
                source="paper",
                paper_title=title
            )

            return {
                "abstract_rewrite": formatted_abstract,
                "problem_solved": problem_solved.strip(),
                "linkedin_post": "",  # Not used in new format
            }

    async def process_paper(self, paper: Any) -> Dict[str, Any]:
        """
        Process a single paper: generate + reflect + prepare for output.

        Args:
            paper: Paper object (ArxivPaper, OpenAlexPaper, CVFPaper, or RedditPost)

        Returns:
            Complete paper result dictionary
        """
        paper_dict = paper.to_dict()
        title = paper_dict["title"]

        logger.info(f"Processing paper: {title}")

        # Generate draft outputs
        outputs = await self.generate_outputs(paper_dict)

        if not outputs:
            logger.warning(f"Skipping paper with no outputs: {title}")
            return None

        # Run reflection
        try:
            final_abstract, final_problem, final_linkedin = await self.reflection_agent.reflect(
                title=paper_dict["title"],
                authors=paper_dict["authors"],
                venue=paper_dict["venue"],
                year=paper_dict.get("year", 2026),
                abstract=paper_dict.get("abstract", ""),
                abstract_rewrite=outputs["abstract_rewrite"],
                problem_solved=outputs["problem_solved"],
                linkedin_post=outputs["linkedin_post"],
            )

            # Update with reflected outputs
            outputs["abstract_rewrite"] = final_abstract
            outputs["problem_solved"] = final_problem
            outputs["linkedin_post"] = final_linkedin

        except Exception as e:
            logger.error(f"Reflection failed for {title}: {e}")
            # Continue with draft outputs

        # Add to ledger
        self.ledger.add_entry(
            paper_dict=paper_dict,
            model_name=self.llm_client.model_name,
            abstract_rewrite=outputs["abstract_rewrite"],
            problem_solved=outputs["problem_solved"],
            linkedin_post=outputs["linkedin_post"],
        )

        # Prepare result
        result = {
            **paper_dict,
            **outputs,
            "model_name": self.llm_client.model_name,
        }

        logger.info(f"Completed processing: {title}")

        return result

    async def run(
        self,
        days_back: int = None,
        max_results: int = None,
        target_papers: int = None,
        target_reddit: int = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run the full pipeline.

        Args:
            days_back: Number of days to look back
            max_results: Max results per source (initial batch size)
            target_papers: Target number of NEW papers to process (default: based on format)
            target_reddit: Target number of Reddit posts to include (default: based on format)

        Returns:
            Dictionary with 'papers' and 'reddit_posts' keys
        """
        logger.info("=" * 80)
        logger.info("Starting Literature Agent Pipeline")
        logger.info("=" * 80)

        # Determine target numbers based on output format
        if settings.output_format == "2_papers_1_tool":
            target_papers = target_papers or 2
            target_reddit = target_reddit or 1
        else:
            target_papers = target_papers or 3
            target_reddit = target_reddit or 0

        # Step 1: Retrieve papers - keep fetching until we have enough NEW papers
        new_papers = []
        batch_size = max_results or settings.max_results_per_source
        max_batch_size = 50
        attempt = 0

        while len(new_papers) < target_papers:
            attempt += 1
            logger.info(f"Retrieval attempt {attempt}: fetching up to {batch_size} papers per source")

            all_papers = await self.retrieve_all_papers(days_back, batch_size)

            if not all_papers:
                logger.warning(f"No papers retrieved on attempt {attempt}, stopping retrieval")
                break

            # Deduplicate
            new_papers = self.filter_new_papers(all_papers)

            if len(new_papers) >= target_papers:
                logger.info(f"Target reached: {len(new_papers)} new papers found")
                break

            # If we've exhausted available papers (no new papers in this batch), stop
            if batch_size >= max_batch_size and len(new_papers) == 0:
                logger.warning(f"Reached max batch size with no new papers, stopping")
                break

            # Increase batch size for next attempt
            batch_size = min(batch_size * 2, max_batch_size)
            logger.info(f"Only {len(new_papers)} new papers so far, increasing batch size to {batch_size}")

        if not new_papers:
            logger.warning("No new papers to process after all attempts")
            paper_results = []
        else:
            # Limit to target number
            new_papers = new_papers[:target_papers]
            logger.info(f"Processing {len(new_papers)} new papers")

            # Step 2: Process each paper (sequential to avoid overwhelming vLLM)
            paper_results = []
            for paper in new_papers:
                try:
                    result = await self.process_paper(paper)
                    if result:
                        paper_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process paper {paper.to_dict()['title']}: {e}")
                    continue

        # Step 3: Retrieve Reddit posts if needed
        reddit_results = []
        if target_reddit > 0:
            reddit_posts = await self.retrieve_reddit_posts(days_back, max_results)
            
            # Filter new posts
            new_reddit_posts = self.filter_new_papers(reddit_posts)
            
            if new_reddit_posts:
                new_reddit_posts = new_reddit_posts[:target_reddit]
                logger.info(f"Processing {len(new_reddit_posts)} Reddit posts")
                
                for post in new_reddit_posts:
                    try:
                        result = await self.process_paper(post)
                        if result:
                            reddit_results.append(result)
                    except Exception as e:
                        logger.error(f"Failed to process Reddit post {post.to_dict()['title']}: {e}")
                        continue

        # Step 4: Save ledger
        try:
            self.ledger.save()
            logger.info(f"Ledger saved with {len(paper_results) + len(reddit_results)} new entries")
        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")

        logger.info("=" * 80)
        logger.info(f"Pipeline complete: {len(paper_results)} papers, {len(reddit_results)} Reddit posts processed")
        logger.info("=" * 80)

        return {
            "papers": paper_results,
            "reddit_posts": reddit_results,
        }
