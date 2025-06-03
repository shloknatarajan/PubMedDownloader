from typing import List, Optional, Union, Dict
from loguru import logger
import pandas as pd
import os
from .pmcid_from_pmid import get_pmcid_from_pmid
from .html_from_pmcid import get_html_from_pmcid
from .markdown_from_html import PubMedHTMLToMarkdownConverter
import argparse
import tqdm
import time
from .manage_records import get_scraped_pmcids

def save_file(file_path: str, content: str):
    """
    Save the content to the file_path
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)

def get_markdown_from_pmcid(pmcid: str) -> Optional[str]:
    """
    Convert a single PMCID to Markdown
    """
    converter = PubMedHTMLToMarkdownConverter()
    return converter.convert_html(pmcid)

def process_single_pmcid(pmcid: str, save_dir: Optional[str] = "data") -> Optional[str]:
    """
    Process a single PMCID to get its markdown content.
    
    Args:
        pmcid (str): The PMCID to process
        save_dir (Optional[str]): Directory to save the files to (default: "data")
        
    Returns:
        Optional[str]: The markdown content if successful, None if any step fails
    """
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


def get_markdown_from_pmid(
    pmids: Union[str, List[str]], 
    save_dir: Optional[str] = "data",
    delay: float = 0.4
) -> Union[Optional[str], Dict[str, Optional[str]]]:
    """
    Get the article(s) from the PMID(s)
    High level conversion steps
    1. PMID --> PMCID
    2. PMCID --> Raw HTML
    3. Raw HTML --> Parsed Markdown
    4. Save markdown and raw HTML

    Args:
        pmid (Union[str, List[str]]): A single PMID string or a list of PMIDs to fetch
        save_dir (str): The directory to save the files to (default: "data")
        delay (float): Delay between requests in seconds (default: 0.4)
    Returns:
        Union[Optional[str], Dict[str, Optional[str]]]: 
            - If input is a single PMID: Returns the Markdown content if successful, None if any step fails
            - If input is a list of PMIDs: Returns a dictionary mapping PMIDs to their Markdown contents
    """
    total_pmids = len(pmids)
    logger.info(f"Starting processing of {total_pmids} PMIDs")

    # Convert PMIDs to PMCIDs
    pmcid_mapping = get_pmcid_from_pmid(pmids)
    pmcids = [pmcid_mapping.get(pmid) for pmid in pmids]

    # Handle multiple PMIDs sequentially
    results: Dict[str, Optional[str]] = {}
    successful = 0
    failed = 0
    skipped = 0
    scraped_pmcids = set(get_scraped_pmcids(update=False))

    # Convert PMCIDS to HTML
    html_mapping = get_html_from_pmcid(pmcids)
    for i, pmcid in tqdm.tqdm(enumerate(pmcids, 1)):
        if pmcid is None:
            logger.warning(f"No PMCID found for PMID {pmids[i]}")
            continue
        if pmcid in scraped_pmcids:
            skipped += 1
            logger.warning(f"Skipping PMCID {pmcid}, found in record_map")
            continue
        result = process_single_pmcid(pmcid, save_dir)
        results[pmcid] = result
        
        if result is not None:
            successful += 1
        else:
            failed += 1
        
        # Log progress
        logger.info(f"Processed {i}/{total_pmids} PMIDs (Success: {successful}, Failed: {failed})")
        
        # Add delay between requests if not the last item
        if i < total_pmids:
            time.sleep(delay)

    # Log final summary
    logger.info(f"Processing completed. Total: {total_pmids}, Success: {successful}, Failed: {failed}")
    return results



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
