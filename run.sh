#!/bin/tcsh

# generate JSON for RNASEQ samples only
mkdir -p gtex_rnaseq_json
./gtex_v7_to_dats.py --smafrze=RNASEQ --output_dir=gtex_rnaseq_json
