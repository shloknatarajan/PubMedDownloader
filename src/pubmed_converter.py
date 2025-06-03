from .pmcid_from_pmid import get_pmcid_from_pmid
from .html_from_pmcid import get_html_from_pmcid
from .markdown_from_html import PubMedHTMLToMarkdownConverter
from typing import List, Optional
import os
from loguru import logger
from tqdm import tqdm

class PubMedToMarkdownConverter:
    """
    Args:
        save_dir (str): Directory to save the files to (default: "data/")
    """
    def __init__(self, save_dir: str = "data"):
        self.html_to_markdown = PubMedHTMLToMarkdownConverter()
        self.save_dir = save_dir
        
    def single_pmid_to_markdown(self, pmid: str) -> Optional[str]:
        """
        Convert a single PMID to markdown.
        
        Args:
            pmid (str): The PMID to convert
            
        Returns:
            Optional[str]: The markdown content if successful, None if any step fails
        """
        # Get PMCID
        pmcid_mapping = get_pmcid_from_pmid([pmid])
        pmcid = pmcid_mapping.get(pmid)
        
        if pmcid is None:
            logger.warning(f"No PMCID found for PMID {pmid}")
            return None
            
        # Get HTML
        html = get_html_from_pmcid(pmcid)
        if html is None:
            logger.error(f"No HTML found for PMCID {pmcid}")
            return None
            
        # Convert to markdown
        try:
            markdown = self.html_to_markdown.convert_html(html)
            return markdown
        except Exception as e:
            logger.error(f"Error converting HTML to markdown for PMID {pmid}: {str(e)}")
            return None
    
    def check_existing_html(self, pmids: List[str], save_dir: str = "data/") -> List[str]:
        """
        Check if the html files exist in the save_dir/html directory
        """
        html_dir = os.path.join(save_dir, "html")
        existing_html = []
        for pmid in pmids:
            html_file = os.path.join(html_dir, f"{pmid}.html")
            if os.path.exists(html_file):
                existing_html.append(pmid)
        return existing_html
    
    def check_existing_markdown(self, pmids: List[str], save_dir: str = "data/") -> List[str]:
        """
        Check if the markdown files exist in the save_dir/markdown directory
        """
        markdown_dir = os.path.join(save_dir, "markdown")
        existing_markdown = []
        for pmid in pmids:
            markdown_file = os.path.join(markdown_dir, f"{pmid}.md")
            if os.path.exists(markdown_file):
                existing_markdown.append(pmid)
        return existing_markdown
    
    def local_html_to_markdown(self, save_dir: str = "data/") -> None:
        """
        Convert all html files in the save_dir/raw_html directory to markdown
        """
        htmls = os.listdir(os.path.join(save_dir, "raw_html"))
        html_paths = [os.path.join(save_dir, "raw_html", f) for f in htmls]
        for html_path in tqdm(html_paths, desc=f"Converting html ({save_dir}/raw_html) to markdown"):
            markdown = self.converter.convert_file(html_path)
            with open(os.path.join(save_dir, "markdown", f"{html_path.split('/')[-1].replace('.html', '.md')}" ), "w") as f:
                f.write(markdown)
    
    def pmids_to_html(self, pmids: List[str], save_dir: str = "data") -> None:
        """
        Convert a list of pmids to markdown
        Save raw html to save_dir/html and markdown to save_dir/markdown
        
        Args:
            pmids (List[str]): List of PMIDs to convert
            save_dir (str): Directory to save the files to (default: "data/")
        """
        # Create necessary directories
        html_dir = os.path.join(save_dir, "html")
        markdown_dir = os.path.join(save_dir, "markdown")
        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(markdown_dir, exist_ok=True)

        # Get PMCIDs
        logger.info(f"Getting PMCIDs for {len(pmids)} PMIDs")
        pmcid_mapping = get_pmcid_from_pmid(pmids)
        pmcids = [pmcid_mapping.get(pmid) for pmid in pmids]
        valid_pmcids = [pmcid for pmcid in pmcids if pmcid is not None]
        
        logger.info(f"Found {len(valid_pmcids)} valid PMCIDs")
        
        # Convert to HTML
        logger.info(f"Converting PMCIDs to HTML")
        for pmcid in tqdm(valid_pmcids, desc="Converting PMCIDs to HTML"):
            html_text = get_html_from_pmcid(pmcid)
            if html_text is None:
                logger.error(f"No HTML found for PMCID {pmcid}")
                continue

            # Save HTML
            try:
                html_path = os.path.join(html_dir, f"{pmcid}.html")
                with open(html_path, "w") as f:
                    f.write(html_text)
            except Exception as e:
                logger.error(f"Error saving HTML for PMCID {pmcid}: {str(e)}")
                continue

    def pmids_to_markdown(self, pmids: List[str], save_dir: str = "data") -> None:
        """
        Convert a list of pmids to markdown
        """
        self.pmids_to_html(pmids, save_dir)
        self.local_html_to_markdown(save_dir)
    
if __name__ == "__main__":
    converter = PubMedToMarkdownConverter()
    pmid_example = "23922954"
    markdown = converter.convert_single_pmid(pmid_example)
    print(markdown)
    pmids = ["23922954", "23922955", "23922956"]
    converter.convert_pmids(pmids)