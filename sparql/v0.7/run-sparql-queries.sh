#!/bin/bash

tar xzvf ../../releases/KC7-crosscut-metadata-v0.7.tgz
export JSON_DIR=KC7-crosscut-metadata-v0.7/data/datasets/
export TOPMED_DATS=$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public.jsonld

# Example SPARQL queries using RDFLib.

# ------------------------------------------------------
# list 2nd-level Datasets
# ------------------------------------------------------

# SPARQL 
#time ./sparql_list_2nd_level_datasets.py --dats_file=$TOPMED_DATS
# Direct RDFLib access
time ./rdflib_list_2nd_level_datasets.py --dats_file=$TOPMED_DATS
exit

# ------------------------------------------------------
# list dbGaP study variables
# ------------------------------------------------------

# retrieve all variables
# SPARQL
time ./sparql_list_dataset_variables.py --dats_file=$TOPMED_DATS
# Direct RDFLib access
time ./rdflib_list_dataset_variables.py --dats_file=$TOPMED_DATS

# retrieve variables from a specific study
# SPARQL
time ./sparql_list_dataset_variables.py --dats_file=$TOPMED_DATS --dataset_id='phs001024.v3.p1'
# Direct RDFLib access
time ./rdflib_list_dataset_variables.py --dats_file=$TOPMED_DATS --dataset_id='phs001024.v3.p1'

