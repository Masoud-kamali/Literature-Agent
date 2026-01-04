"""Mock end-to-end test with sample papers."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.pipeline import LiteraturePipeline
from src.clients.arxiv_client import ArxivPaper
from src.dedupe.ledger import PaperLedger
from src.llm.vllm_chat import VLLMChatClient


@pytest.fixture
def mock_papers():
    """Create mock sample papers."""
    paper1 = ArxivPaper(
        arxiv_id="2401.12345",
        title="3D Gaussian Splatting for Real-Time Rendering",
        authors=["Alice Smith", "Bob Johnson"],
        abstract="We present a novel approach to real-time rendering using 3D Gaussian primitives. Our method achieves state-of-the-art quality while maintaining interactive frame rates.",
        published=datetime(2024, 1, 15),
        updated=datetime(2024, 1, 15),
        primary_category="cs.CV",
        pdf_url="https://arxiv.org/pdf/2401.12345.pdf",
        categories=["cs.CV", "cs.GR"],
    )

    paper2 = ArxivPaper(
        arxiv_id="2401.54321",
        title="Dynamic 3D Gaussian Splatting for Video Reconstruction",
        authors=["Charlie Davis"],
        abstract="This work extends 3D Gaussian Splatting to dynamic scenes, enabling high-quality video reconstruction from multi-view inputs.",
        published=datetime(2024, 1, 20),
        updated=datetime(2024, 1, 20),
        primary_category="cs.CV",
        pdf_url="https://arxiv.org/pdf/2401.54321.pdf",
        categories=["cs.CV"],
    )

    return [paper1, paper2]


@pytest.fixture
def mock_llm_responses():
    """Mock LLM responses."""
    return {
        "abstract_rewrite": "This paper introduces a groundbreaking technique for real-time 3D scene rendering utilising Gaussian splatting primitives. The approach demonstrates superior visual fidelity compared to existing methods whilst maintaining interactive performance suitable for practical applications.",
        "problem_solved": "Traditional real-time rendering techniques struggle to balance visual quality with computational efficiency. This work addresses this limitation by leveraging 3D Gaussian primitives, which provide a more efficient representation for high-quality scene reconstruction.",
        "linkedin_post": "🚀 New Research Alert: 3D Gaussian Splatting for Real-Time Rendering (arXiv 2024)\n\nResearchers have developed a novel approach that achieves photorealistic 3D rendering at interactive frame rates. By using 3D Gaussian primitives, this method outperforms traditional techniques in both quality and speed.\n\nWhy it matters: This breakthrough could revolutionise applications in VR/AR, gaming, and digital twins by making high-fidelity 3D rendering accessible in real-time scenarios.\n\n#ComputerVision #3DGraphics #MachineLearning",
        "critique": '{"abstract_rewrite_issues": [], "problem_solved_issues": [], "linkedin_post_issues": [], "revision_actions": [], "overall_score": 9}',
    }


@pytest.mark.asyncio
async def test_mock_pipeline_run(tmp_path, mock_papers, mock_llm_responses):
    """Test full pipeline with mocked components."""

    # Create temp ledger
    ledger_path = tmp_path / "test_ledger.csv"
    ledger = PaperLedger(ledger_path=ledger_path)

    # Mock LLM client
    mock_llm = AsyncMock(spec=VLLMChatClient)
    mock_llm.model_name = "test-model"

    # Setup mock responses
    async def mock_generate(*args, **kwargs):
        # Return different responses based on prompt content
        user_prompt = kwargs.get("user_prompt", "")
        if "abstract rewrite" in user_prompt.lower():
            return mock_llm_responses["abstract_rewrite"]
        elif "problem" in user_prompt.lower():
            return mock_llm_responses["problem_solved"]
        elif "linkedin" in user_prompt.lower():
            return mock_llm_responses["linkedin_post"]
        elif "critique" in user_prompt.lower():
            return mock_llm_responses["critique"]
        else:
            return "Mock response"

    mock_llm.generate_with_system = mock_generate

    # Create pipeline with mocks
    pipeline = LiteraturePipeline(llm_client=mock_llm, ledger=ledger)

    # Mock the retrieval methods
    pipeline.arxiv_client.search_papers = AsyncMock(return_value=mock_papers)
    pipeline.openalex_client.search_papers = AsyncMock(return_value=[])
    pipeline.cvf_client.search_papers = AsyncMock(return_value=[])

    # Run pipeline
    results = await pipeline.run(days_back=7, max_results=10)

    # Assertions
    assert len(results) == 2
    assert results[0]["title"] == "3D Gaussian Splatting for Real-Time Rendering"
    assert results[0]["source"] == "arxiv"
    assert "abstract_rewrite" in results[0]
    assert "problem_solved" in results[0]
    assert "linkedin_post" in results[0]

    # Check ledger was updated
    assert len(ledger.processed_ids) == 2
    assert ledger.is_processed("2401.12345")
    assert ledger.is_processed("2401.54321")


@pytest.mark.asyncio
async def test_deduplication(tmp_path, mock_papers):
    """Test that duplicate papers are skipped."""

    ledger_path = tmp_path / "test_ledger.csv"
    ledger = PaperLedger(ledger_path=ledger_path)

    # Pre-add first paper to ledger
    paper_dict = mock_papers[0].to_dict()
    ledger.add_entry(
        paper_dict=paper_dict,
        model_name="test",
        abstract_rewrite="Previous",
        problem_solved="Previous",
        linkedin_post="Previous",
    )
    ledger.save()

    # Create new pipeline instance (will load existing ledger)
    mock_llm = AsyncMock(spec=VLLMChatClient)
    mock_llm.model_name = "test-model"

    pipeline = LiteraturePipeline(llm_client=mock_llm, ledger=PaperLedger(ledger_path=ledger_path))

    # Filter papers
    new_papers = pipeline.filter_new_papers(mock_papers)

    # Only second paper should be new
    assert len(new_papers) == 1
    assert new_papers[0].arxiv_id == "2401.54321"
