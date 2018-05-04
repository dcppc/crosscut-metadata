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

## Statistical Methods Ontology
# "count"
COUNT_TYPE = OrderedDict([("value", "count"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000047")])

# "sequence read count"
# TODO - strictly speaking the definition of this term says that it applies to a DNA sequencing assay, not an RNA sequencing assay
# TODO - also not clear if different names can be associated with the same valueIRI (different from each other and different from the name of the indicated term)
GENE_READ_COUNT_NAME = OrderedDict([("value", "Gene read counts"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000064")])
TRANSCRIPT_READ_COUNT_NAME = OrderedDict([("value", "Transcript read counts"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000064")])
EXON_READ_COUNT_NAME = OrderedDict([("value", "Exon read counts"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000064")])
JUNCTION_READ_COUNT_NAME = OrderedDict([("value", "Junction read counts"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000064")])

## Ontology for Biomedical Investigations
# "transcription profiling assay"
TRANSCRIPT_PROFILING_TYPE = OrderedDict([("value", "transcription profiling"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000424")])
# "RNA-seq assay"
RNASEQ_ASSAY_TYPE = OrderedDict([("value", "RNA-seq assay"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0001271")])
# "Illumina"
ILLUMINA_TYPE = OrderedDict([("value", "Illumina"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000759")])

# documentation for earlier version at https://data.broadinstitute.org/cancer/cga/tools/rnaseqc/RNA-SeQC_Help_v1.1.2.pdf
RNA_SEQ_QC = OrderedDict([
        ("@type", "Software"),
        ("name", "RNASeQC"),
        ("version", "v1.1.8")])

# gene read counts Dimension
GENE_READ_COUNTS_DIM = OrderedDict([
        ("@type", "Dimension"),
        ("name", GENE_READ_COUNT_NAME),
        ("description", "gene read counts"),
        ("types", [COUNT_TYPE])
        ])

TRANSCRIPT_READ_COUNTS_DIM = OrderedDict([
        ("@type", "Dimension"),
        ("name", TRANSCRIPT_READ_COUNT_NAME),
        ("description", "transcript read counts"),
        ("types", [COUNT_TYPE])
        ])

EXON_READ_COUNTS_DIM = OrderedDict([
        ("@type", "Dimension"),
        ("name", EXON_READ_COUNT_NAME),
        ("description", "exon read counts"),
        ("types", [COUNT_TYPE])
        ])

# junction count Dimension
JUNCTION_COUNT_DIM = OrderedDict([
        ("@type", "Dimension"),
        # TODO - is there a more appropriate ontology term for this?
        ("name", JUNCTION_READ_COUNT_NAME),
        ("description", "Junction read counts"),
        ("types", [COUNT_TYPE])
        ])

# gene TPM Dimension
# TODO - is this transcripts per _gene_ kilobase million?
GENE_TPM_DIM = OrderedDict([
        ("@type", "Dimension"),
        ("name", OrderedDict([("value", "Transcripts Per Kilobase Million"), ("valueIRI", "")])),
        ("description", "Transcripts Per Kilobase Million"),
        ("types", [COUNT_TYPE])
        ])

TISSUE_MEDIAN_TPM_DIM = OrderedDict([
        ("@type", "Dimension"),
        ("name", OrderedDict([("value", "Tissue Median Transcripts Per Kilobase Million"), ("valueIRI", "")])),
        ("description", "Tissue Median Transcripts Per Kilobase Million"),
        ("types", [COUNT_TYPE])
        ])

# transcript TPM Dimension
TRANSCRIPT_TPM_DIM = OrderedDict([
        ("@type", "Dimension"),
        ("name", OrderedDict([("value", "Transcripts Per Kilobase Million"), ("valueIRI", "")])),
        ("description", "Transcripts Per Kilobase Million"),
        ("types", [COUNT_TYPE])
        ])

# STAR Aligner
STAR = OrderedDict([
        ("@type", "Software"),
        ("name", "STAR Aligner"),
        ("version", "v2.4.2a")
        ])

# RSEM Software
RSEM = OrderedDict([
        ("@type", "Software"),
        ("name", "RSEM"),
        ("version", "1.2.22")
        ])

# Public RNA-Seq datasets listed at https://www.gtexportal.org/home/datasets
RNASEQ_DATASETS = [
    { "descr": "Gene read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_reads.gct.gz", 
      "measures": [GENE_READ_COUNTS_DIM], "uses": [RNA_SEQ_QC] },
    { "descr": "Gene TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_tpm.gct.gz", 
      "measures": [GENE_TPM_DIM], "uses": [RNA_SEQ_QC] },
    # TODO - this file was derived directly from the preceding one
    { "descr": "Tissue median TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_median_tpm.gct.gz", 
      "measures": [TISSUE_MEDIAN_TPM_DIM], "uses": [RNA_SEQ_QC] },
    { "descr": "Junction read counts.", "file": "GTEx_Analysis_2016-01-15_v7_STARv2.4.2a_junctions.gct.gz", 
      "measures": [JUNCTION_COUNT_DIM], "uses": [STAR] },
    { "descr": "Transcript read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RSEMv1.2.22_transcript_expected_count.txt.gz", 
      "measures": [TRANSCRIPT_READ_COUNTS_DIM], "uses": [RSEM] },
    { "descr": "Transcript TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RSEMv1.2.22_transcript_tpm.txt.gz", 
      "measures": [TRANSCRIPT_TPM_DIM], "uses": [RSEM] },
    { "descr": "Exon read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_exon_reads.txt.gz", 
      "measures": [EXON_READ_COUNTS_DIM], "uses": [RNA_SEQ_QC] }
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
            ("information", TRANSCRIPT_PROFILING_TYPE),
            ("method", RNASEQ_ASSAY_TYPE),
            ("platform", ILLUMINA_TYPE)
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
                ("creators", [GTEX_CONSORTIUM]),
                # TODO - where does the actual filename belong?
                ("distributions", [OrderedDict([
                                ("@type", "DatasetDistribution"),
                                ("access", OrderedDict([
                                            ("@type", "Access"),
                                            ("landingPage", GTEX_DATASETS_URL)
                                            ]))
                                ])]),

                # TODO - 'measures' and 'uses' belong in DataAnalysis, not Dataset?
#                ("measures", measures),
#                ("uses", uses)
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
            ("creators", [GTEX_CONSORTIUM]),
            ("distributions", [OrderedDict([
                                    ("@type", "DatasetDistribution"),
                                    ("access", OrderedDict([
                                                ("@type", "Access"),
                                                ("landingPage", GTEX_DATASETS_URL)
                                                ]))
                                    ])]),
            # TODO - 'measures' and 'uses' belong in DataAnalysis, not Dataset?
#            ("uses", [RNA_SEQ_QC]),
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
