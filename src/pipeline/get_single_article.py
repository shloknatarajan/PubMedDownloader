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
from src.convert import batch_pmid_to_pmcid, html_to_markdown, save_markdown
from src.pmcid_to_text.fetch_article import get_html_from_pmcid, save_html
import argparse

def save_file(file_path: str, content: str):
    """
    Save the content to the file_path
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)

def get_article(pmid: str, save_dir: Optional[str] = "data") -> Optional[str]:
    """
    Get the article from the PMID
    1. Convert PMID to PMCID
    2. Get HTML content
    3. Convert HTML to Markdown
    4. Return the Markdown content
        
    Args:
        pmid (str): The PMID to fetch
        save_dir (str): The directory to save the files to (default: "data")
    Returns:
        Optional[str]: The Markdown content if successful, None if any step fails
    """
    # Convert PMID to PMCID
    pmcid_mapping = batch_pmid_to_pmcid(pmid)
    pmcid = pmcid_mapping.get(pmid)
    
    if pmcid is None:
        logger.error(f"No PMCID found for PMID {pmid}")
        return None
    
    logger.info(f"PMCID found for PMID {pmid}: {pmcid}")
    
    # Get HTML content
    raw_html = get_html_from_pmcid(pmcid)
    if raw_html is None:
        logger.error(f"No HTML found for PMCID {pmcid}")
        return None
    
    logger.info(f"HTML found for PMCID {pmcid}")

    # Convert HTML to Markdown
    markdown = html_to_markdown(raw_html)

    if save_dir is not None:
        # Save raw html to data/raw_html
        save_file(f"{save_dir}/raw_html/{pmcid}.html", raw_html)

        # Save markdown to data/articles
        save_file(f"{save_dir}/articles/{pmcid}.md", markdown)

    return markdown


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and save article text from PMID")
    parser.add_argument("--pmid", type=str, help="PMID of the article to fetch")
    args = parser.parse_args()

    if not args.pmid:
        parser.error("--pmid is required")

    html = get_article(args.pmid)
    print(html)