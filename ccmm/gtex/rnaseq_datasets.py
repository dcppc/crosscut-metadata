#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
from collections import OrderedDict
import json
import logging
import sys
import urllib.request

# dbGaP landin page for GTEx
GTEX_DB_GAP_URL = "https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?study_id=phs000424.v7.p2"

GTEX_DB_GAP_ID = "phs000424.v7.p2"

# landing page for public RNA-Seq datasets
GTEX_DATASETS_URL = "https://www.gtexportal.org/home/datasets"

# KC2-generated GUIDs for the public RNA-Seq datasets
GTEX_DATASETS_GUIDS_URL = "https://api.datacite.org/works?data-center-id=datacite.gtex"

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
# "DNA sequencing"
DNA_SEQUENCING_TYPE = OrderedDict([("value", "DNA sequencing"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000626")])
# "whole genome sequencing assay"
WGS_ASSAY_TYPE = OrderedDict([("value", "whole genome sequencing assay"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002117")])

# documentation for earlier version at https://data.broadinstitute.org/cancer/cga/tools/rnaseqc/RNA-SeQC_Help_v1.1.2.pdf
RNA_SEQ_QC = DatsObj("Software", [
        ("name", "RNASeQC"),
        ("version", "v1.1.8")])

# gene read counts Dimension
GENE_READ_COUNTS_DIM = DatsObj("Dimension", [
        ("name", GENE_READ_COUNT_NAME),
        ("description", "gene read counts"),
        ("types", [COUNT_TYPE])
        ])

TRANSCRIPT_READ_COUNTS_DIM = DatsObj("Dimension", [
        ("name", TRANSCRIPT_READ_COUNT_NAME),
        ("description", "transcript read counts"),
        ("types", [COUNT_TYPE])
        ])

EXON_READ_COUNTS_DIM = DatsObj("Dimension", [
        ("name", EXON_READ_COUNT_NAME),
        ("description", "exon read counts"),
        ("types", [COUNT_TYPE])
        ])

# junction count Dimension
JUNCTION_COUNT_DIM = DatsObj("Dimension", [
        # TODO - is there a more appropriate ontology term for this?
        ("name", JUNCTION_READ_COUNT_NAME),
        ("description", "Junction read counts"),
        ("types", [COUNT_TYPE])
        ])

# gene TPM Dimension
# TODO - is this transcripts per _gene_ kilobase million?
GENE_TPM_DIM = DatsObj("Dimension", [
        ("name", OrderedDict([("value", "Transcripts Per Kilobase Million"), ("valueIRI", "")])),
        ("description", "Transcripts Per Kilobase Million"),
        ("types", [COUNT_TYPE])
        ])

TISSUE_MEDIAN_TPM_DIM = DatsObj("Dimension", [
        ("name", OrderedDict([("value", "Tissue Median Transcripts Per Kilobase Million"), ("valueIRI", "")])),
        ("description", "Tissue Median Transcripts Per Kilobase Million"),
        ("types", [COUNT_TYPE])
        ])

# transcript TPM Dimension
TRANSCRIPT_TPM_DIM = DatsObj("Dimension", [
        ("name", OrderedDict([("value", "Transcripts Per Kilobase Million"), ("valueIRI", "")])),
        ("description", "Transcripts Per Kilobase Million"),
        ("types", [COUNT_TYPE])
        ])

# STAR Aligner
STAR = DatsObj("Software", [
        ("name", "STAR Aligner"),
        ("version", "v2.4.2a")
        ])

# RSEM Software
RSEM = DatsObj("Software", [
        ("name", "RSEM"),
        ("version", "1.2.22")
        ])

# Public RNA-Seq datasets listed at https://www.gtexportal.org/home/datasets
#  doi_descr gives a dataset title that can be linked to a Datacite doi from GTEX_DATASETS_GUIDS_URL
#  doi_descr is assumed to be the same as descr if not specified
RNASEQ_DATASETS = [
    { "descr": "Gene read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_reads.gct.gz", 
      "analysis" : {"name": "Gene read count analysis.", "measures": [GENE_READ_COUNTS_DIM], "uses": [RNA_SEQ_QC]} },
    { "descr": "Gene TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_tpm.gct.gz", 
      "analysis" : {"name": "Gene TPM analysis.", "measures": [GENE_TPM_DIM], "uses": [RNA_SEQ_QC]} },
    # TODO - this file was derived directly from the preceding one
    { "descr": "Tissue median TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_gene_median_tpm.gct.gz", 
      "analysis" : {"name": "Tissue median TPM analysis.", "measures": [TISSUE_MEDIAN_TPM_DIM], "uses": [RNA_SEQ_QC]},
      "doi_descr": 'This file contains the median TPM by tissue.' },
    { "descr": "Junction read counts.", "file": "GTEx_Analysis_2016-01-15_v7_STARv2.4.2a_junctions.gct.gz", 
      "analysis" : {"name": "Junction read count analysis.", "measures": [JUNCTION_COUNT_DIM], "uses": [STAR]} },
    { "descr": "Transcript read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RSEMv1.2.22_transcript_expected_count.txt.gz", 
      "analysis" : {"name": "Transcript read count analysis.", "measures": [TRANSCRIPT_READ_COUNTS_DIM], "uses": [RSEM]} },
    { "descr": "Transcript TPMs.", "file": "GTEx_Analysis_2016-01-15_v7_RSEMv1.2.22_transcript_tpm.txt.gz", 
      "analysis" : {"name": "Transcript TPM analysis.", "measures": [TRANSCRIPT_TPM_DIM], "uses": [RSEM]} },
    { "descr": "Exon read counts.", "file": "GTEx_Analysis_2016-01-15_v7_RNASeQCv1.1.8_exon_reads.txt.gz", 
      "analysis" : {"name": "Exon read count analysis.", "measures": [EXON_READ_COUNTS_DIM], "uses": [RNA_SEQ_QC]} }
]

DB_GAP = DatsObj("DataRepository", [("name", "dbGaP")])

GTEX_CONSORTIUM = DatsObj("Organization", [
        ("name", "The Genotype-Tissue Expression (GTEx) Consortium"),
        ("abbreviation", "The GTEx Consortium"),
        ])

# TODO - where did  2017-06-30 release date come from?
GTEX_V7_RELEASE_DATE = OrderedDict([
        ("date", "2017-06-30T00:00:00.000Z"), 
        ("type", {"value": "release date"})
        ])

GTEX_V7_RNASEQ_TYPE = OrderedDict([
            ("information", TRANSCRIPT_PROFILING_TYPE),
            ("method", RNASEQ_ASSAY_TYPE),
            ("platform", ILLUMINA_TYPE)
            ])

GTEX_V7_WGS_TYPE = OrderedDict([
        ("information", DNA_SEQUENCING_TYPE),
        ("method", WGS_ASSAY_TYPE),
        ("platform", ILLUMINA_TYPE)
        ])

GTEX_V7_TYPES = [ GTEX_V7_WGS_TYPE, GTEX_V7_RNASEQ_TYPE ]

# parse dataset GUIDs from GTEX_DATASETS_GUIDS_URL
def set_dataset_guids():
    guid_data = None

    # read Datacite JSON
    with urllib.request.urlopen(GTEX_DATASETS_GUIDS_URL) as response:
        guid_data = response.read()
    guid_json = json.loads(guid_data.decode('utf-8'))
    
    # build mapping from title to DOI
    title2doi = {}
    for d in guid_json["data"]:
        # doi
        id = d['id']
        atts = d['attributes']
        title = atts['title']
        url = atts['url']
        version = atts['version']

        # everything should be tagged as v7 except for DroNc-seq data (?) and Biobank Inventory
        if version != "v7" and not title.startswith("DroNc-seq") and not title.startswith("Biobank Inventory"):
            logging.fatal("found GTEx version other than v7 (" + version + ") in '" + title + "' from " + GTEX_DATASETS_GUIDS_URL)
            sys.exit(1)

        # title (and resource-type-subtype) are the only fields that map (indirectly) to data file
        if title in title2doi:
            logging.fatal("duplicate entry for GTEx dataset with title '" + title + "' from " + GTEX_DATASETS_GUIDS_URL)
            sys.exit(1)

        title2doi[title + "."] = id
        logging.debug("mapped dataset title '" + title + "' to DOI/GUID " + id)

    # look up DOI for each dataset
    for ds in RNASEQ_DATASETS:
        descr = ds["descr"]
        if "doi_descr" in ds:
            descr = ds["doi_descr"]

        if descr not in title2doi:
            logging.fatal("couldn't find dataset with title = '" + descr + "' in " + GTEX_DATASETS_GUIDS_URL)
            sys.exit(1)            

        doi = title2doi[descr]
        ds["doi"] = doi

def get_dataset_json():
    set_dataset_guids()
    # individual RNA-Seq datasets/files
    rnaseq_data_subsets = [];

    # create DATS Dataset for each RNA-Seq data product
    for dss in RNASEQ_DATASETS:
        descr = dss["descr"]
        file = dss["file"]

        analysis = dss["analysis"]
        measures = analysis["measures"]
        uses = analysis["uses"]
        # "The name of the activity, usually one sentece or short description of the data analysis."
        analysis_name = analysis["name"]
        # "A textual narrative comprised of one or more statements describing the data analysis."
#        analysis_descr = analysis["descr"]

        # DataAnalysis
        data_analysis = DatsObj("DataAnalysis", [
                ("name", analysis_name),
#                ("description", analysis_descr),
                ("measures", measures),
                ("uses", uses)
                ])

        # Dataset
        subset = DatsObj("Dataset", id=dss["doi"], atts=[
                ("identifier", DatsObj("Identifier", [
                            ("identifier", "GTEx_Analysis_2016-01-15_v7_RNA-SEQ_" + file)
                            ])),
                ("version", "v7"),
                ("dates", [GTEX_V7_RELEASE_DATE]),
                ("title", "GTEx v7 RNA-Seq Analysis, " + descr),
                ("storedIn", DB_GAP),
                ("types", [ GTEX_V7_RNASEQ_TYPE ]),
                ("creators", [GTEX_CONSORTIUM]),
                ("producedBy", data_analysis),
                # TODO - where does the actual filename belong?
                ("distributions", [DatsObj("DatasetDistribution", [
                                ("access", DatsObj("Access", [
                                            ("landingPage", GTEX_DATASETS_URL)
                                            ]))
                                ])]),
                ])
        rnaseq_data_subsets.append(subset)

    # parent RNA-Seq dataset
    parent_rnaseq_dataset = DatsObj("Dataset", [
            ("identifier", DatsObj("Identifier", [
                        ("identifier", "GTEx_Analysis_2016-01-15_v7_RNA-SEQ")
                        ])),
            ("version", "v7"),
            ("dates", [GTEX_V7_RELEASE_DATE]),
            ("title",  "GTEx v7 RNA-Seq Analysis"),
            ("storedIn", DB_GAP),
            ("types", [ GTEX_V7_RNASEQ_TYPE ]),
            ("creators", [GTEX_CONSORTIUM]),
            ("distributions", [DatsObj("DatasetDistribution", [
                                    ("access", DatsObj("Access", [
                                                ("landingPage", GTEX_DATASETS_URL)
                                                ]))
                                    ])]),
            ("hasPart", rnaseq_data_subsets)
            ])

    # parent GTEx dataset
    gtex_dataset = DatsObj("Dataset", [
            ("identifier", DatsObj("Identifier", [
                        ("identifier", GTEX_DB_GAP_ID)
                        ])),
            ("version", "v7"),
            ("dates", [GTEX_V7_RELEASE_DATE]),
            ("title",  "GTEx v7"),
            ("storedIn", DB_GAP),
            # TODO add types for parent GTEx project
            ("types", GTEX_V7_TYPES),
            ("creators", [GTEX_CONSORTIUM]),
            ("distributions", [DatsObj("DatasetDistribution", [
                            ("access", DatsObj("Access", [
                                        ("landingPage", GTEX_DB_GAP_URL)
                                        ]))
                            ])]),
            ("hasPart", [ parent_rnaseq_dataset ])
            ])

    # TODO - add 'licenses', 'availability', 'dimensions', 'primaryPublications'?
    return gtex_dataset
