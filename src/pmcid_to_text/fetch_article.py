"""
PMCID --> Full Article Text (HTML)
This uses a standard get request with a user agent and accept header to fetch the article text.
"""
import os
import argparse
import requests
from loguru import logger
import time
from typing import List, Optional
import tqdm

def get_html_from_pmcid(pmcid: str) -> Optional[str]:
    """
    Given a PMCID, fetch the full article text from the NCBI website.
    Returns the HTML text of the article in string format from the url
    https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/?report=classic
    
    Args:
        pmcid (str): The PMCID to fetch
        
    Returns:
        Optional[str]: The article html text if successful, None if there was an error
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/?report=classic"
    logger.info(f"Fetching article from {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an exception for 4XX/5XX status codes
        return response.text
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred for PMCID {pmcid}: {str(e)}")
        if response.text:
            logger.error(f"Server response: {response.text}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error occurred for PMCID {pmcid}: {str(e)}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timed out for PMCID {pmcid}: {str(e)}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while fetching PMCID {pmcid}: {str(e)}")
        return None

def save_html(pmcid: str, text: str, save_path: str = "data/raw_html") -> None:
    """
    Save the HTML text of the article to a file
    
    Args:
        pmcid (str): The PMCID of the article
        text (str): The article text to save
        save_path (str): The path to save the article to
    """
    os.makedirs(save_path, exist_ok=True)
    with open(f"{save_path}/{pmcid}.html", "w") as f:
        f.write(text)
    logger.info(f"Article saved to {save_path}/{pmcid}.html")

def save_batch_html_from_pmcids(pmcids: List[str], save_path: str = "data/raw_html", delay: float = 0.4) -> None:
    """
    Get the article text from the NCBI website for a batch of PMCIDs
    
    Args:
        pmcids (List[str]): List of PMCIDs to fetch
        save_path (str): The path to save the articles to
        delay (float): Delay between requests in seconds
    """
    for pmcid in tqdm.tqdm(pmcids):
        text = get_html_from_pmcid(pmcid)
        if text is not None:
            save_html(pmcid, text, save_path)
        time.sleep(delay)
    logger.info(f"All articles saved to {save_path}")

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Fetch and save article text from NCBI")
    parser.add_argument("--pmcid", type=str, help="PMCID of the article to fetch")
    parser.add_argument("--save_path", default="data/articles", type=str, help="Path to save the article text")
    args = parser.parse_args()

    if not args.pmcid:
        parser.error("--pmcid is required")

    text = get_html_from_pmcid(args.pmcid)
    if text is not None:
        save_html(args.pmcid, text, args.save_path)

if __name__ == "__main__":
    main()
