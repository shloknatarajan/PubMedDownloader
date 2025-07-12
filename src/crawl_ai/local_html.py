import asyncio
import os
import re
import tempfile
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from tqdm import tqdm
from loguru import logger
from bs4 import BeautifulSoup

def extract_article_content(html_content):
    """Extract main article content from PMC HTML, removing navigation and UI elements."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove navigation, header, footer, and UI elements
    for element in soup.find_all(['header', 'nav', 'footer', 'aside']):
        element.decompose()
    
    # Remove specific PMC UI elements
    for element in soup.find_all(class_=['usa-banner', 'skip-link', 'ncbi-header', 'header', 'footer']):
        element.decompose()
        
    for element in soup.find_all(id=['skip-to-main-content', 'header', 'footer']):
        element.decompose()
    
    # Remove script and style tags
    for element in soup.find_all(['script', 'style']):
        element.decompose()
    
    # Find the main article content
    article = soup.find('article') or soup.find(class_='article') or soup.find('main')
    if not article:
        # Fallback: look for content container
        article = soup.find(id='maincontent') or soup.find(class_='content') or soup
    
    return str(article)

async def extract_tables_and_figures(html_content):
    """Extract tables and figures from raw HTML using crawl4ai.
    
    Args:
        html_content (str): Raw HTML content
        
    Returns:
        dict: Dictionary containing extracted tables and figures with the following structure:
            {
                'tables': [
                    {
                        'headers': ['col1', 'col2', ...],
                        'rows': [['row1_col1', 'row1_col2', ...], ...],
                        'caption': 'Table caption text',
                        'summary': 'Table summary'
                    }
                ],
                'images': [
                    {
                        'src': 'image_url_or_path',
                        'alt': 'alt text',
                        'title': 'title text',
                        'width': 'width_value',
                        'height': 'height_value'
                    }
                ]
            }
    """
    # Clean and preprocess the HTML content
    cleaned_html = extract_article_content(html_content)
    
    # Create a temporary file to serve the HTML content to crawl4ai
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(cleaned_html)
        temp_file_path = temp_file.name
    
    try:
        # Create file URL for local HTML processing
        file_url = f"file://{Path(temp_file_path).absolute()}"
        
        # Use crawl4ai to extract media and tables
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=file_url,
                bypass_cache=True,
                screenshot=False,  # Don't need screenshot for table/figure extraction
                exclude_external_images=True,  # Focus on embedded content
            )
        
        if not result.success:
            logger.error(f"Crawl4ai extraction failed: {result.error_message}")
            return {'tables': [], 'images': []}
        
        # Extract tables and images from the result
        extracted_data = {
            'tables': result.media.get("tables", []),
            'images': result.media.get("images", [])
        }
        
        # Filter and enhance image data to focus on figures
        filtered_images = []
        for img in extracted_data['images']:
            # Skip very small images (likely icons or decorative elements)
            try:
                width = int(img.get('width', 0)) if img.get('width') else 0
                height = int(img.get('height', 0)) if img.get('height') else 0
                
                # Filter criteria for figures:
                # - Has meaningful alt text or title
                # - Reasonable dimensions (likely actual figures)
                # - Not obviously decorative (no "icon", "button", "logo" in alt text)
                alt_text = (img.get('alt', '') or '').lower()
                title_text = (img.get('title', '') or '').lower()
                
                is_figure = (
                    (width >= 100 or height >= 100 or width == 0 or height == 0) and  # Reasonable size or unknown size
                    (alt_text and not any(term in alt_text for term in ['icon', 'button', 'logo', 'arrow', 'bullet'])) or
                    (title_text and not any(term in title_text for term in ['icon', 'button', 'logo', 'arrow', 'bullet'])) or
                    any(term in alt_text for term in ['figure', 'fig', 'graph', 'chart', 'plot', 'diagram', 'image'])
                )
                
                if is_figure:
                    filtered_images.append(img)
                    
            except (ValueError, TypeError):
                # If we can't parse dimensions, include the image if it has descriptive text
                alt_text = (img.get('alt', '') or '').lower()
                if alt_text and len(alt_text) > 3:
                    filtered_images.append(img)
        
        extracted_data['images'] = filtered_images
        
        logger.info(f"Extracted {len(extracted_data['tables'])} tables and {len(extracted_data['images'])} figures from HTML")
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error during table/figure extraction: {str(e)}")
        return {'tables': [], 'images': []}
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass

def format_as_academic_markdown(markdown_content, pmcid):
    """Format crawl4ai markdown output to match academic paper structure with metadata."""
    lines = markdown_content.split('\n')
    
    # Initialize structure
    title = ""
    authors = ""
    journal = ""
    date = ""
    doi = ""
    pmid = ""
    keywords = ""
    main_content = []
    
    # State tracking
    skip_until_content = True
    in_abstract = False
    abstract_background = ""
    abstract_methods = ""
    abstract_conclusions = ""
    current_abstract_section = ""
    
    # Common academic section headers to detect
    section_patterns = {
        r'^\s*abstract\s*$': '## Abstract',
        r'^\s*introduction\s*$': '## Introduction',
        r'^\s*background\s*$': '### Background',
        r'^\s*methods?\s*$': '## Methods',
        r'^\s*methodology\s*$': '## Methodology',
        r'^\s*materials?\s+and\s+methods?\s*$': '## Materials and Methods',
        r'^\s*results?\s*$': '## Results',
        r'^\s*discussion\s*$': '## Discussion',
        r'^\s*conclusions?\s*$': '### Conclusions',
        r'^\s*acknowledgments?\s*$': '## Acknowledgments',
        r'^\s*acknowledgements?\s*$': '## Acknowledgements',
        r'^\s*references?\s*$': '## References',
        r'^\s*bibliography\s*$': '## References',
        r'^\s*funding\s*$': '## Funding',
        r'^\s*conflicts?\s+of\s+interest\s*$': '## Conflicts of Interest',
        r'^\s*data\s+availability\s*$': '## Data Availability',
        r'^\s*supplementary\s+materials?\s*$': '## Supplementary Materials',
        r'^\s*ethics\s+statement\s*$': '## Ethics Statement',
        r'^\s*author\s+contributions?\s*$': '## Author Contributions',
        r'^\s*keywords?\s*[:.]?\s*$': 'Keywords:'
    }
    
    # Parse content
    for line in lines:
        # Skip common website navigation patterns
        if any(pattern in line.lower() for pattern in [
            'skip to main content', 'official website', 'here\'s how you know',
            '.gov website', 'ncbi home page', 'search database', 'log in',
            'dashboard', 'publications', 'account settings', 'pubmed',
            'pmc', 'mesh', 'download pdf', 'cite this', 'share this'
        ]):
            continue
            
        # Extract metadata early
        if 'doi:' in line.lower() or 'doi.org' in line.lower():
            doi_match = re.search(r'doi:\s*([^\s]+)|doi\.org/([^\s\)]+)', line.lower())
            if doi_match:
                doi = doi_match.group(1) or doi_match.group(2)
        
        if 'pmid:' in line.lower():
            pmid_match = re.search(r'pmid:\s*(\d+)', line.lower())
            if pmid_match:
                pmid = pmid_match.group(1)
        
        # Skip empty lines at the beginning
        if skip_until_content and line.strip() == '':
            continue
            
        # Start collecting content when we hit actual article content
        if line.strip() and skip_until_content:
            # Look for title-like content (usually the first substantial line)
            if len(line.strip()) > 10 and not line.startswith('!') and not line.startswith('[') and not line.startswith('http'):
                skip_until_content = False
                title = line.strip()
                continue
        
        if not skip_until_content:
            line_lower = line.strip().lower()
            
            # Handle abstract sections specially
            if line_lower == 'abstract' or in_abstract:
                if line_lower == 'abstract':
                    in_abstract = True
                    continue
                elif line_lower in ['introduction', 'background', 'methods', 'results', 'discussion', 'conclusions']:
                    in_abstract = False
                elif line_lower.startswith('background'):
                    current_abstract_section = 'background'
                    abstract_background = line.replace('Background:', '').replace('background:', '').strip()
                    continue
                elif line_lower.startswith('methods') or line_lower.startswith('method'):
                    current_abstract_section = 'methods'
                    abstract_methods = line.replace('Methods:', '').replace('methods:', '').replace('Method:', '').replace('method:', '').strip()
                    continue
                elif line_lower.startswith('results') or line_lower.startswith('result'):
                    current_abstract_section = 'methods'  # Continue methods section if it contains results
                    if abstract_methods:
                        abstract_methods += ' ' + line.replace('Results:', '').replace('results:', '').replace('Result:', '').replace('result:', '').strip()
                    else:
                        abstract_methods = line.replace('Results:', '').replace('results:', '').replace('Result:', '').replace('result:', '').strip()
                    continue
                elif line_lower.startswith('conclusions') or line_lower.startswith('conclusion'):
                    current_abstract_section = 'conclusions'
                    abstract_conclusions = line.replace('Conclusions:', '').replace('conclusions:', '').replace('Conclusion:', '').replace('conclusion:', '').strip()
                    continue
                elif line.strip() and current_abstract_section:
                    # Continue building current abstract section
                    if current_abstract_section == 'background':
                        abstract_background += ' ' + line.strip()
                    elif current_abstract_section == 'methods':
                        abstract_methods += ' ' + line.strip()
                    elif current_abstract_section == 'conclusions':
                        abstract_conclusions += ' ' + line.strip()
                    continue
            
            # Handle keywords
            if 'keywords' in line_lower and ':' in line:
                keywords = line.split(':', 1)[1].strip()
                continue
            
            # Extract authors (usually appears early, before abstract)
            if not authors and not in_abstract and len(line.strip()) > 5 and ',' in line and not line.startswith('#'):
                # Check if this looks like author names
                if any(indicator in line.lower() for indicator in ['university', 'institute', 'hospital', 'college', 'department', 'center', 'school']):
                    authors = line.strip()
                    continue
            
            # Check if this line matches a section header pattern
            section_matched = False
            for pattern, header in section_patterns.items():
                if re.match(pattern, line_lower):
                    main_content.append(f"\n{header}\n")
                    section_matched = True
                    in_abstract = False
                    break
            
            if not section_matched and not in_abstract:
                # Check for numbered sections (e.g., "1. Introduction", "2.1 Methods")
                numbered_section = re.match(r'^\s*(\d+\.?\d*\.?)\s+(.+)$', line.strip())
                if numbered_section and len(numbered_section.group(2)) > 3:
                    section_title = numbered_section.group(2).title()
                    main_content.append(f"\n## {section_title}\n")
                # Check for other potential headings (all caps, short lines)
                elif line.strip().isupper() and 3 < len(line.strip()) < 50 and line.strip().replace(' ', '').isalpha():
                    main_content.append(f"\n### {line.strip().title()}\n")
                else:
                    main_content.append(line)
    
    # Build the structured markdown
    result = []
    
    # Title
    if title:
        result.append(f"# {title}")
        result.append("")
    
    # Metadata section
    result.append("## Metadata")
    if authors:
        result.append(f"**Authors:** {authors}")
    if journal:
        result.append(f"**Journal:** {journal}")
    if date:
        result.append(f"**Date:** {date}")
    if doi:
        result.append(f"**DOI:** [https://doi.org/{doi}](https://doi.org/{doi})")
    if pmid:
        result.append(f"**PMID:** {pmid}")
    result.append(f"**PMCID:** {pmcid}")
    result.append(f"**URL:** https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/")
    result.append(f"**PDF:** [https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/](https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/)")
    result.append("")
    
    # Abstract section
    if abstract_background or abstract_methods or abstract_conclusions:
        result.append("## Abstract")
        result.append("")
        if abstract_background:
            result.append("**Background:** ")
            result.append(abstract_background)
            result.append("")
        if abstract_methods:
            result.append("**Methods and Results:** ")
            result.append(abstract_methods)
            result.append("")
        if abstract_conclusions:
            result.append("**Conclusions:** ")
            result.append(abstract_conclusions)
            result.append("")
    
    # Keywords
    if keywords:
        result.append(f"Keywords: {keywords}")
        result.append("")
    
    # Main content
    if main_content:
        content = '\n'.join(main_content)
        # Clean up excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'^\s*\n+', '', content)
        # Ensure proper spacing around headers
        content = re.sub(r'\n(#{1,6}\s)', r'\n\n\1', content)
        content = re.sub(r'(#{1,6}\s[^\n]+)\n([^\n#])', r'\1\n\n\2', content)
        result.append(content.strip())
    
    # Fallback if no title found
    if not title:
        result.insert(0, "# Research Article")
        result.insert(1, "")
    
    return '\n'.join(result)

async def crawl_local_html_files(html_dir, output_dir):
    html_dir = Path(html_dir)
    output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    html_files = list(html_dir.glob("*.html"))
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    async with AsyncWebCrawler() as crawler:
        for html_file in tqdm(html_files):
            pmcid = html_file.stem
            output_file = output_dir / f"{pmcid}.md"
            
            if output_file.exists():
                logger.info(f"Skipping {html_file.name} - already converted")
                continue
            
            logger.info(f"Processing {html_file.name}...")
            
            try:
                # Read and preprocess HTML
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Extract main article content
                article_html = extract_article_content(html_content)
                
                # Write temporary file for crawl4ai to process
                temp_file = html_file.with_suffix('.temp.html')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(article_html)
                
                file_url = f"file://{temp_file.absolute()}"
                result = await crawler.arun(url=file_url, bypass_cache=True)
                
                # Clean up temp file
                temp_file.unlink()
                
                if result.success:
                    # Format the markdown content
                    formatted_content = format_as_academic_markdown(result.markdown, pmcid)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(formatted_content)
                    logger.info(f"Successfully converted {html_file.name} to {output_file.name}")
                else:
                    logger.error(f"Failed to crawl {html_file.name}: {result.error_message}")
            except Exception as e:
                logger.error(f"Error processing {html_file.name}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(crawl_local_html_files("data/test/html", "data/test/markdown"))