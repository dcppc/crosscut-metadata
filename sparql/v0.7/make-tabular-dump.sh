#!/bin/bash

# Create tab-delimited dump of public GTEx metadata from DATS JSON-LD document.

# It is recommended to use the "local contexts" version of the GTEx
# JSON-LD file as created in the run-sparql-queries-faster.sh script:

export JSON_DIR=KC7-crosscut-metadata-v0.7/data/datasets/
export GTEX_DATS=$JSON_DIR/GTEx_v7_public_local_contexts.jsonld

time ./rdflib_tabular_dump.py --dats_file=$GTEX_DATS > GTEx_v7_public.tab.txt
