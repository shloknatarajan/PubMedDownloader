from .pmcid_from_pmid import get_pmcid_from_pmid
from .html_from_pmcid import get_html_from_pmcid
from .markdown_from_html import PubMedHTMLToMarkdownConverter
from typing import List, Optional
import os
from loguru import logger
from tqdm import tqdm
import argparse


class PubMedDownloader:
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
        pmcid = pmcid_mapping.get(str(pmid))

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

    def check_existing_html_pmcids(self, save_dir: str = "data/") -> List[str]:
        """
        Get a list of all PMCIDs that have HTML files in the save_dir/html directory.

        Args:
            save_dir (str): Directory to check for HTML files (default: "data/")

        Returns:
            List[str]: List of PMCIDs that have existing HTML files
        """
        html_dir = os.path.join(save_dir, "html")
        if not os.path.exists(html_dir):
            return []

        existing_html = []
        for filename in os.listdir(html_dir):
            if filename.endswith(".html"):
                pmcid = filename[:-5]  # Remove .html extension
                existing_html.append(pmcid)
        return existing_html

    def check_existing_markdown_pmcids(self, save_dir: str = "data/") -> List[str]:
        """
        Get a list of all PMCIDs that have markdown files in the save_dir/markdown directory.

        Args:
            save_dir (str): Directory to check for markdown files (default: "data/")

        Returns:
            List[str]: List of PMCIDs that have existing markdown files
        """
        markdown_dir = os.path.join(save_dir, "markdown")
        if not os.path.exists(markdown_dir):
            return []

        existing_markdown = []
        for filename in os.listdir(markdown_dir):
            if filename.endswith(".md"):
                pmcid = filename[:-3]  # Remove .md extension
                existing_markdown.append(pmcid)
        return existing_markdown

    def local_html_to_markdown(
        self, save_dir: str = "data/", overwrite: bool = False
    ) -> None:
        """
        Convert all html files in the save_dir/html directory to markdown

        Args:
            save_dir (str): Directory containing HTML files (default: "data/")
            overwrite (bool): Whether to overwrite existing markdown files (default: False)
        """
        html_dir = os.path.join(save_dir, "html")
        if not os.path.exists(html_dir):
            logger.warning(f"No HTML directory found at {html_dir}")
            return

        htmls = os.listdir(html_dir)
        html_paths = [os.path.join(html_dir, f) for f in htmls]

        if not overwrite:
            # Get existing markdown files
            existing_markdown = self.check_existing_markdown_pmcids(save_dir)
            logger.info(f"Found {len(existing_markdown)} existing markdown files")
            # Filter out HTML files that already have markdown
            htmls = [
                html
                for html in htmls
                if html.replace(".html", "") not in existing_markdown
            ]
            html_paths = [os.path.join(html_dir, f) for f in htmls]

        logger.info(f"Converting {len(htmls)} HTML files to Markdown")
        for html_path in tqdm(
            html_paths, desc=f"Converting html ({save_dir}/html) to markdown"
        ):
            markdown = self.html_to_markdown.convert_file(html_path)
            with open(
                os.path.join(
                    save_dir,
                    "markdown",
                    f"{html_path.split('/')[-1].replace('.html', '.md')}",
                ),
                "w",
            ) as f:
                f.write(markdown)

    def pmids_to_pmcids(self, pmids: List[str], save_dir: str = "data") -> None:
        """
        Convert a list of pmids to pmcids
        """
        logger.info(f"Getting PMCIDs for {len(pmids)} PMIDs")
        pmcid_mapping = get_pmcid_from_pmid(pmids, save_dir=save_dir)
        pmcids = [pmcid_mapping.get(str(pmid)) for pmid in pmids]
        valid_pmcids = [pmcid for pmcid in pmcids if pmcid is not None]
        logger.info(f"Found {len(valid_pmcids)} valid PMCIDs out of {len(pmids)} PMIDs")
        return valid_pmcids

    def pmcids_to_html(self, pmcids: List[str], save_dir: str = "data") -> None:
        """
        Convert a list of pmcids to html
        Save raw html to save_dir/html and markdown to save_dir/markdown

        Args:
            pmcids (List[str]): List of PMCIDs to convert
            save_dir (str): Directory to save the files to (default: "data/")
        """
        # Create necessary directories
        html_dir = os.path.join(save_dir, "html")
        markdown_dir = os.path.join(save_dir, "markdown")
        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(markdown_dir, exist_ok=True)

        # Get existing HTML files
        existing_html = self.check_existing_html_pmcids(save_dir)
        logger.info(f"Found {len(existing_html)} existing html files")
        # Filter out PMCIDs that already have HTML
        pmcids = [pmcid for pmcid in pmcids if pmcid not in existing_html]
        logger.info(f"Converting {len(pmcids)} PMCIDs to HTML")

        # Convert to HTML
        for pmcid in tqdm(pmcids, desc="Converting PMCIDs to HTML"):
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

    def pmids_to_markdown(
        self, pmids: List[str], save_dir: str = "data", overwrite: bool = False
    ) -> None:
        """
        Convert a list of pmids to markdown

        Args:
            pmids (List[str]): List of PMIDs to convert
            save_dir (str): Directory to save the files to (default: "data/")
            overwrite (bool): Whether to overwrite existing files (default: False)
        """
        pmcids = self.pmids_to_pmcids(pmids, save_dir)
        if not overwrite:
            # Get existing markdown files
            existing_markdown = self.check_existing_markdown_pmcids(save_dir)
            logger.info(f"Found {len(existing_markdown)} existing markdown files")
            # Filter out PMCIDs that already have markdown
            pmcids = [pmcid for pmcid in pmcids if pmcid not in existing_markdown]
        logger.info(f"Converting {len(pmcids)} PMCIDs to Markdown")

        self.pmcids_to_html(pmcids, save_dir)
        self.local_html_to_markdown(save_dir, overwrite=overwrite)


def convert_pmids_from_file(
    file_path: str, save_dir: str = "data", overwrite: bool = False
):
    """
    Convert pmids from a txt file to markdown
    Expects a txt file with one PMID per line

    Args:
        file_path (str): Path to the txt file containing PMIDs
        save_dir (str): Directory to save the files to (default: "data/")
        overwrite (bool): Whether to overwrite existing markdown files (default: False)
    """
    converter = PubMedDownloader()
    pmids = [line.strip() for line in open(file_path, "r").readlines() if line.strip()]
    converter.pmids_to_markdown(pmids, save_dir, overwrite)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PMIDs to markdown format")
    parser.add_argument(
        "--file_path", type=str, help="Path to the txt file containing PMIDs"
    )
    parser.add_argument(
        "--save_dir",
        type=str,
        default="data",
        help="Directory to save the files to (default: 'data/')",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Whether to overwrite existing markdown files (default: False)",
    )
    args = parser.parse_args()

    if args.file_path:
        convert_pmids_from_file(args.file_path, args.save_dir, args.overwrite)
    else:
        parser.error("--file_path is required")
