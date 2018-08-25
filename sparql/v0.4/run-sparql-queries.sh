#!/bin/bash

tar xzvf ../releases/KC7-crosscut-metadata-v0.4.tgz
export JSON_DIR=KC7-crosscut-metadata-v0.4/data/datasets/

# takes about 1m35s using GitHub context URIs
time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public.jsonld



