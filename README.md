# Goal
Go from a PMID to the full article text 

## Options
- Test if the PMCID works to get the full text as expected (this would be fully supported / legal) using official APIs
- Some sort of GET request system with link https://pmc.ncbi.nlm.nih.gov/articles/{PMCID}/
- Find some pre-built package
- Look into Aaron's playwright method


## Examples for testing
| PMID | PMCID | Link |  Notes |
| ---- | ----- | ----- | ----- |
| 12895196 | PMC1884285 | https://pmc.ncbi.nlm.nih.gov/articles/PMC1884285/ | Intervention study|
| 17872605 | PMC1952551 | https://pmc.ncbi.nlm.nih.gov/articles/PMC1952551/ | Case study |