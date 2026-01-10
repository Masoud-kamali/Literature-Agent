"""Configuration module using Pydantic settings."""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Project paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
    output_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "output")
    ledger_path: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent / "data" / "ledger.csv"
    )

    # vLLM settings (OpenAI-compatible endpoint)
    vllm_base_url: str = Field(
        default="http://localhost:8000/v1",
        description="vLLM OpenAI-compatible API endpoint",
    )
    vllm_api_key: str = Field(
        default="EMPTY",
        description="Dummy API key for local vLLM (not used but required by client)",
    )
    vllm_model_name: str = Field(
        default="meta-llama/Llama-3.1-8B-Instruct",
        description="Model name as configured in vLLM server",
    )
    vllm_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    vllm_max_tokens: int = Field(default=1024, ge=64, le=4096)
    vllm_timeout: int = Field(default=120, description="Timeout in seconds for LLM calls")

    # Data source settings
    arxiv_base_url: str = "https://export.arxiv.org/api/query"
    openalex_base_url: str = "https://api.openalex.org"
    openalex_mailto: str = Field(
        default="researcher@example.edu.au",
        description="Polite pool mailto parameter for OpenAlex",
    )

    # CVF settings
    cvf_base_url: str = "https://openaccess.thecvf.com"
    cvf_years: List[int] = Field(default=[2024, 2023, 2022], description="Years to scrape CVF")
    cvf_venues: List[str] = Field(
        default=["CVPR", "ICCV", "ECCV"], description="CVF venues to monitor"
    )

    # Reddit settings
    reddit_base_url: str = "https://www.reddit.com"
    reddit_subreddits: List[str] = Field(
        default=["PlayCanvas", "GaussianSplatting"],
        description="Subreddits to monitor for tools and discussions",
    )
    reddit_user_agent: str = Field(
        default="Literature-Agent/1.0 (Research paper monitoring)",
        description="User agent for Reddit API",
    )
    reddit_delay: float = Field(default=2.0, description="Delay between Reddit requests (seconds)")

    # Search keywords for 3D Gaussian Splatting
    search_keywords: List[str] = Field(
        default=[
            "gaussian splatting",
            "3DGS",
            "3D Gaussian Splatting",
            "splatting radiance field",
            "neural gaussian",
        ]
    )

    # Retrieval settings
    default_days_back: int = Field(default=7, description="Default lookback period in days")
    max_results_per_source: int = Field(
        default=50, description="Maximum papers to fetch per source"
    )

    # HTTP retry settings
    http_max_retries: int = Field(default=3, description="Maximum HTTP retry attempts")
    http_retry_delay: float = Field(default=2.0, description="Base delay between retries (seconds)")
    http_timeout: int = Field(default=30, description="HTTP request timeout in seconds")

    # Rate limiting
    arxiv_delay: float = Field(default=3.0, description="Delay between arXiv requests (seconds)")
    openalex_delay: float = Field(
        default=0.1, description="Delay between OpenAlex requests (seconds)"
    )
    cvf_delay: float = Field(default=2.0, description="Delay between CVF page requests (seconds)")
    
    # Output format settings
    output_format: str = Field(
        default="2_papers_1_tool",
        description="Format for LinkedIn posts: '2_papers_1_tool' or '3_papers'",
    )

    # LinkedIn settings
    linkedin_dry_run: bool = Field(
        default=True, description="If True, only generate posts without publishing"
    )
    linkedin_post_min_words: int = Field(default=120, description="Minimum words for LinkedIn post")
    linkedin_post_max_words: int = Field(default=180, description="Maximum words for LinkedIn post")

    # Reflection agent settings
    reflection_max_iterations: int = Field(
        default=1, description="Number of reflection cycles (1 = single critique+revision)"
    )
    reflection_temperature: float = Field(default=0.3, description="Temperature for critic agent")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        description="Loguru log format",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
