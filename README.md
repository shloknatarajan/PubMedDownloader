# Convert Pubmed Article (PMID) to Markdown
Go from a PMID to the full article text in markdown format as long as the article has a valid PMCID

## Usage
```
python -m src.markdown_from_pmid --pmid <PIMD> --save_dir <data>
```

## Examples for testing
| PMID | PMCID | Link |  Notes |
| ---- | ----- | ----- | ----- |
| 12895196 | PMC1884285 | https://pmc.ncbi.nlm.nih.gov/articles/PMC1884285/ | Intervention study|
| 17872605 | PMC1952551 | https://pmc.ncbi.nlm.nih.gov/articles/PMC1952551/ | Case study |

## Notes
Make sure to have a .env with your NCBI_EMAIL=your-email@school.edu