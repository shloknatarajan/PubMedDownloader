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
from .pmcid_from_pmid import batch_pmcid_from_pmid
from .html_from_pmcid import get_html_from_pmcid
from .markdown_from_html import html_to_markdown
import argparse
import tqdm


def save_file(file_path: str, content: str):
    """
    Save the content to the file_path
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)


def get_markdown_from_pmid(pmid: str, save_dir: Optional[str] = "data") -> Optional[str]:
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
    pmcid_mapping = batch_pmcid_from_pmid(pmid)
    pmcid = pmcid_mapping.get(pmid)

    if pmcid is None:
        logger.warning(f"No PMCID found for PMID {pmid}. Skipping...")
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

    if markdown is None:
        logger.error(f"No Markdown found for PMCID {pmcid}")
        return None

    if save_dir is not None:
        # Save raw html to data/raw_html
        save_file(f"{save_dir}/raw_html/{pmcid}.html", raw_html)

        # Save markdown to data/articles
        save_file(f"{save_dir}/articles/{pmcid}.md", markdown)

    return markdown


def save_batch_markdown_from_pmid(
    pmids: List[str], save_dir: Optional[str] = "data"
) -> List[str]:
    """
    Get the article from the PMID
    """
    skipped_pmids = []
    for pmid in tqdm.tqdm(pmids):
        markdown = get_markdown_from_pmid(pmid, save_dir)
        if markdown is None:
            skipped_pmids.append(pmid)

    return skipped_pmids


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and save article text from PMID"
    )
    parser.add_argument("--pmid", type=str, help="PMID of the article to fetch")
    parser.add_argument("--save_dir", type=str, help="Directory to save the article to")
    args = parser.parse_args()

    if not args.pmid:
        parser.error("--pmid is required")

    markdown = get_markdown_from_pmid(args.pmid, args.save_dir)
    print(markdown)
