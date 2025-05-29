"""
1. PMID
2. PMCID
3. Raw HTML
4. Parsed XML
"""
from typing import List, Optional
from loguru import logger
import pandas as pd
import os
from src.pmid_to_pmcid.converter import batch_pmid_to_pmcid
from src.pmcid_to_text.fetch_article import get_html_from_pmcid, save_html
import argparse

def get_article(pmid: str) -> Optional[str]:
    """
    Get the article from the PMID
    1. Convert PMID to PMCID
    2. Get HTML content
    3. Return the PMID, PMCID, and HTML save path
    
    Args:
        pmid (str): The PMID to fetch
        
    Returns:
        Optional[str]: The PMID, PMCID, and HTML save path if successful, None if any step fails
    """
    # Convert PMID to PMCID
    pmcid_mapping = batch_pmid_to_pmcid(pmid)
    pmcid = pmcid_mapping.get(pmid)
    
    if pmcid is None:
        logger.error(f"No PMCID found for PMID {pmid}")
        return None
    
    logger.info(f"PMCID found for PMID {pmid}: {pmcid}")
    
    # Get HTML content
    html = get_html_from_pmcid(pmcid)
    if html is None:
        logger.error(f"No HTML found for PMCID {pmcid}")
        return None
    
    logger.info(f"HTML found for PMCID {pmcid}")

    # Save the HTML content
    html_save_path = "data/raw_html"
    save_html(pmcid, html, html_save_path)
    return pmid, pmcid, html_save_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and save article text from PMID")
    parser.add_argument("--pmid", type=str, help="PMID of the article to fetch")
    args = parser.parse_args()

    if not args.pmid:
        parser.error("--pmid is required")

    html = get_article(args.pmid)
    print(html)