#!/usr/bin/env python3

# Create DATS JSON description of GTEx v7 public RNA-Seq DataSet.

import argparse
import ccmm.gtex.rnaseq_datasets
import ccmm.gtex.rna_extracts
import json
import logging
import os

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

V7_SUBJECT_PHENOTYPES_FILE = 'GTEx_v7_Annotations_SubjectPhenotypesDS.txt'
V7_SAMPLE_ATTRIBUTES_FILE = 'GTEx_v7_Annotations_SampleAttributesDS.txt'

RNASEQ_SMAFRZE = 'RNASEQ'

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for GTEx v7 public RNA-Seq data.')
    parser.add_argument('--output_file', default='.', help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # create top-level dataset
    rnaseq_dataset = ccmm.gtex.rnaseq_datasets.get_dataset_json()

    # read metadata for subjects and samples
    subjects = ccmm.gtex.rna_extracts.read_subject_phenotypes_file(V7_SUBJECT_PHENOTYPES_FILE)
    samples = ccmm.gtex.rna_extracts.read_sample_attributes_file(V7_SAMPLE_ATTRIBUTES_FILE)

    # filter subjects by RNA-Seq smafrze
    samples = ccmm.gtex.rna_extracts.filter_samples(samples, RNASEQ_SMAFRZE)

    # link subjects to samples
    ccmm.gtex.rna_extracts.link_samples_to_subjects(samples, subjects)

    # add samples to top-level Dataset
    samples_json = ccmm.gtex.rna_extracts.get_samples_json(samples, subjects)
    rnaseq_dataset['isAbout'] = samples_json

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(rnaseq_dataset, indent=2))

if __name__ == '__main__':
    main()
