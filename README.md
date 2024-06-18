# IJSEM-webscraper

Jupyter notebook webscraper (selenium and beautifulsoup) designed to take the content of the weekly html email sent by IJSEM. Open the link to each publication and extract the organism name, accession numbers and type strain information. This is then compared to what NCBI taxonomy has with srcchk. NOTE use of srcchk requires linux to access this internal NCBI tool. The outputs are compared in pandas looking for differing organism names. Final output is an excel file to allow taxonomy updates. 
If accessions or strains are not found, these will be blank in the dataframe. Possible causes of this are html text blocks (Author Notes or Abstract) being missing in the publication or the search strings being missing in the Author Notes or Abstract text. These situations require manual inspection. 
Ongoing improvement hopes to make the strain matching more accurate. 
Publications reporting multiple organism names are found, however future improvement is needed to accurately match the strain names and accessions with each organism name. 
May eventually convert this to standard .py script executable by linux command line. 
