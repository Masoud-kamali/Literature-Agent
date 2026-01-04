"""LangGraph-based reflection agent for critique and revision."""

import json
import re
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from loguru import logger

from src.config import settings
from src.llm.prompts import (
    CRITIC_PROMPT,
    CRITIC_SYSTEM_PROMPT,
    REVISER_PROMPT,
    SYSTEM_PROMPT,
)
from src.llm.vllm_chat import VLLMChatClient


class ReflectionState(TypedDict):
    """State for reflection graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    title: str
    authors: str
    venue: str
    year: int
    abstract: str
    abstract_rewrite: str
    problem_solved: str
    linkedin_post: str
    critique: str
    revision_actions: list[str]
    iteration: int
    max_iterations: int
    score: float


class ReflectionAgent:
    """
    LangGraph-based reflection agent.

    Flow:
    1. Generate initial outputs (draft)
    2. Critic reviews outputs and provides structured feedback
    3. Reviser applies feedback to produce final outputs
    """

    def __init__(self, llm_client: VLLMChatClient):
        """
        Initialise reflection agent.

        Args:
            llm_client: vLLM chat client instance
        """
        self.llm_client = llm_client
        self.max_iterations = settings.reflection_max_iterations

        # Build LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the reflection state graph."""
        workflow = StateGraph(ReflectionState)

        # Add nodes
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("reviser", self._reviser_node)

        # Entry point
        workflow.set_entry_point("critic")

        # Conditional edges
        workflow.add_conditional_edges(
            "critic",
            self._should_revise,
            {
                "revise": "reviser",
                "accept": END,
            },
        )

        workflow.add_edge("reviser", END)

        return workflow.compile()

    async def _critic_node(self, state: ReflectionState) -> ReflectionState:
        """
        Critic node: review outputs and provide structured feedback.

        Args:
            state: Current reflection state

        Returns:
            Updated state with critique
        """
        logger.info("Reflection: Running critic node")

        user_prompt = CRITIC_PROMPT.format(
            title=state["title"],
            authors=state["authors"],
            year=state["year"],
            abstract=state["abstract"],
            abstract_rewrite=state["abstract_rewrite"],
            problem_solved=state["problem_solved"],
            linkedin_post=state["linkedin_post"],
        )

        # Generate critique
        critique_text = await self.llm_client.generate_with_system(
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=settings.reflection_temperature,
            max_tokens=1024,
        )

        # Parse JSON critique
        try:
            # Extract JSON using regex (handles text before/after JSON)
            json_match = re.search(r'\{[\s\S]*\}', critique_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try removing markdown code blocks
                critique_text = critique_text.strip()
                if critique_text.startswith("```"):
                    lines = critique_text.split("\n")
                    json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else critique_text
                else:
                    json_str = critique_text

            critique_data = json.loads(json_str)

            revision_actions = critique_data.get("revision_actions", [])
            score = critique_data.get("overall_score", 5)

            state["critique"] = json_str
            state["revision_actions"] = revision_actions
            state["score"] = score

            logger.info(f"Critique score: {score}/10, {len(revision_actions)} actions")

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse critique JSON: {e}. Using fallback score.")
            logger.debug(f"Critique response: {critique_text[:200]}...")
            # Fallback: treat as acceptable
            state["critique"] = critique_text
            state["revision_actions"] = []
            state["score"] = 8.0

        return state

    async def _reviser_node(self, state: ReflectionState) -> ReflectionState:
        """
        Reviser node: apply critique to produce revised outputs.

        Args:
            state: Current reflection state

        Returns:
            Updated state with revised outputs
        """
        logger.info("Reflection: Running reviser node")

        user_prompt = REVISER_PROMPT.format(
            title=state["title"],
            authors=state["authors"],
            year=state["year"],
            abstract=state["abstract"],
            abstract_rewrite=state["abstract_rewrite"],
            problem_solved=state["problem_solved"],
            linkedin_post=state["linkedin_post"],
            critique=state["critique"],
            revision_actions="\n".join(f"- {a}" for a in state["revision_actions"]),
        )

        # Generate revised outputs
        revised_text = await self.llm_client.generate_with_system(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=settings.vllm_temperature,
            max_tokens=2048,
        )

        # Parse JSON response
        try:
            # Extract JSON using regex (handles text before/after JSON)
            json_match = re.search(r'\{[\s\S]*\}', revised_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try removing markdown code blocks
                revised_text = revised_text.strip()
                if revised_text.startswith("```"):
                    lines = revised_text.split("\n")
                    json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else revised_text
                else:
                    json_str = revised_text

            revised_data = json.loads(json_str)

            state["abstract_rewrite"] = revised_data.get(
                "abstract_rewrite", state["abstract_rewrite"]
            )
            state["problem_solved"] = revised_data.get(
                "problem_solved", state["problem_solved"]
            )
            state["linkedin_post"] = revised_data.get(
                "linkedin_post", state["linkedin_post"]
            )

            logger.info("Revision complete")

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse revised JSON: {e}. Keeping draft outputs.")
            logger.debug(f"Reviser response: {revised_text[:200]}...")
            # Keep original outputs

        state["iteration"] += 1

        return state

    def _should_revise(self, state: ReflectionState) -> str:
        """
        Decide whether to revise or accept outputs.

        Args:
            state: Current reflection state

        Returns:
            "revise" or "accept"
        """
        score = state.get("score", 8.0)
        iteration = state.get("iteration", 0)
        max_iter = state.get("max_iterations", self.max_iterations)

        # Accept if score is good or we've hit max iterations
        if score >= 8.0 or iteration >= max_iter:
            logger.info(f"Accepting outputs (score={score}, iteration={iteration})")
            return "accept"
        else:
            logger.info(f"Revising outputs (score={score}, iteration={iteration})")
            return "revise"

    async def reflect(
        self,
        title: str,
        authors: str,
        venue: str,
        year: int,
        abstract: str,
        abstract_rewrite: str,
        problem_solved: str,
        linkedin_post: str,
    ) -> tuple[str, str, str]:
        """
        Run reflection process on generated outputs.

        Args:
            title: Paper title
            authors: Paper authors
            venue: Venue name
            year: Publication year
            abstract: Original abstract
            abstract_rewrite: Generated abstract rewrite
            problem_solved: Generated problem statement
            linkedin_post: Generated LinkedIn post

        Returns:
            Tuple of (final_abstract_rewrite, final_problem_solved, final_linkedin_post)
        """
        logger.info(f"Starting reflection for: {title}")

        initial_state = ReflectionState(
            messages=[],
            title=title,
            authors=authors,
            venue=venue,
            year=year,
            abstract=abstract,
            abstract_rewrite=abstract_rewrite,
            problem_solved=problem_solved,
            linkedin_post=linkedin_post,
            critique="",
            revision_actions=[],
            iteration=0,
            max_iterations=self.max_iterations,
            score=0.0,
        )

        # Run graph
        final_state = await self.graph.ainvoke(initial_state)

        return (
            final_state["abstract_rewrite"],
            final_state["problem_solved"],
            final_state["linkedin_post"],
        )
