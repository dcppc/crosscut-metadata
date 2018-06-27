#!/usr/bin/env python3

# Create DATS JSON description of Mouse Genome Database reference genome and (some) associated annotation.
# At minimum it will include genes, gene names, and human orthologs.

import argparse
from ccmm.dats.datsobj import DATSEncoder
import ccmm.mgd.ref_genome_dataset
import json
import logging
import os
import re
import sys

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for Mouse Genome Database reference genome and annotation.')
    parser.add_argument('--output_file', required=True, help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    parser.add_argument('--gff3_path', required=True, help ='Path to MGD GFF3 file.')
    parser.add_argument('--human_homologs_path', required=True, help ='Path to MGD HOM_MouseHumanSequence.rpt file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # create top-level dataset
    mgd_dataset = ccmm.mgd.ref_genome_dataset.get_dataset_json(args.gff3_path, args.human_homologs_path)

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(mgd_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()



