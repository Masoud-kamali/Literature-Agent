"""LinkedIn publishing stub (dry-run by default)."""

import json
from typing import Dict, List

from loguru import logger

from src.config import settings


class LinkedInPublisher:
    """
    LinkedIn publishing client.

    By default operates in dry-run mode (prints payloads without posting).
    Actual OAuth integration and posting is left as an exercise for the user.
    """

    def __init__(self, dry_run: bool = None):
        """
        Initialise LinkedIn publisher.

        Args:
            dry_run: If True, only generate payloads (defaults to config)
        """
        self.dry_run = dry_run if dry_run is not None else settings.linkedin_dry_run

    def prepare_post_payload(self, paper_result: Dict) -> Dict:
        """
        Prepare LinkedIn post payload from paper result.

        Args:
            paper_result: Paper result dictionary with linkedin_post

        Returns:
            Dictionary suitable for LinkedIn API (in dry-run, this is informational)
        """
        linkedin_post = paper_result.get("linkedin_post", "")

        # Simplified payload structure
        # In production, this would follow LinkedIn API v2 schema
        payload = {
            "author": "urn:li:person:YOUR_PERSON_URN",  # Placeholder
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": linkedin_post},
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {"text": paper_result.get("title", "")},
                            "originalUrl": paper_result.get("url", ""),
                            "title": {"text": paper_result.get("title", "")},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        return payload

    def publish(self, paper_results: List[Dict]) -> List[Dict]:
        """
        Publish LinkedIn posts for papers (dry-run by default).

        Args:
            paper_results: List of paper result dictionaries

        Returns:
            List of publish results (in dry-run, these are just the payloads)
        """
        if not paper_results:
            logger.info("No papers to publish")
            return []

        results = []

        for paper in paper_results:
            payload = self.prepare_post_payload(paper)

            if self.dry_run:
                logger.info("=" * 80)
                logger.info(f"[DRY-RUN] LinkedIn post for: {paper['title']}")
                logger.info("=" * 80)
                logger.info("\nPost content:")
                logger.info("-" * 80)
                print(paper["linkedin_post"])
                logger.info("-" * 80)
                logger.info("\nAPI Payload (for reference):")
                print(json.dumps(payload, indent=2))
                logger.info("=" * 80)

                results.append({"status": "dry-run", "paper_id": paper["canonical_id"]})
            else:
                # Actual posting would go here
                # Example (pseudo-code):
                # response = requests.post(
                #     "https://api.linkedin.com/v2/ugcPosts",
                #     headers={"Authorization": f"Bearer {access_token}"},
                #     json=payload
                # )
                logger.warning(
                    "Actual LinkedIn posting not implemented. "
                    "Please implement OAuth flow and API integration."
                )
                results.append({"status": "not-implemented", "paper_id": paper["canonical_id"]})

        return results

    def print_instructions(self):
        """Print instructions for manual LinkedIn posting."""
        logger.info("\n" + "=" * 80)
        logger.info("LinkedIn Publishing Instructions")
        logger.info("=" * 80)
        logger.info(
            """
To enable actual LinkedIn posting, you need to:

1. Create a LinkedIn App at: https://www.linkedin.com/developers/apps
2. Configure OAuth 2.0 redirect URLs
3. Request the following permissions:
   - w_member_social (to post on behalf of member)
   - r_liteprofile (to read profile info)
4. Implement OAuth 2.0 flow to get access token
5. Use LinkedIn API v2 to post:
   - Endpoint: POST https://api.linkedin.com/v2/ugcPosts
   - See: https://docs.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api

Example OAuth flow (simplified):
1. Redirect user to LinkedIn authorization URL
2. User grants permission
3. LinkedIn redirects back with authorization code
4. Exchange code for access token
5. Use access token in API requests

For detailed implementation, see LinkedIn's official documentation.

The payloads above show the structure you'll need to POST to the API.
"""
        )
        logger.info("=" * 80 + "\n")
