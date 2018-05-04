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

# landing page for public RNA-Seq datasets
GTEX_DATASETS_URL = "https://www.gtexportal.org/home/datasets"

# "count" from Statistical Methods Ontology
COUNT_TYPE = OrderedDict([("value", "count"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000047")])

RNA_SEQ_QC = OrderedDict([
        ("@type", "Software"),
        ("name", "RNASeQC"),
        ("version", "v1.1.8")])

# gene read counts Dimension
READ_COUNTS_DIM = OrderedDict([
        ("@type", "Dimension"),
        # "sequence read count" from Statistical Methods Ontology
        # TODO - strictly speaking the definition of this term says that it applies to a DNA sequencing assay, not an RNA sequencing assay
        ("name", OrderedDict([("value", "gene read counts"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000064")])),
        ("description", "gene read counts"),
        ("types", [COUNT_TYPE])
        ])

# junction count Dimension
JUNCTION_COUNT_DIM = OrderedDict([
        ("@type", "Dimension"),
        # "sequence read count" from Statistical Methods Ontology
        ("name", OrderedDict([("value", "Junction read counts"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000064")])),
        ("description", "Junction read counts"),
        ("types", [COUNT_TYPE])
        ])

# STAR Aligner
STAR = OrderedDict([
        ("@type", "Software"),
        ("name", "STAR Aligner"),
        ("version", "v2.4.2a")
        ])

# transcript TPM Dimension
TRANSCRIPT_TPM_DIM = OrderedDict([
        ("@type", "Dimension"),
        # "sequence read count" from Statistical Methods Ontology
        ("name", OrderedDict([("value", "Transcripts Per Kilobase Million"), ("valueIRI", "")])),
        ("description", "Transcripts Per Kilobase Million"),
        ("types", [COUNT_TYPE])
        ])

# RSEM Software
RSEM = OrderedDict([
        ("@type", "Software"),
        ("name", "RSEM"),
        ("version", "1.2.22")
        ])

# Public RNA-Seq datasets listed at https://www.gtexportal.org/home/datasets
RNASEQ_DATASETS = [
    { "descr": "Gene read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_reads.gct.gz", "measures": [READ_COUNTS_DIM], "uses": [] },
    { "descr": "Gene TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_tpm.gct.gz", "measures": [], "uses": [] },
    # TODO - this file was derived directly from the preceding one
    { "descr": "Tissue median TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_median_tpm.gct.gz", "measures": [], "uses": [] },
    { "descr": "Junction read counts.", "file": "GTEx_Analysis_2016-01-15_v7_STARv2.4.2a_junctions.gct.gz", "measures": [JUNCTION_COUNT_DIM], "uses": [STAR] },
    { "descr": "Transcript read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RSEMv1.2.22_transcript_expected_count.txt.gz", "measures": [], "uses": [] },
    { "descr": "Transcript TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RSEMv1.2.22_transcript_tpm.txt.gz", "measures": [TRANSCRIPT_TPM_DIM], "uses": [RSEM] },
    { "descr": "Exon read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_exon_reads.txt.gz", "measures": [], "uses": [] }
]

DB_GAP = OrderedDict([("@type", "DataRepository"), ("name", "dbGaP")])

GTEX_CONSORTIUM = OrderedDict([
        ("@type", "Organization"),
        ("name", "The Genotype-Tissue Expression (GTEx) Consortium"),
        ("abbreviation", "The GTEx Consortium"),
        ])

# TODO - where did  2017-06-30 release date come from?
GTEX_V7_RELEASE_DATE = OrderedDict([
        ("date", "2017-06-30"), 
        ("type", {"value": "release date"})
        ])

GTEX_V7_TYPES = [OrderedDict([
            # Ontology for Biomedical Investigations / transcription profiling assay
            ("information", OrderedDict([("value", "transcription profiling"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000424")])),
            # Ontology for Biomedical Investigations / RNA-seq assay
            ("method", OrderedDict([("value", "RNA-seq assay"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0001271")])),
            # Ontology for Biomedical Investigations / Illumina
            ("platform", OrderedDict([("value", "Illumina"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000759")]))
            ])]

# ------------------------------------------------------
# Dataset JSON
# ------------------------------------------------------

def write_datasets_json(output_file):
    # individual RNA-Seq datasets/files
    rnaseq_data_subsets = [];

    # create DATS Dataset for each RNA-Seq data product
    for dss in RNASEQ_DATASETS:
        descr = dss["descr"]
        file = dss["file"]
        measures = dss["measures"]
        uses = dss["uses"]

        subset = OrderedDict([
                ("@type", "Dataset"),
                ("identifier",  OrderedDict([
                            ("@type", "Identifier"),
                            ("identifier", "GTEx_Analysis_2016-01-15_v7_RNA-SEQ_" + file)
                            ])),
                ("version", "v7"),
                ("dates", [GTEX_V7_RELEASE_DATE]),
                ("title", "GTEx v7 RNA-Seq Analysis, " + descr),
                ("storedIn", DB_GAP),
                ("types", GTEX_V7_TYPES),
                ("creators", GTEX_CONSORTIUM),
                # TODO - where does the actual filename belong?
                ("distributions", [OrderedDict([
                                ("@type", "DatasetDistribution"),
                                ("access", OrderedDict([
                                            ("@type", "Access"),
                                            ("landingPage", GTEX_DATASETS_URL)
                                            ]))
                                ])]),
                # TODO - "measures" does not appear in DATS v2.2 dataset_schema.json?
                ("measures", measures),
                ("uses", uses)
                ])
        rnaseq_data_subsets.append(subset)

    # parent RNA-Seq dataset
    parent_rnaseq_dataset = OrderedDict([
            ("@type", "Dataset"),
            ("identifier",  OrderedDict([
                        ("@type", "Identifier"),
                        ("identifier", "GTEx_Analysis_2016-01-15_v7_RNA-SEQ")
                        ])),
            ("version", "v7"),
            ("dates", [GTEX_V7_RELEASE_DATE]),
            ("title",  "GTEx v7 RNA-Seq Analysis"),
            ("storedIn", DB_GAP),
            ("types", GTEX_V7_TYPES),
            ("creators", GTEX_CONSORTIUM),
            ("distributions", [OrderedDict([
                                    ("@type", "DatasetDistribution"),
                                    ("access", OrderedDict([
                                                ("@type", "Access"),
                                                ("landingPage", GTEX_DATASETS_URL)
                                                ]))
                                    ])]),
            ("uses", [RNA_SEQ_QC]),
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
