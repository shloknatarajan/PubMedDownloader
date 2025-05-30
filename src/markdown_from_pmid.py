from typing import List, Optional
from loguru import logger
import pandas as pd
import os
from .pmcid_from_pmid import batch_pmcid_from_pmid
from .html_from_pmcid import get_html_from_pmcid
from .markdown_from_html import PubMedHTMLToMarkdownConverter
import argparse
import tqdm
import time
from .manage_records import get_scraped_pmids

def save_file(file_path: str, content: str):
    """
    Save the content to the file_path
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)


def get_markdown_from_pmid(
    pmid: str, save_dir: Optional[str] = "data"
) -> Optional[str]:
    """
    Get the article from the PMID
    High level conversion steps
    1. PMID --> PMCID
    2. PMCID --> Raw HTML
    3. Raw HTML --> Parsed Markdown
    4. Save markdown and raw HTML

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
    converter = PubMedHTMLToMarkdownConverter()
    markdown = converter.convert_html(raw_html)

    if markdown is None:
        logger.error(f"No Markdown found for PMCID {pmcid}")
        return None

    if save_dir is not None:
        # Save raw html to data/raw_html
        save_file(f"{save_dir}/raw_html/{pmcid}.html", raw_html)

        # Save markdown to data/articles
        save_file(f"{save_dir}/articles/{pmcid}.md", markdown)

    return markdown


def save_batch_markdown_from_pmids(
    pmids: List[str], save_dir: Optional[str] = "data", delay: float = 0.4
) -> List[str]:
    """
    Process a batch of PMIDs to get their markdown content.
    
    Args:
        pmids (List[str]): List of PMIDs to process
        save_dir (Optional[str]): Directory to save the articles to (default: "data")
        delay (float): Delay between requests in seconds (default: 0.4)
        
    Returns:
        List[str]: List of PMIDs that were skipped due to errors
    """
    # Get the list of PMIDs that have already been scraped
    scraped_pmids = set(get_scraped_pmids(update=False))
    skipped_pmids = []
    for pmid in tqdm.tqdm(pmids, desc="Processing PMIDs"):
        if pmid in scraped_pmids:
            logger.warning(f"Skipping PMID {pmid}, found in record_map")
            skipped_pmids.append(pmid)
            continue
        try:
            markdown = get_markdown_from_pmid(pmid, save_dir)
            if markdown is None:
                logger.warning(f"Failed to process PMID {pmid}")
                skipped_pmids.append(pmid)
            time.sleep(delay)  # Add delay between requests
        except Exception as e:
            logger.error(f"Error processing PMID {pmid}: {str(e)}")
            skipped_pmids.append(pmid)
            time.sleep(delay)  # Still add delay even after errors

    if skipped_pmids:
        logger.warning(f"Skipped {len(skipped_pmids)} PMIDs")
    logger.info("Finished processing PMIDs")
        
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
