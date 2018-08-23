#!/usr/bin/env python3

# Create DATS JSON description of GTEx v7 public RNA-Seq DataSet.

import argparse
from ccmm.dats.datsobj import DATSEncoder
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
    parser.add_argument('--output_file', required=True, help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    parser.add_argument('--max_output_samples', required=False, help ='Impose a limit on the number of sample Materials in the output DATS. For testing purposes only.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # Dataset for GTEx project
    gtex_dataset = ccmm.gtex.rnaseq_datasets.get_dataset_json()

    # Dataset for public RNA-Seq analysis
    rnaseq_dataset = gtex_dataset.get("hasPart")[0]

    # read metadata for subjects and samples
    subjects = ccmm.gtex.rna_extracts.read_subject_phenotypes_file(V7_SUBJECT_PHENOTYPES_FILE)
    samples = ccmm.gtex.rna_extracts.read_sample_attributes_file(V7_SAMPLE_ATTRIBUTES_FILE)

    # filter subjects by RNA-Seq smafrze
    samples = ccmm.gtex.rna_extracts.filter_samples(samples, RNASEQ_SMAFRZE)

    # link subjects to samples
    ccmm.gtex.rna_extracts.link_samples_to_subjects(samples, subjects)

    # samples
    samples_json = ccmm.gtex.rna_extracts.get_samples_json(samples, subjects)

    # option to limit number of samples in the output
    if args.max_output_samples is not None:
        samples_json = samples_json[:int(args.max_output_samples)]
        logging.warn("limiting output to " + str(len(samples_json)) + " sample(s) due to value of --max_output_samples")

    # JSON-LD id references for samples
    sample_refs_json = [ s.getIdRef() for s in samples_json ]

    # add samples and sample refs to 2nd-level Datasets
    data_subsets = rnaseq_dataset.get("hasPart")
    # add full samples JSON to the first 2nd-level Dataset
    data_subsets[0].set('isAbout', samples_json)

    # use JSON-LD id references for the rest:
    for ds in data_subsets[1:]:
        ds.set('isAbout', sample_refs_json)

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(gtex_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
