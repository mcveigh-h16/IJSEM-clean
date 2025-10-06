# IJSEM-webscraper

## selenium_webscraper-ver4.4.ipynb
Jupyter notebook webscraper (selenium and beautifulsoup) designed to take the content of the weekly html email sent by IJSEM. Open the link to each publication and extract the organism name, accession numbers and type strain information. This is then compared to what NCBI taxonomy has with srcchk. NOTE use of srcchk requires linux to access this internal NCBI tool. The outputs are compared in pandas looking for differing organism names. Final output is an excel file to allow taxonomy updates. 
Organism names, strain names and accessions are extracted from the species description for each species described in the paper. 
If strains are not found, these will be blank in the dataframe. These situations require manual inspection. 
Strain name detection by spacy with custom NER library. This NER library could be expanded for added accuracy but working 99% of the time now as is. 
Script is optimized for bacterial type strain detections. Future improvements could included switching organism name detection from regex to NLP with spacy. Updated for windows 11 computer 

## IJSEMwebscraper1.4.py 
standard python version of the notebook with same core functionality. Updated for windows 11 computer. Call the script with the prefix of the .htm input file. Output files saved with same prefix
## IJSEMwebscraper_SS3.py 
modification of IJSEMwebscraper.py for Shoba's web driver installation. 
