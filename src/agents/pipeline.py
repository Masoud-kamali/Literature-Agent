"""Main pipeline orchestrating retrieval, generation, reflection, and ledger updates."""

import asyncio
from typing import Any, Dict, List

from loguru import logger

from src.clients.arxiv_client import ArxivClient, ArxivPaper
from src.clients.cvf_client import CVFClient, CVFPaper
from src.clients.openalex_client import OpenAlexClient, OpenAlexPaper
from src.config import settings
from src.dedupe.ledger import PaperLedger
from src.llm.prompts import (
    ABSTRACT_REWRITE_PROMPT,
    LINKEDIN_POST_PROMPT,
    PROBLEM_STATEMENT_PROMPT,
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

        # Initialise reflection agent
        self.reflection_agent = ReflectionAgent(self.llm_client)

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
        Generate all three outputs for a paper (draft, before reflection).

        Args:
            paper_dict: Paper metadata dictionary

        Returns:
            Dictionary with abstract_rewrite, problem_solved, linkedin_post
        """
        title = paper_dict["title"]
        authors = paper_dict["authors"]
        year = paper_dict["year"]
        abstract = paper_dict.get("abstract", "")

        if not abstract:
            logger.warning(f"No abstract available for {title}, skipping")
            return {}

        logger.info(f"Generating outputs for: {title}")

        # Generate all three outputs concurrently
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

        linkedin_post_task = self.llm_client.generate_with_system(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=LINKEDIN_POST_PROMPT.format(
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
            ),
        )

        abstract_rewrite, problem_solved, linkedin_post = await asyncio.gather(
            abstract_rewrite_task,
            problem_solved_task,
            linkedin_post_task,
        )

        return {
            "abstract_rewrite": abstract_rewrite.strip(),
            "problem_solved": problem_solved.strip(),
            "linkedin_post": linkedin_post.strip(),
        }

    async def process_paper(self, paper: Any) -> Dict[str, Any]:
        """
        Process a single paper: generate + reflect + prepare for output.

        Args:
            paper: Paper object (ArxivPaper, OpenAlexPaper, or CVFPaper)

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
                year=paper_dict["year"],
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
        target_papers: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Run the full pipeline.

        Args:
            days_back: Number of days to look back
            max_results: Max results per source (initial batch size)
            target_papers: Target number of NEW papers to process (default: 3)

        Returns:
            List of processed paper results
        """
        logger.info("=" * 80)
        logger.info("Starting Literature Agent Pipeline")
        logger.info("=" * 80)

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
            return []

        # Limit to target number
        new_papers = new_papers[:target_papers]
        logger.info(f"Processing {len(new_papers)} new papers")

        # Step 2: Process each paper (sequential to avoid overwhelming vLLM)
        results = []
        for paper in new_papers:
            try:
                result = await self.process_paper(paper)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Failed to process paper {paper.to_dict()['title']}: {e}")
                continue

        # Step 3: Save ledger
        try:
            self.ledger.save()
            logger.info(f"Ledger saved with {len(results)} new entries")
        except Exception as e:
            logger.error(f"Failed to save ledger: {e}")

        logger.info("=" * 80)
        logger.info(f"Pipeline complete: {len(results)} papers processed")
        logger.info("=" * 80)

        return results
