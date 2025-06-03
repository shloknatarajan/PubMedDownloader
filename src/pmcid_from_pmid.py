import requests
from typing import List, Dict, Optional, Union
import os
import time
from tqdm import tqdm
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def get_pmcid_from_pmid(
    pmids: Union[List[str], str],
    email: str = os.getenv("NCBI_EMAIL"),
    batch_size: int = 100,
    delay: float = 0.4,
) -> Dict[str, Optional[str]]:
    """
    Convert a list of PMIDs to PMCIDs using NCBI's ID Converter API.

    Args:
        pmids: List of PMIDs (as strings) or a single PMID (as a string).
        email: Your email address for NCBI tool identification.
        batch_size: Number of PMIDs to send per request (max: 200).
        delay: Seconds to wait between requests (default 0.4 to respect NCBI).

    Returns:
        Dict mapping each PMID to a PMCID (or None if not available).
    """
    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    results = {}

    if email is None or email == "":
        logger.warning(
            "No email provided. Please set the NCBI_EMAIL environment variable."
        )

    if isinstance(pmids, str):
        pmids = [pmids]
    else:
        pmids = [str(pmid) for pmid in pmids]

    # Process remaining PMIDs
    logger.info(f"Starting conversion of {len(pmids)} PMIDs to PMCIDs")
    for i in tqdm(range(0, len(pmids), batch_size), desc="Converting PMIDs to PMCIDs", unit="batch"):
        batch = pmids[i : i + batch_size]
        batch_str = [str(pmid) for pmid in batch]
        ids_str = ",".join(batch_str)

        params = {
            "tool": "pmid2pmcid_tool",
            "email": email,
            "ids": ids_str,
            "format": "json",
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            records = data.get("records", [])
            for record in records:
                pmid = record.get("pmid")
                pmcid = record.get("pmcid")
                results[pmid] = pmcid if pmcid else None
                if not pmcid:
                    logger.warning(f"PMID {pmid} has no PMCID available.")
        except Exception as e:
            logger.error(f"Failed batch starting at index {i}: {e}")
            for pmid in batch:
                results[pmid] = None

        time.sleep(delay)
    logger.info(f"Processed {len(pmids)} PMIDs")
    return results
