#!/bin/bash

# Example showing parse speed improvement using locally cached context files
# and query speed improvement using RDFLib API calls instead of RDFLib
# SPARQL query evaluator.

#tar xzvf ../../releases/KC7-crosscut-metadata-v0.7.tgz
export JSON_DIR=KC7-crosscut-metadata-v0.7/data/datasets/
# include patched/hacked rdflib_jsonld
export PYTHONPATH=/home/jcrabtree/git/crosscut-metadata/python

# download context files locally
#git clone git@github.com:datatagsuite/context.git

# rewrite JSON-LD files to use local contexts
#perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_public.jsonld >$JSON_DIR/GTEx_v7_public_local_contexts.jsonld
#perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public.jsonld >$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public_local_contexts.jsonld

export TOPMED_DATS=$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public_local_contexts.jsonld
export GTEX_DATS=$JSON_DIR/GTEx_v7_public_local_contexts.jsonld

# ------------------------------------------------------
# list 2nd-level Datasets
# ------------------------------------------------------

# ~1.5 seconds on macbook
# ~3 seconds on kamek w/ rdflib_jsonld patch (30-65 without)
#time ./rdflib_list_2nd_level_datasets.py --dats_file=$TOPMED_DATS

# ~3 minutes
# 5m12s on kamek w/ rdflib_jsonld patch 
#time ./rdflib_list_2nd_level_datasets.py --dats_file=$GTEX_DATS

# ------------------------------------------------------
# list dbGaP study variables
# ------------------------------------------------------

# ~5 seconds
time ./rdflib_list_dataset_variables.py --dats_file=$TOPMED_DATS
# ~1.5 seconds
time ./rdflib_list_dataset_variables.py --dats_file=$TOPMED_DATS --dataset_id='phs001024.v3.p1'
# ~3 minutes
time ./rdflib_list_dataset_variables.py --dats_file=$GTEX_DATS



