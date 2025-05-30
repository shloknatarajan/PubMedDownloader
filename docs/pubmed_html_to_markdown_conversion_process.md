# Process for Converting PubMed HTML to Markdown

Based on analysis of 20+ PMC HTML files from the raw_html directory.

## Document Structure Analysis

**Two main types of PMC articles:**
- **Modern articles** (2010+): Structured HTML with full text content
- **Legacy articles** (older): Scanned images with limited structured text

## Core Conversion Steps

### Step 1: Extract Metadata
```html
<!-- Target these meta tags -->
<meta name="citation_title" content="...">
<meta name="citation_author" content="...">
<meta name="citation_journal_title" content="...">
<meta name="citation_publication_date" content="...">
<meta name="citation_doi" content="...">
<meta name="citation_pmid" content="...">
<meta name="citation_pdf_url" content="...">
```

### Step 2: Extract Main Content Sections
Target the main article body: `<section class="body main-article-body">`

**Key sections to extract:**
- Abstract: `<section class="abstract" id="abstract1">`
- Introduction: `<section id="Sec1">` with `<h2 class="pmc_sec_title">Introduction</h2>`
- Methods: `<section id="Sec2">` with methods-related titles
- Results: `<section id="SecX">` with results titles
- Discussion: `<section id="SecY">` with discussion titles
- References: `<section id="Bib1" class="ref-list">`

## Content Element Conversion

### Tables
```html
<!-- Source HTML structure -->
<section class="tw xbox font-sm" id="Tab1">
    <h3 class="obj_head">Table 1.</h3>
    <div class="caption p"><p>Caption text</p></div>
    <div class="tbl-box p">
        <table class="content">
            <thead>...</thead>
            <tbody>...</tbody>
        </table>
    </div>
</section>
```

**Conversion approach:**
1. Extract table title from `<h3 class="obj_head">`
2. Extract caption from `<div class="caption p">`
3. Convert HTML table to markdown table format
4. Preserve alignment attributes (`align="left/center/right"`)
5. Handle complex structures (rowspan/colspan with notation)

### Figures
```html
<!-- Source HTML structure -->
<figure class="fig xbox font-sm" id="Fig2">
    <h4 class="obj_head">Fig. 2.</h4>
    <p class="img-box">
        <img class="graphic" src="https://cdn.ncbi.nlm.nih.gov/pmc/blobs/...jpg">
    </p>
    <figcaption>Caption text</figcaption>
</figure>
```

**Conversion approach:**
1. Extract figure number from `<h4 class="obj_head">`
2. Preserve image URL from `src` attribute
3. Extract caption text from `<figcaption>`
4. Create markdown image reference: `![Figure X](URL)`
5. Include figure caption below image

### Mathematical Equations
```html
<!-- Source MathML -->
<table class="disp-formula p" id="FD1">
    <tr>
        <td class="formula">
            <math display="block">...</math>
        </td>
        <td class="label">(1)</td>
    </tr>
</table>
```

**Conversion approach:**
1. Convert MathML to LaTeX format when possible
2. Use equation blocks: `$$LaTeX equation$$`
3. Preserve equation numbering
4. Fall back to image capture for complex equations

### Citations and References
```html
<!-- In-text citations -->
<a href="#bcp15541-bib-0001" class="usa-link">
    <sup>1</sup>
</a>

<!-- Reference list -->
<section id="Bib1" class="ref-list">
    <ul class="ref-list font-sm">
        <li>
            <span class="label">1.</span>
            <cite>Reference content</cite>
            [<a href="DOI_LINK">DOI</a>]
            [<a href="PMC_LINK">PMC</a>]
            [<a href="PUBMED_LINK">PubMed</a>]
        </li>
    </ul>
</section>
```

**Conversion approach:**
1. Convert in-text citations to markdown format: `[1]`
2. Create reference section with numbered list
3. Preserve external links (DOI, PMC, PubMed)
4. Maintain citation integrity with internal linking

## Link Preservation Strategy

### Figure Links
- Preserve original CDN URLs: `https://cdn.ncbi.nlm.nih.gov/pmc/blobs/...`
- Include zoom/tileshop links for interactive viewing
- Add "Open in new tab" functionality

### PDF Links
- Extract from `<meta name="citation_pdf_url">` 
- Include direct download links in markdown header

### Supplementary Materials
- Extract links to supplementary tables/files
- Preserve appendix references
- Include supporting information links

## Quality Preservation Steps

### Text Formatting
- Convert `<em>` to `*italic*`
- Convert `<strong>` to `**bold**`
- Preserve subscripts: `<sub>` → `_subscript_`
- Preserve superscripts: `<sup>` → `^superscript^`

### Section Hierarchy
- Extract heading levels from `<h2>`, `<h3>`, `<h4>`
- Convert to markdown headers: `##`, `###`, `####`
- Preserve section numbering when present

### Cross-References
- Convert internal links to markdown references
- Maintain table/figure cross-referencing
- Preserve section linking

## Output Format Template

```markdown
# [Article Title]

**Authors:** [Author list]  
**Journal:** [Journal Name]  
**DOI:** [DOI Link]  
**PMID:** [PMID]  
**PDF:** [PDF Link]

## Abstract
[Abstract content]

## Introduction
[Introduction content]

## Methods
[Methods content]

### [Subsection]
[Subsection content]

## Results
[Results content]

### Table 1: [Table Title]
[Table Caption]

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |

### Figure 1: [Figure Title]
![Figure 1](image_url)
[Figure Caption]

## Discussion
[Discussion content]

## References
1. [Reference 1 with links]
2. [Reference 2 with links]
```

## Special Considerations

### Legacy Articles (Scanned)
- Extract text from abstract sections
- Include links to scanned page images
- Preserve PDF references for full content access
- Note content limitations in markdown header

### Complex Tables
- Use HTML table blocks when markdown tables insufficient
- Preserve formatting for complex scientific data
- Include table notes and footnotes

### Error Handling
- Graceful degradation for missing sections
- Fallback strategies for malformed HTML
- Validation of extracted content completeness

## Key CSS Selectors for Implementation

- **Main article body**: `section.body.main-article-body`
- **Abstract**: `section.abstract#abstract1`
- **Section titles**: `h2.pmc_sec_title`, `h3.pmc_sec_title`
- **Tables**: `section.tw.xbox` containing `table.content`
- **Figures**: `figure.fig.xbox` containing `img.graphic`
- **References**: `section.ref-list` containing `ul.ref-list`
- **Equations**: `table.disp-formula` containing `math`
- **Citations**: `a.usa-link[href^="#"]`

## Implementation Notes

1. **Parse HTML with BeautifulSoup or similar robust parser**
2. **Handle missing sections gracefully** - not all articles have all sections
3. **Validate extracted content** - ensure completeness and accuracy
4. **Test with both modern and legacy article formats**
5. **Preserve link integrity** - maintain working references to figures, tables, and citations
6. **Handle special characters** - ensure proper encoding in markdown output