#!/usr/bin/env python3

# Create DATS JSON description of GTEx v7 DataSets

import argparse
from ccmm.dats.datsobj import DATSEncoder
import ccmm.gtex.rnaseq_datasets
import json
import logging
import os

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for GTEx v7 RNA-Seq data files.')
    parser.add_argument('--output_dir', default='.', help ='Destination directory for DATS JSON files.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # create top-level dataset
    rnaseq_dataset = ccmm.gtex.rnaseq_datasets.get_dataset_json()

    # write Dataset to DATS JSON file
    rnaseq_file = os.path.join(args.output_dir, "rnaseq.json")

    with open(rnaseq_file, mode="w") as jf:
        jf.write(json.dumps(rnaseq_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
