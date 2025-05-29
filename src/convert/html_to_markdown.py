"""
Parse the HTML file and filter the text to the article body
Information to get:
- PMID
- PMCID
- Title
- Authors
- Text (convert to markdown)

Final output is a markdown file with the pmcid as the filename
"""

from bs4 import BeautifulSoup
import re
import os

def html_to_markdown(raw_html: str) -> str:
    """
    Parse the HTML file for the pubmed article (example, data/raw_html/PMC1884285.html) and return markdown formatted text
    Contain links to any images in the article. Ignore links to external sites, just include the paper text.
    """
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # Extract metadata
    pmcid = extract_pmcid(soup)
    pmid = extract_pmid(soup)
    title = extract_title(soup)
    authors = extract_authors(soup)
    
    # Extract main article content
    article_content = extract_article_content(soup)
    
    # Build markdown
    markdown = build_markdown(pmcid, pmid, title, authors, article_content)
    
    return markdown

def save_markdown(pmcid: str, markdown: str, save_dir: str) -> None:
    """Save the markdown to a file"""
    save_path = os.path.join(save_dir, f"{pmcid}.md")
    os.makedirs(save_dir, exist_ok=True)
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

def extract_pmcid(soup: BeautifulSoup) -> str:
    """Extract PMCID from the HTML"""
    # Look for PMCID in canonical URL or meta tags
    canonical = soup.find('link', {'rel': 'canonical'})
    if canonical and canonical.get('href'):
        match = re.search(r'PMC(\d+)', canonical['href'])
        if match:
            return f"PMC{match.group(1)}"
    
    # Look in text content
    pmcid_text = soup.find(text=re.compile(r'PMCID:\s*PMC\d+'))
    if pmcid_text:
        match = re.search(r'PMC\d+', pmcid_text)
        if match:
            return match.group(0)
    
    return ""


