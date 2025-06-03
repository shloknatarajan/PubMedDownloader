from .pmcid_from_pmid import get_pmcid_from_pmid
from .html_from_pmcid import get_html_from_pmcid
from .markdown_from_html import PubMedHTMLToMarkdownConverter
from typing import List
import os
from loguru import logger
from tqdm import tqdm

class PubMedToMarkdownConverter:
    """
    Two flows: convert a single pmid to markdown
    - convert a single pmid to markdown
    - convert a list of pmids to markdown saving raw html to save_dir/html and markdown to save_dir/markdown
    """
    def __init__(self):
        self.converter = PubMedHTMLToMarkdownConverter()
    
    def convert_single_pmid(self, pmid: str) -> str:
        pmcid = get_pmcid_from_pmid(pmid)
        html = get_html_from_pmcid(pmcid)
        markdown = self.converter.convert_html(html)
        return markdown
    
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
    
    def convert_local_html(self, save_dir: str = "data/") -> None:
        """
        Convert all html files in the save_dir/raw_html directory to markdown
        """
        htmls = os.listdir(os.path.join(save_dir, "raw_html"))
        html_paths = [os.path.join(save_dir, "raw_html", f) for f in htmls]
        for html_path in tqdm(html_paths, desc=f"Converting html ({save_dir}/raw_html) to markdown"):
            markdown = self.converter.convert_file(html_path)
            with open(os.path.join(save_dir, "markdown", f"{html_path.split('/')[-1].replace('.html', '.md')}" ), "w") as f:
                f.write(markdown)
    
    def convert_pmids(self, pmids: List[str], save_dir: str = "data/") -> None:
        """
        Convert a list of pmids to markdown
        Save raw html to save_dir/html and markdown to save_dir/markdown
        """
        pmcids = get_pmcid_from_pmid(pmids)
        logger.info(f"Converting {len(pmcids)} pmcids to html")
        get_html_from_pmcid(pmcids, save_dir=save_dir)
        logger.info(f"Converting html to markdown")
        htmls = os.listdir(os.path.join(save_dir, "html"))
        htmls = [os.path.join(save_dir, "html", f) for f in htmls]
        for html in tqdm(htmls, desc="Converting html to markdown"):
            markdown = self.converter.convert_file(html)
            with open(os.path.join(save_dir, "markdown", f"{html.split('/')[-1].replace('.html', '.md')}" ), "w") as f:
                f.write(markdown)
    

    
