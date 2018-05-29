#!/bin/tcsh

setenv PYTHONPATH ./

# Generate JSON for RNASEQ samples and then create BDBag
setenv VERSION 0.2
setenv EXTERNAL_ID "KC7-crosscut-ro-metadata-v${VERSION}-internal"
setenv EXTERNAL_DESCR "Internal-only v${VERSION} release of the KC7 crosscut metadata model for GTEx v7 public metadata using DATS v2.2+"

# set up internal bag structure
mkdir -p $EXTERNAL_ID/docs
#mkdir -p $EXTERNAL_ID/data
#mkdir -p $EXTERNAL_ID/metadata
#mkdir -p $EXTERNAL_ID/metadata/annotations/datasets
mkdir -p metadata/annotations/datasets

# convert public GTEx v7 RNA-SEQ metadata to DATS JSON
./bin/gtex_v7_to_dats.py --output_file=metadata/annotations/datasets/gtex_v7_rnaseq.json

# convert public TOPMed metadata for phs000946 to DATS JSON
# retrieve v3 variable summaries from ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/phs000946/phs000946.v3.p1/pheno_variable_summaries/ into ./phs000946.v3, then:
./bin/topmed_to_dats.py --dbgap_public_xml_path=./phs000946.v3 --output_file=metadata/annotations/datasets/TOPMed_phs000946_wgs.json

# convert RESTRICTED ACCESS TOPMed metadata for phs000946 to DATS JSON
# ./bin/topmed_to_dats.py --dbgap_public_xml_path=./phs000946.v3 --dbgap_protected_metadata_path=./phs000946.v3 \
#  --output_file=$EXTERNAL_ID/metadata/annotations/datasets/TOPMed_phs000946_wgs_RESTRICTED.json

# add documentation files
cp releases/ChangeLog $EXTERNAL_ID/docs/
cp RELEASE_NOTES $EXTERNAL_ID/docs/

# create ro-BDBag (requires bdbag 1.3.0 or later)
bdbag --archive tgz \
 --source-organization 'NIH DCPPC KC7 Working Group' \
 --contact-name 'Jonathan Crabtree' \
 --contact-email 'jcrabtree@som.umaryland.edu' \
 --contact-orcid '0000-0002-7286-5690' \
 --external-description "$EXTERNAL_DESCR" \
 --external-identifier $EXTERNAL_ID \
 --ro-metadata-file ./ro_metadata.json \
$EXTERNAL_ID

# validate BDBag
bdbag --validate full $EXTERNAL_ID.tgz
