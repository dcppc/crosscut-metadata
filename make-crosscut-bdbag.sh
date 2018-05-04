#!/bin/tcsh

# Generate JSON for RNASEQ samples and then create BDBag
setenv VERSION 0.1
setenv EXTERNAL_ID "KC7-crosscut-metadata-v${VERSION}-internal"
setenv EXTERNAL_DESCR "Internal-only v${VERSION} release of the KC7 crosscut metadata model for GTEx v7 public metadata using DATS v2.2+"

# convert public GTEx v7 metadata to DATS JSON
mkdir -p $EXTERNAL_ID/samples
./bin/gtex_v7_to_dats.py --smafrze=RNASEQ --output_dir=$EXTERNAL_ID/samples  >all-samples.json

# create/add DATS JSON for RNA-Seq Datasets
mkdir -p $EXTERNAL_ID/datasets
./bin/gtex_v7_datasets_to_dats.py --output_dir=$EXTERNAL_ID/datasets

# add documentation files
mkdir -p $EXTERNAL_ID/docs
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

