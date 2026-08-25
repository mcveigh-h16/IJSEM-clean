# IJSEM-webscraper

IJSEM-webscraper is a collection of Python scripts and Jupyter notebooks for extracting organism names, accession numbers, and type-strain information from International Journal of Systematic and Evolutionary Microbiology (IJSEM) publications. It combines HTML parsing and custom spaCy named-entity recognition to produce structured data that can be compared with NCBI Taxonomy and reviewed for potential taxonomy updates.

## ijsem_html_parser.py 
Current working version. Uses beautiful soup in place of selenium combined with spacy NER for detection. 
Added security at IJSEM is blocking programmatic access to the html files. Tried multiple approaches to getting around this but so far no luck. Work around was to modify the script to remove the programmatic download by selenium. This now requires the user to manually obtain the html files and save them in a directory.

Two approaches to obtaining the html files 

+ click on each publication and allow it to fully render in your browser 
+ Once you have the rendered publication, right click > save as .html in a specific linux directory (i use one called input and this is hard coded in the script
+ Run ijsem_html_parser.py (python ijsem_html_parser.py) Script will then use the same AI driven search in IJSEMwebscraper2.0.py to extract the taxonomic information from each paper and save the output in an excel file. 
+ Note input and output directories are hard coding in the script and need to be modified for each user. 
+ Be sure to clean out old files from input directory before running new data, the script will simply analyze everything it finds in the input directory
U-se a URL list and build in chrome extension to open multiple URLs at once
https://chromewebstore.google.com/?pli=1 has two extensions Bulk URL opener and SingleFile which can be used to open a previously determined list of URLs and save the html to a directory
+ SingleFile will save the html files to the download directory on your computer. If you do this you must then manually move the saved files to the input directory in linux. 
+ Once you have the saved html files in the input directory, simply run ijsem_html_parser.py or ijsem_html_paser.ipynb 

## bulk_url_extractor.py
+ Bulk URL extractor. Use Beautiful Soup to extract URLs from a single HTML file saved from IJSEM weekly publication.
usage:
    python bulk_url_extractor.py <base_filename>
    Outputs a text file <base_filename>.txt with one URL per line. This can be used with BULK URL Opener extension in Chrome.


## labelstudio_to_spacy2.py
Converts `.json` training data exported from Label Studio to spaCy's `.spacy` format.

## Older scripts

### selenium_webscraper-ver4.4.ipynb
Jupyter notebook webscraper (selenium and beautifulsoup) designed to take the content of the weekly html email sent by IJSEM. Open the link to each publication and extract the organism name, accession numbers and type strain information. This is then compared to what NCBI taxonomy has with srcchk. NOTE use of srcchk requires linux to access this internal NCBI tool. The outputs are compared in pandas looking for differing organism names. Final output is an excel file to allow taxonomy updates.
Organism names, strain names and accessions are extracted from the species description for each species described in the paper.
If strains are not found, these will be blank in the dataframe. These situations require manual inspection.
Strain name detection by spacy with custom NER library. This NER library could be expanded for added accuracy but working 99% of the time now as is.
Script is optimized for bacterial type strain detections. Future improvements could included switching organism name detection from regex to NLP with spacy. Updated for windows 11 computer

### IJSEMwebscraper1.4.py
standard python version of the notebook with same core functionality. Updated for windows 11 computer. Call the script with the prefix of the .htm input file. Output files saved with same prefix

### IJSEMwebscraper_SS3.py
modification of IJSEMwebscraper.py for Shoba's web driver installation.

### IJSEMwebscraper1.7.ipynb
Webscraper no longer working reliably but the SPACY training instructions and testing are here which does work. Uses NER for detection of strains, organism names & basionyms using the new spacy training set.

### IJSEMwebscraper2.0.py (was IJSEMwebscraper1.8.py)
No longer working reliably. Uses NER for detection of strains, organism names, basionyms and accessions using the new spacy training set. Accession detection uses NER first but if not found then tries Regex. Post-processing then removes non-INSDC accessions.
