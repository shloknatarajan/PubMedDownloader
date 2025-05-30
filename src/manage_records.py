"""
Goal: Keep a record of the PMIDs that have been converted to pmcid, html, and markdown
Store the record in a json file (data/record_map.json)
"""

import os
from typing import List
import re
from loguru import logger
import pandas as pd

def get_scraped_pmids(update: bool = False) -> List[str]:
    """
    Get a list of all the PMIDs in the record_map.csv file
    
    Args:
        update (bool): If True, create a new record_map.csv file
    Returns:
        List[str]: A list of all the PMIDs in the record_map.csv file
    """
    if update:
        record_map = create_record_map()
    else:
        record_map = pd.read_csv(os.path.join("data", "record_map.csv"))
    pmid_list = record_map['PMID'].tolist()
    return pmid_list

def parse_markdown_metadata(markdown_text: str)-> dict:
    """
    Extract PMID, PMCID, and URL from a markdown text.
    
    Args:
        markdown_text (str): The markdown text to parse
    
    Returns:
        dict: A dictionary containing extracted metadata
    """
    # Dictionary to store extracted metadata
    metadata = {}
    
    # Regular expressions for extraction
    pmcid_pattern = r'\*\*PMCID:\*\*\s*([^\n]+)'
    pmid_pattern = r'\*\*PMID:\*\*\s*([^\n]+)'
    url_pattern = r'\*\*URL:\*\*\s*([^\n]+)'
    
    # Extract PMCID
    pmcid_match = re.search(pmcid_pattern, markdown_text)
    if pmcid_match:
        metadata['PMCID'] = pmcid_match.group(1).strip()
    
    # Extract PMID
    pmid_match = re.search(pmid_pattern, markdown_text)
    if pmid_match:
        metadata['PMID'] = pmid_match.group(1).strip()
    
    # Extract URL
    url_match = re.search(url_pattern, markdown_text)
    if url_match:
        metadata['URL'] = url_match.group(1).strip()
    
    return metadata
    
def validate_record_map(record_map: pd.DataFrame) -> pd.DataFrame:
    """
    Check if any of the records in the record_map are missing required fields.
    
    Args:
        record_map (pd.DataFrame): DataFrame containing the record map
        
    Returns:
        pd.DataFrame: DataFrame containing only the records with missing fields
    """
    # Check for missing values in required columns
    missing_mask = record_map[['PMID', 'PMCID', 'URL']].isna().any(axis=1)
    missing_records = record_map[missing_mask]
    
    if not missing_records.empty:
        logger.warning(f"Found {len(missing_records)} records with missing fields")
        for _, row in missing_records.iterrows():
            missing_fields = [col for col in ['PMID', 'PMCID', 'URL'] if pd.isna(row[col])]
            logger.warning(f"Record {row['markdown_path']} is missing: {', '.join(missing_fields)}")
    
    return missing_records

def create_record_map() -> pd.DataFrame:
    """
    Get a list of all the markdown files in the data/articles directory
    Extract PMID, PMCID, and URL to create a csv table:
    PMID,PMCID,URL,markdown_path
    
    Returns:
        pd.DataFrame: DataFrame containing the record map
    """
    records = []
    markdown_path = os.path.join("data", "markdown")
    
    for file in os.listdir(markdown_path):
        if file.endswith(".md"):
            row = {
                "PMID": None,
                "PMCID": None,
                "markdown_path": f"{markdown_path}/{file}",
                "URL": None,
            }
            metadata = parse_markdown_metadata(open(f"{markdown_path}/{file}", "r").read())
            if metadata['PMID'] is not None:
                row['PMID'] = metadata['PMID']
            if metadata['PMCID'] is not None:
                row['PMCID'] = metadata['PMCID']
            if metadata['URL'] is not None:
                row['URL'] = metadata['URL']
            records.append(row)

    # Create DataFrame from list of records
    record_map = pd.DataFrame(records)

    missing_records = validate_record_map(record_map)
    if len(missing_records) > 0:
        logger.warning(f"Missing records: {missing_records}")
    logger.info("Finished processing records")

    # Save record map to a CSV
    record_map_path = os.path.join("data", "record_map.csv")
    record_map.to_csv(record_map_path, index=False)
    
    logger.info(f"Record map saved to {record_map_path}")
    return record_map

if __name__ == "__main__":
    create_record_map()

