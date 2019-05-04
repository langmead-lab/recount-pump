for f in experiment run study submission sample common package analysis; do
   wget "https://www.ncbi.nlm.nih.gov/viewvc/v1/trunk/sra/doc/SRA/SRA.${f}.xsd?view=co" -O SRA.${f}.xsd 
done
