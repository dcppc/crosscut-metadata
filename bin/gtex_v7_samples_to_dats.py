#!/usr/bin/env python3

# Convert GTEx v7 sample metadata to DATS JSON (one file per sample.)

import argparse
import ccmm.gtex.rna_extracts
import json
import logging
import os
import sys

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

V7_SUBJECT_PHENOTYPES_FILE = 'GTEx_v7_Annotations_SubjectPhenotypesDS.txt'
V7_SAMPLE_ATTRIBUTES_FILE = 'GTEx_v7_Annotations_SampleAttributesDS.txt'

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Convert GTEx v7 metadata to DATS JSON.')
    parser.add_argument('--output_dir', default='.', help ='Destination directory for DATS JSON files.')
    parser.add_argument('--smafrze', default=None, help ='Analysis freeze. One of RNASEQ,WGS,WES,OMNI,EXCLUDE.')
    parser.add_argument('--print_sample_histogram', dest='print_sample_histogram', action='store_true', default=False, help ='Print histogram of samples per subject.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # read metadata for subjects and samples
    subjects = ccmm.gtex.rna_extracts.read_subject_phenotypes_file(V7_SUBJECT_PHENOTYPES_FILE)
    samples = ccmm.gtex.rna_extracts.read_sample_attributes_file(V7_SAMPLE_ATTRIBUTES_FILE)

    # filter subjects by smafrze
    samples = ccmm.gtex.rna_extracts.filter_samples(samples, args.smafrze)

    # link subjects to samples
    ccmm.gtex.rna_extracts.link_samples_to_subjects(samples, subjects)

    # print subject sample count histogram
    if args.print_sample_histogram:
        ccmm.gtex.rna_extracts.print_subject_sample_count_histogram(samples)
        sys.exit(0)

    # produce DATS JSON file for each sample
    ccmm.gtex.rna_extracts.write_samples_json(subjects, samples, args.output_dir)

if __name__ == '__main__':
    main()
