#!/bin/tcsh

setenv PYTHONPATH ./

# Generate JSON for RNASEQ samples and then create BDBag
setenv VERSION 0.2
setenv EXTERNAL_ID "KC7-crosscut-metadata-v${VERSION}"
setenv EXTERNAL_DESCR "v${VERSION} release of the KC7 crosscut metadata model for GTEx v7 and TOPMed public metadata using DATS v2.2+"

# set up internal bag structure
mkdir -p $EXTERNAL_ID/docs
mkdir -p $EXTERNAL_ID/datasets

# convert public GTEx v7 RNA-SEQ metadata to DATS JSON
./bin/gtex_v7_to_dats.py --output_file=$EXTERNAL_ID/datasets/gtex_v7_rnaseq_public.json

# convert public TOPMed metadata for phs000946 to DATS JSON
# retrieve v3 variable summaries from ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/phs000946/phs000946.v3.p1/pheno_variable_summaries/ into ./phs000946.v3, then:
./bin/topmed_to_dats.py --dbgap_public_xml_path=./phs000946.v3 --output_file=$EXTERNAL_ID/datasets/TOPMed_phs000946_wgs_public.json

# convert RESTRICTED ACCESS TOPMed metadata for phs000946 to DATS JSON
# retrieve v3 variable summaries and access restricted metadata into ./phs000946.v3, then run:
# ./bin/topmed_to_dats.py --dbgap_public_xml_path=./phs000946.v3 --dbgap_protected_metadata_path=./phs000946.v3 \
#  --output_file=$EXTERNAL_ID/metadata/annotations/datasets/TOPMed_phs000946_wgs_RESTRICTED.json

# add documentation files
cp releases/ChangeLog $EXTERNAL_ID/docs/
cp RELEASE_NOTES $EXTERNAL_ID/docs/

# create BDBag 
bdbag --archive tgz \
 --source-organization 'NIH DCPPC KC7 Working Group' \
 --contact-name 'Jonathan Crabtree' \
 --contact-email 'jcrabtree@som.umaryland.edu' \
 --external-description "$EXTERNAL_DESCR" \
 --external-identifier $EXTERNAL_ID \
$EXTERNAL_ID

# validate BDBag
bdbag --validate full $EXTERNAL_ID.tgz