def extract_pmid(soup: BeautifulSoup) -> str:
    """Extract PMID from the HTML"""
    # Look for PMID link
    pmid_link = soup.find('a', href=re.compile(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)'))
    if pmid_link:
        match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', pmid_link['href'])
        if match:
            return match.group(1)
    
    # Look in text content
    pmid_text = soup.find(text=re.compile(r'PMID:\s*\d+'))
    if pmid_text:
        match = re.search(r'PMID:\s*(\d+)', pmid_text)
        if match:
            return match.group(1)
    
    return ""


def extract_title(soup: BeautifulSoup) -> str:
    """Extract article title"""
    # Look in citation meta tag
    title_meta = soup.find('meta', {'name': 'citation_title'})
    if title_meta:
        return title_meta.get('content', '').strip()
    
    # Look in page title and clean it
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().strip()
        # Remove PMC suffix
        title = re.sub(r'\s*-\s*PMC$', '', title)
        return title
    
    return ""


def extract_authors(soup: BeautifulSoup) -> list:
    """Extract list of authors"""
    authors = []
    
    # Look in citation meta tags
    author_metas = soup.find_all('meta', {'name': 'citation_author'})
    for meta in author_metas:
        author = meta.get('content', '').strip()
        if author:
            authors.append(author)
    
    return authors


def extract_article_content(soup: BeautifulSoup) -> str:
    """Extract main article content and convert to markdown"""
    markdown_parts = []
    
    # Find the main article element
    article = soup.find('article') or soup.find('main')
    if not article:
        return ""
    
    # Extract abstract
    abstract_section = article.find('section', class_='abstract')
    if abstract_section:
        abstract_content = convert_section_to_markdown(abstract_section)
        # Check if the content already starts with "## Abstract"
        if not abstract_content.strip().startswith("## Abstract"):
            markdown_parts.append("## Abstract\n\n")
        markdown_parts.append(abstract_content)
        markdown_parts.append("\n")
    
    # Extract main body sections
    main_sections = article.find_all('section', id=re.compile(r'^sec\d+$'))
    for section in main_sections:
        section_md = convert_section_to_markdown(section)
        if section_md.strip():
            markdown_parts.append(section_md)
            markdown_parts.append("\n")
    
    # Extract references if present
    ref_section = article.find('section', class_='ref-list')
    if ref_section:
        markdown_parts.append("## References\n")
        markdown_parts.append(convert_references_to_markdown(ref_section))
    
    return "".join(markdown_parts)


def convert_section_to_markdown(section) -> str:
    """Convert a section element to markdown"""
    markdown_parts = []
    
    for element in section.children:
        if hasattr(element, 'name'):
            if element.name == 'h2':
                markdown_parts.append(f"## {element.get_text().strip()}\n\n")
            elif element.name == 'h3':
                markdown_parts.append(f"### {element.get_text().strip()}\n\n")
            elif element.name == 'p':
                paragraph_md = convert_paragraph_to_markdown(element)
                if paragraph_md.strip():
                    markdown_parts.append(f"{paragraph_md}\n\n")
            elif element.name == 'figure':
                figure_md = convert_figure_to_markdown(element)
                if figure_md.strip():
                    markdown_parts.append(f"{figure_md}\n\n")
            elif element.name == 'ul' or element.name == 'ol':
                list_md = convert_list_to_markdown(element)
                if list_md.strip():
                    markdown_parts.append(f"{list_md}\n\n")
    
    return "".join(markdown_parts)


def convert_paragraph_to_markdown(p_element) -> str:
    """Convert paragraph element to markdown, handling inline formatting"""
    text_parts = []
    
    for element in p_element.children:
        if hasattr(element, 'name'):
            if element.name == 'em' or element.name == 'i':
                text_parts.append(f"*{element.get_text()}*")
            elif element.name == 'strong' or element.name == 'b':
                text_parts.append(f"**{element.get_text()}**")
            elif element.name == 'sup':
                text_parts.append(f"^{element.get_text()}^")
            elif element.name == 'sub':
                text_parts.append(f"_{element.get_text()}_")
            elif element.name == 'a':
                href = element.get('href', '')
                text = element.get_text()
                if href.startswith('http'):
                    text_parts.append(f"[{text}]({href})")
                else:
                    text_parts.append(text)
            else:
                text_parts.append(element.get_text())
        else:
            text_parts.append(str(element))
    
    return "".join(text_parts).strip()


def convert_figure_to_markdown(figure_element) -> str:
    """Convert figure element to markdown"""
    markdown_parts = []
    
    # Find image
    img = figure_element.find('img')
    if img:
        src = img.get('src', '')
        alt = img.get('alt', '')
        if src:
            # Convert relative URLs to absolute for PMC
            if src.startswith('/') or src.startswith('https://cdn.ncbi.nlm.nih.gov'):
                if src.startswith('/'):
                    src = f"https://cdn.ncbi.nlm.nih.gov{src}"
                markdown_parts.append(f"![{alt}]({src})\n\n")
    
    # Find caption
    caption = figure_element.find('figcaption')
    if caption:
        caption_text = convert_paragraph_to_markdown(caption)
        if caption_text.strip():
            markdown_parts.append(f"*{caption_text.strip()}*\n")
    
    return "".join(markdown_parts)


def convert_list_to_markdown(list_element) -> str:
    """Convert list element to markdown"""
    markdown_parts = []
    is_ordered = list_element.name == 'ol'
    
    for i, li in enumerate(list_element.find_all('li'), 1):
        li_text = convert_paragraph_to_markdown(li)
        if is_ordered:
            markdown_parts.append(f"{i}. {li_text}\n")
        else:
            markdown_parts.append(f"- {li_text}\n")
    
    return "".join(markdown_parts)


def convert_references_to_markdown(ref_section) -> str:
    """Convert references section to markdown"""
    markdown_parts = []
    
    ref_list = ref_section.find('ul', class_='ref-list')
    if ref_list:
        for li in ref_list.find_all('li'):
            ref_text = li.get_text().strip()
            if ref_text:
                # Clean up extra whitespace
                ref_text = re.sub(r'\s+', ' ', ref_text)
                markdown_parts.append(f"- {ref_text}\n")
    
    return "".join(markdown_parts)


def build_markdown(pmcid: str, pmid: str, title: str, authors: list, content: str) -> str:
    """Build the final markdown document"""
    markdown_parts = []
    
    # Title
    if title:
        markdown_parts.append(f"# {title}\n\n")
    
    # Metadata
    markdown_parts.append("## Metadata\n\n")
    if pmcid:
        markdown_parts.append(f"**PMCID:** {pmcid}\n\n")
        # Add URL to the article
        markdown_parts.append(f"**URL:** https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/\n\n")
    if pmid:
        markdown_parts.append(f"**PMID:** {pmid}\n\n")
    
    # Authors
    if authors:
        markdown_parts.append("**Authors:** ")
        markdown_parts.append(", ".join(authors))
        markdown_parts.append("\n\n")
    
    # Article content
    if content:
        markdown_parts.append(content)
    
    return "".join(markdown_parts) 