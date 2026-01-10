#!/usr/bin/env python3
"""Clear the ledger to test with new prompts (keeps header, removes all entries)."""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def main():
    """Clear the ledger file."""
    ledger_path = Path(__file__).parent.parent / "data" / "ledger.csv"
    
    # Backup first
    backup_path = ledger_path.parent / f"ledger_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if ledger_path.exists():
        # Read current content
        with open(ledger_path, 'r') as f:
            lines = f.readlines()
        
        # Save backup
        with open(backup_path, 'w') as f:
            f.writelines(lines)
        
        logger.info(f"Backed up ledger to: {backup_path}")
        
        # Keep only header
        header = lines[0] if lines else "canonical_id,source,arxiv_id,doi,title,authors,venue,year,url,discovered_date,processed_date,model_name,abstract_rewrite,problem_solved,linkedin_post\n"
        
        with open(ledger_path, 'w') as f:
            f.write(header)
        
        logger.info(f"Cleared ledger (kept header only)")
        logger.info(f"Removed {len(lines) - 1} entries")
    else:
        logger.warning("Ledger file does not exist")


if __name__ == "__main__":
    main()

