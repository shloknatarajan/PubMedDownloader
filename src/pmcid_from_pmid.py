import requests
from typing import List, Dict, Optional, Union
import os
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from tqdm import tqdm
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def _get_cache_file_path() -> Path:
    """Get the cache file path from environment or default."""
    cache_dir = os.getenv("PMID_CACHE_DIR", "data/cache")
    cache_file = os.getenv("PMID_CACHE_FILE", "pmid_to_pmcid.json")
    cache_path = Path(cache_dir) / cache_file
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    return cache_path


def _load_cache() -> Dict[str, Dict]:
    """Load existing cache from file."""
    cache_path = _get_cache_file_path()
    if not cache_path.exists():
        return {}
    
    try:
        with open(cache_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load cache file {cache_path}: {e}")
        return {}


def _save_cache(cache: Dict[str, Dict]) -> None:
    """Save cache to file."""
    cache_path = _get_cache_file_path()
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=2)
    except IOError as e:
        logger.error(f"Failed to save cache to {cache_path}: {e}")


def _is_cache_entry_valid(entry: Dict, expiry_days: int = 30) -> bool:
    """Check if a cache entry is still valid."""
    if 'timestamp' not in entry:
        return False
    
    try:
        cached_time = datetime.fromisoformat(entry['timestamp'])
        expiry_time = cached_time + timedelta(days=expiry_days)
        return datetime.now() < expiry_time
    except (ValueError, KeyError):
        return False


def get_pmcid_from_pmid(
    pmids: Union[List[str], str],
    email: str = os.getenv("NCBI_EMAIL"),
    batch_size: int = 100,
    delay: float = 0.4,
    use_cache: bool = True,
    cache_expiry_days: int = 30,
) -> Dict[str, Optional[str]]:
    """
    Convert a list of PMIDs to PMCIDs using NCBI's ID Converter API.

    Args:
        pmids: List of PMIDs (as strings) or a single PMID (as a string).
        email: Your email address for NCBI tool identification.
        batch_size: Number of PMIDs to send per request (max: 200).
        delay: Seconds to wait between requests (default 0.4 to respect NCBI).
        use_cache: Whether to use cached results (default: True).
        cache_expiry_days: Days after which cache entries expire (default: 30).

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

    # Load cache and filter out already cached PMIDs
    cache = _load_cache() if use_cache else {}
    cached_count = 0
    pmids_to_fetch = []
    
    for pmid in pmids:
        if use_cache and pmid in cache and _is_cache_entry_valid(cache[pmid], cache_expiry_days):
            results[pmid] = cache[pmid].get('pmcid')
            cached_count += 1
        else:
            pmids_to_fetch.append(pmid)
    
    if cached_count > 0:
        logger.info(f"Found {cached_count} cached PMIDs, fetching {len(pmids_to_fetch)} from API")
    
    if not pmids_to_fetch:
        logger.info("All PMIDs found in cache")
        return results

    # Process remaining PMIDs
    logger.info(f"Starting conversion of {len(pmids_to_fetch)} PMIDs to PMCIDs")
    for i in tqdm(range(0, len(pmids_to_fetch), batch_size), desc="Converting PMIDs to PMCIDs", unit="batch"):
        batch = pmids_to_fetch[i : i + batch_size]
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
            
            # Update cache with new results
            timestamp = datetime.now().isoformat()
            for record in records:
                pmid = record.get("pmid")
                pmcid = record.get("pmcid")
                results[pmid] = pmcid if pmcid else None
                if not pmcid:
                    logger.warning(f"PMID {pmid} has no PMCID available.")
                
                # Cache the result
                if use_cache:
                    cache[pmid] = {
                        'pmcid': pmcid,
                        'timestamp': timestamp
                    }
            
            # Handle PMIDs not found in response
            for pmid in batch:
                if pmid not in [r.get("pmid") for r in records]:
                    results[pmid] = None
                    if use_cache:
                        cache[pmid] = {
                            'pmcid': None,
                            'timestamp': timestamp
                        }
                        
        except Exception as e:
            logger.error(f"Failed batch starting at index {i}: {e}")
            timestamp = datetime.now().isoformat()
            for pmid in batch:
                results[pmid] = None
                # Cache failed lookups to avoid repeated API calls
                if use_cache:
                    cache[pmid] = {
                        'pmcid': None,
                        'timestamp': timestamp
                    }

        time.sleep(delay)
    
    # Save updated cache
    if use_cache and pmids_to_fetch:
        _save_cache(cache)
        
    logger.info(f"Processed {len(pmids)} PMIDs ({cached_count} from cache, {len(pmids_to_fetch)} from API)")
    return results
