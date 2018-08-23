#!/bin/tcsh

setenv PYTHONPATH ./

# Script to create the crosscut metadata model instance. 
#
# The public or non-access-restricted crosscut metadata model instance is a
# BDBag that contains DATS JSON-LD files that describe the metadata from the 
# following resources:
#
# 1. Public GTEx v7 metadata from dbGaP and the GTEx portal.
# 2. Public TOPMed metadata from non-access-restricted dbGaP files.
# 
# In the case of both GTEx and TOPMed the crosscut metadata model instance may 
# be expanded to include access-restricted dbGaP metadata (see the relevant script 
# invocation below) but this expanded instance may not be publicly distributed.

setenv VERSION 0.4
setenv EXTERNAL_ID "KC7-crosscut-metadata-v${VERSION}"
setenv EXTERNAL_DESCR "v${VERSION} release of the KC7 crosscut metadata model for GTEx v7 and TOPMed public metadata using DATS v2.2+"

# set up internal bag structure
mkdir -p $EXTERNAL_ID/docs
mkdir -p $EXTERNAL_ID/datasets

## -----------------------------------------------
## Public GTEx v7 RNA-Seq metadata
## -----------------------------------------------

# This script requires the following two GTEx metadata files 
# (from https://www.gtexportal.org/home/datasets to be in the current working directory:
#
# GTEx_v7_Annotations_SubjectPhenotypesDS.txt
# GTEx_v7_Annotations_SampleAttributesDS.txt

./bin/gtex_v7_to_dats.py --output_file=$EXTERNAL_ID/datasets/GTEx_v7_rnaseq_public.jsonld 

# limit to 20 samples to create smaller file for test purposes
./bin/gtex_v7_to_dats.py --output_file=$EXTERNAL_ID/datasets/GTEx_v7_rnaseq_20_SAMPLES_public.jsonld --max_output_samples=20

## -----------------------------------------------
## Public GTEx v7 dbGaP metadata
## -----------------------------------------------

# Convert public dbGaP metadata for GTEx to DATS JSON.
#
# First retrieve the pheno_variable_summaries files for GTEx into a local directory:
#  1. create local directory dbgap-data if it does not already exist
#  2. pull ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/phs000424/phs000424.v7.p2/pheno_variable_summaries/ into dbgap-data/phs000424.v7.p2
#  3. run the command below

./bin/dbgap_gtex_to_dats.py --dbgap_public_xml_path=./dbgap-data/phs000424.v7.p2 --output_file=$EXTERNAL_ID/datasets/GTEx_v7_dbGaP_public.jsonld

## -----------------------------------------------
## Public TOPMed metadata
## -----------------------------------------------

# Convert public dbGaP metadata for selected TOPMed studies to DATS JSON.
#
# First retrieve the pheno_variable_summaries from the desired TOPMed studies into a local directory: 
#  1. create local directory dbgap-data if it does not already exist
#  2. pull ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/phs001024/phs001024.v3.p1/pheno_variable_summaries/ into dbgap-data/phs001024.v3.p1
#  3. pull ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/phs000951/phs000951.v2.p2/pheno_variable_summaries/ into dbgap-data/phs000951.v2.p2
#  4. pull ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/phs000179/phs000179.v5.p2/pheno_variable_summaries/ into dbgap-data/phs000179.v5.p2
#  5. run the command below

./bin/topmed_to_dats.py --dbgap_accession_list='phs001024.v3.p1,phs000951.v2.p2,phs000179.v5.p2' \
  --dbgap_public_xml_path=./dbgap-data \
  --output_file=$EXTERNAL_ID/datasets/TOPMed_phs000951_phs000946_phs001024_wgs_public.jsonld

## -----------------------------------------------
## RESTRICTED ACCESS TOPMed metadata
## -----------------------------------------------

# Convert RESTRICTED ACCESS TOPMed metadata to DATS JSON.

#./bin/topmed_to_dats.py --dbgap_accession_list='phs001024.v3.p1,phs000951.v2.p2,phs000179.v5.p2' \
#  --dbgap_public_xml_path=./dbgap-data \
#  --dbgap_protected_metadata_path=./restricted-access-dbgap-data \
#  --output_file=$EXTERNAL_ID/datasets/TOPMed_phs000951_phs000946_phs001024_wgs_RESTRICTED.jsonld

## -----------------------------------------------
## Add documentation
## -----------------------------------------------

cp releases/ChangeLog $EXTERNAL_ID/docs/
cp RELEASE_NOTES $EXTERNAL_ID/docs/

## -----------------------------------------------
## Create BDBag
## -----------------------------------------------

bdbag --archive tgz \
 --source-organization 'NIH DCPPC KC7 Working Group' \
 --contact-name 'Jonathan Crabtree' \
 --contact-email 'jcrabtree@som.umaryland.edu' \
 --external-description "$EXTERNAL_DESCR" \
 --external-identifier $EXTERNAL_ID \
$EXTERNAL_ID

## -----------------------------------------------
## Validate BDBag
## -----------------------------------------------

bdbag --validate full $EXTERNAL_ID.tgz
