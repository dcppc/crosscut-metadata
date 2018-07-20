#!/bin/tcsh

setenv PYTHONPATH ./

# Script to create the crosscut metadata model instance. 
#
# The public or non-access-restricted crosscut metadata model instance is a
# BDBag that contains DATS JSON-LD files that describe the metadata from the 
# following resources:
#
# 1. Public mouse C57BL/6J reference genome and human homologs from MGI/MGD.
# 2. Public GTEx v7 RNA-Seq metadata.
# 3. Public TOPMed metadata from non-access-restricted dbGaP files.
# 
# In the case of TOPMed the crosscut metadata model instance may be expanded
# to include access-restricted dbGaP metadata (see the relevant script 
# invocation below) but this expanded instance may not be publicly distributed.

setenv VERSION 0.4
setenv EXTERNAL_ID "KC7-crosscut-metadata-v${VERSION}"
setenv EXTERNAL_DESCR "v${VERSION} release of the KC7 crosscut metadata model for MGI, GTEx v7, and TOPMed public metadata using DATS v2.2+"

# set up internal bag structure
mkdir -p $EXTERNAL_ID/docs
mkdir -p $EXTERNAL_ID/datasets

## -----------------------------------------------
## Public mouse C57BL/6J reference genome
## -----------------------------------------------

# retrieve the requisite flat files from MGI/MGD:
#mkdir -p mgd-data
#cd mgd-data
#curl -O http://www.informatics.jax.org/downloads/mgigff/MGI.gff3.gz
#curl -O http://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt
#cd ..

# convert the MGI metadata to DATS JSON-LD
./bin/mgd_to_dats.py --gff3_path=mgd-data/MGI.gff3.gz --human_homologs_path=mgd-data/HOM_MouseHumanSequence.rpt --output_file=$EXTERNAL_ID/datasets/MGD_GRCm38-C57BL6J_public.json

## -----------------------------------------------
## Public GTEx v7 RNA-Seq metadata
## -----------------------------------------------

# this script expects the following two GTEx metadata files 
# (from https://www.gtexportal.org/home/datasets to be in the current working directory:
#
# GTEx_v7_Annotations_SubjectPhenotypesDS.txt
# GTEx_v7_Annotations_SampleAttributesDS.txt

./bin/gtex_v7_to_dats.py --output_file=$EXTERNAL_ID/datasets/GTEx_v7_rnaseq_public.json

## -----------------------------------------------
## Public TOPMed metadata
## -----------------------------------------------

# convert public TOPMed metadata for phs000946 to DATS JSON
# retrieve v3 variable summaries from ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/phs000946/phs000946.v3.p1/pheno_variable_summaries/ into ./phs000946.v3, then:

./bin/topmed_to_dats.py --dbgap_public_xml_path=./phs000946.v3 --output_file=$EXTERNAL_ID/datasets/TOPMed_phs000946_wgs_public.json

## -----------------------------------------------
## RESTRICTED ACCESS TOPMed metadata
## -----------------------------------------------

# convert RESTRICTED ACCESS TOPMed metadata for phs000946 to DATS JSON
# retrieve v3 variable summaries and access restricted metadata into ./phs000946.v3, then run:

# ./bin/topmed_to_dats.py --dbgap_public_xml_path=./phs000946.v3 --dbgap_protected_metadata_path=./phs000946.v3 \
#  --output_file=$EXTERNAL_ID/metadata/annotations/datasets/TOPMed_phs000946_wgs_RESTRICTED.json

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
