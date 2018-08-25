#!/bin/bash

# Example showing parse speed improvement using locally cached context files.

#tar xzvf ../releases/KC7-crosscut-metadata-v0.4.tgz
export JSON_DIR=KC7-crosscut-metadata-v0.4/data/datasets/

# download context files locally
git clone git@github.com:datatagsuite/context.git

# rewrite JSON-LD files to use local contexts
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public.jsonld >$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_rnaseq_public.jsonld >$JSON_DIR/GTEx_v7_rnaseq_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public.jsonld >$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_dbGaP_public.jsonld >$JSON_DIR/GTEx_v7_dbGaP_public_local_contexts.jsonld

# takes about 2-3 seconds using local context files (vs ~95 seconds using GitHub context URIs)
time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public_local_contexts.jsonld
# takes about 9-10 seconds using local context files
time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public_local_contexts.jsonld
# takes about 6-7 seconds using local context files
time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/GTEx_v7_dbGaP_public_local_contexts.jsonld
# takes about 6-8 minutes using local context files
#time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/GTEx_v7_rnaseq_public_local_contexts.jsonld
