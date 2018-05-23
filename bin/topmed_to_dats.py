#!/usr/bin/env python3

# Create DATS JSON description of TOPMed public data.

import argparse
from ccmm.dats.datsobj import DATSEncoder
import ccmm.topmed.wgs_datasets
#import ccmm.topmed.dna_extracts
import json
import logging
import os

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for TOPMed public metadata.')
    parser.add_argument('--output_file', default='.', help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # create top-level dataset
    topmed_dataset = ccmm.topmed.wgs_datasets.get_dataset_json()

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(topmed_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
