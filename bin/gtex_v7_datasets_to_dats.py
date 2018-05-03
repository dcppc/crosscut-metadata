#!/usr/bin/env python3

# Create DATS JSON description of GTEx v7 DataSets

import argparse
from collections import OrderedDict
import csv
import json
import logging
import os
import re
import sys

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

# Public RNA-Seq datasets listed at https://www.gtexportal.org/home/datasets
RNASEQ_DATASETS = [
    { "descr": "Gene read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_reads.gct.gz" },
    { "descr": "Gene TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_tpm.gct.gz" },
    # TODO - this file was derived directly from the preceding one
    { "descr": "Tissue median TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_median_tpm.gct.gz" },
    { "descr": "Junction read counts.", "file": "GTEx_Analysis_2016-01-15_v7_STARv2.4.2a_junctions.gct.gz" },
    { "descr": "Transcript read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RSEMv1.2.22_transcript_expected_count.txt.gz" },
    { "descr": "Transcript TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RSEMv1.2.22_transcript_tpm.txt.gz" },
    { "descr": "Exon read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_exon_reads.txt.gz" }
]

DB_GAP = OrderedDict([("@type", "DataRepository"), ("name", "dbGaP")])

GTEX_CONSORTIUM = OrderedDict([
        ("@type", "Organization"),
        ("name", "The Genotype-Tissue Expression (GTEx) Consortium"),
        ("abbreviation", "The GTEx Consortium"),
        ])

# ------------------------------------------------------
# Error handling
# ------------------------------------------------------

def fatal_error(err_msg):
    logging.fatal(err_msg)
    sys.exit(1)

def fatal_parse_error(err_msg, file, lnum):
    msg = err_msg + " at line " + str(lnum) + " of " + file
    fatal_error(msg)

# ------------------------------------------------------
# Dataset JSON
# ------------------------------------------------------

def write_datasets_json(output_file):
    # individual RNA-Seq datasets/files
    rnaseq_data_subsets = [];

    # create DATS Dataset for each RNA-Seq data product
    for dss in RNASEQ_DATASETS:
        subset = OrderedDict([])
        rnaseq_data_subsets.append(subset)

    # parent RNA-Seq dataset
    parent_rnaseq_dataset = OrderedDict([
            ("@type", "Dataset"),
            ("identifier",  OrderedDict([
                        ("@type", "Identifier"),
                        ("identifier", "GTEx_Analysis_2016-01-15_v7_RNA-SEQ")
                        ])),
            ("version", "v7"),
             # TODO - where did this 2017-06-30 release date come from?
            ("dates", [OrderedDict([
                            ("date", "2017-06-30"), 
                            ("type", {"value": "release date"})])]),
            ("title",  "GTEx v7 RNA-Seq Analysis"),
            ("storedIn", DB_GAP),
            ("types", [OrderedDict([
                            ("information", {"value": "transcription_profiling"}),
                            ("method", {"value": "nucleotide sequencing"}),
                            ("platform", {"value": "Illumina"})
                       ])]),
            ("creators", GTEX_CONSORTIUM),
            ("distributions", [OrderedDict([
                                    ("@type", "DatasetDistribution"),
                                    ("access", OrderedDict([
                                                ("@type", "Access"),
                                                ("landingPage", "https://www.gtexportal.org/home/datasets")
                                                ]))
                                    ])]),
            ("hasPart", rnaseq_data_subsets)
            ])

    # TODO - add 'licenses', 'availability', 'dimensions', 'primaryPublications', 'isAbout' (linking to ~12K sample materials)

    with open(output_file, mode="w") as jf:
        jf.write(json.dumps(parent_rnaseq_dataset, indent=2))

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

    # produce DATS JSON file
    datasets_file = os.path.join(args.output_dir, "rnaseq.json")
    write_datasets_json(datasets_file)

if __name__ == '__main__':
    main()
