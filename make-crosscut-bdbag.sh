#!/bin/tcsh

setenv PYTHONPATH ./

# Generate JSON for RNASEQ samples and then create BDBag
setenv VERSION 0.2
setenv EXTERNAL_ID "KC7-crosscut-metadata-v${VERSION}-internal"
setenv EXTERNAL_DESCR "Internal-only v${VERSION} release of the KC7 crosscut metadata model for GTEx v7 public metadata using DATS v2.2+"

# set up internal bag structure
mkdir -p $EXTERNAL_ID/docs
mkdir -p $EXTERNAL_ID/data
mkdir -p $EXTERNAL_ID/metadata
mkdir -p $EXTERNAL_ID/metadata/annotations/datasets

# convert public GTEx v7 RNA-SEQ metadata to DATS JSON
./bin/gtex_v7_to_dats.py --output_dir=$EXTERNAL_ID/metadata/annotations/datasets
exit

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

# not supported in bdbag 1.2.4 (the most recent):
# --author-orcid '0000-0002-7286-5690' \

# validate BDBag
bdbag --validate full $EXTERNAL_ID.tgz
