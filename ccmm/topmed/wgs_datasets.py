#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
from collections import OrderedDict
import logging
import re
import sys

TOPMED_DESCRIPTION = """TOPMed generates scientific resources related to heart, lung, blood, and sleep disorders (HLBS). It \
is sponsored by the NIH NHLBI and is part of a broader Precision Medicine Initiative."""

# List of 19 TOPMed studies cut and pasted from https://www.ncbi.nlm.nih.gov/gap/?term=topmed
TOPMED_STUDIES_STR = """
phs000946.v3.p1
NHLBI TOPMed: Boston Early-Onset COPD Study in the TOPMed ProgramVersions 1-2: passed embargo
Version 3: 2018-05-18
VDAS80Pedigree Whole Genome SequencingLinks
HiSeq X Ten
phs001024.v3.p1
NHLBI TOPMed: Partners HealthCare BiobankVersions 1-2: passed embargo
Version 3: 2018-05-18
VDAS128Case SetLinks
HiSeq X Ten
phs000964.v3.p1
NHLBI TOPMed: The Jackson Heart StudyVersions 1-2: passed embargo
Version 3: 2018-05-18
VDAS3596Longitudinal CohortLinks
HiSeq X Ten
phs000956.v3.p1
NHLBI TOPMed: Genetics of Cardiometabolic Health in the AmishVersions 1-2: passed embargo
Version 3: 2018-05-17
VDAS1123FamilyLinks
HiSeq X Ten
phs000954.v2.p1
NHLBI TOPMed: The Cleveland Family Study (WGS)Versions 1-2: passed embargo
VDAS994LongitudinalLinks
HiSeq X Ten
phs000921.v2.p1
NHLBI TOPMed: Study of African Americans, Asthma, Genes and Environment (SAGE) StudyVersions 1-2: passed embargo
VDAS500Case SetLinks
HiSeq X Ten
phs001040.v2.p1
NHLBI TOPMed: Novel Risk Factors for the Development of Atrial Fibrillation in WomenVersions 1-2: passed embargo
VDAS118Case SetLinks
HiSeq X Ten
phs000993.v2.p2
NHLBI TOPMed: Heart and Vascular Health Study (HVH)Versions 1-2: passed embargo
VDAS709Case SetLinks
HiSeq X Ten
phs000997.v2.p2
NHLBI TOPMed: The Vanderbilt AF Ablation RegistryVersions 1-2: passed embargo
VDAS171Case SetLinks
HiSeq X Ten
phs001032.v3.p2
NHLBI TOPMed: The Vanderbilt Atrial Fibrillation RegistryVersions 1-3: passed embargo
VDAS1134Case SetLinks
HiSeq X Ten
phs001062.v2.p2
NHLBI TOPMed: MGH Atrial Fibrillation StudyVersions 1-2: passed embargo
VDAS999Case SetLinks
HiSeq X Ten
phs000920.v2.p2
NHLBI TOPMed: Genes-environments and Admixture in Latino Asthmatics (GALA II) StudyVersions 1-2: passed embargo
VDAS999Case SetLinks
HiSeq X Ten
phs000974.v2.p2
NHLBI TOPMed: Whole Genome Sequencing and Related Phenotypes in the Framingham Heart StudyVersions 1-2: passed embargo
VDAS4154CohortLinks
HiSeq X Ten
phs000951.v2.p2
NHLBI TOPMed: Genetic Epidemiology of COPD (COPDGene) in the TOPMed ProgramVersions 1-2: passed embargo
VDAS10229Case-ControlLinks
HiSeq X Ten
phs000988.v2.p1
NHLBI TOPMed: The Genetic Epidemiology of Asthma in Costa RicaVersions 1-2: passed embargo
VDAS1533Parent-Offspring TriosLinks
HiSeq X Ten
phs000972.v2.p1
NHLBI TOPMed: Genome-wide Association Study of Adiposity in SamoansVersions 1-2: passed embargo
VDAS1332Cross-Sectional, PopulationLinks
HiSeq X Ten
phs001211.v1.p1
NHLBI TOPMed: Trans-Omics for Precision Medicine Whole Genome Sequencing Project: ARICVersion 1: passed embargo
VDAS4230Case-ControlLinks
HiSeq X Ten
phs001189.v1.p1
NHLBI TOPMed: Cleveland Clinic Atrial Fibrillation StudyVersion 1: passed embargo
VDAS362Case SetLinks
HiSeq X Ten
phs001143.v1.p1
NHLBI TOPMed: The Genetics and Epidemiology of Asthma in BarbadosVersion 1: passed embargo
VDAS1527FamilyLinks
HiSeq 2000
"""

DBGAP_QUERY_URL_PREFIX = 'https://www.ncbi.nlm.nih.gov/gap/?term='
DBGAP_TOPMED_QUERY_URL = DBGAP_QUERY_URL_PREFIX + 'topmed'

## Ontology for Biomedical Investigations
# "DNA sequencing"
DNA_SEQUENCING_TYPE = OrderedDict([("value", "DNA sequencing"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000626")])
# "whole genome sequencing assay"
WGS_ASSAY_TYPE = OrderedDict([("value", "whole genome sequencing assay"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002117")])
# "Illumina"
ILLUMINA_TYPE = OrderedDict([("value", "Illumina"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000759")])
# "Illumina HiSeq 2000"
HISEQ_2000_TYPE = OrderedDict([("value", "Illumina HiSeq 2000"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002001")])
# "Illumina HiSeq X Ten"
HISEQ_X10_TYPE = OrderedDict([("value", "Illumina HiSeq X Ten"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002129")])

HISEQ_TYPES = {
    "HiSeq 2000": HISEQ_2000_TYPE,
    "HiSeq X Ten": HISEQ_X10_TYPE
}

# NCI Thesaurus OBO Edition
# "Actual Subject Number"
N_SUBJECTS_TYPE = OrderedDict([("value", "Actual Subject Number"), ("valueIRI", "http://purl.obolibrary.org/obo/NCIT_C98703")])

# TODO - duplicated from rnaseq_datasets.py
DB_GAP = DatsObj("DataRepository", [("name", "dbGaP")])

NIH_NHLBI = DatsObj("Organization", [
        ("name", "The National Institute of Health's National Heart, Lung and Blood Institute"),
        ("abbreviation", "NHLBI")
        ])

TOPMED_TYPES = [
    # WGS sequencing
    OrderedDict([
            ("information", DNA_SEQUENCING_TYPE),
            ("method", WGS_ASSAY_TYPE),
            # WGS platform is either HiSeq 2000 or HiSeq X 10
            ("platform", ILLUMINA_TYPE)
            ])
    # TODO - add other types for which data/analyses have not yet been generated, e.g., SNP/GWAS
    ]

# 
def get_dbgap_studies(qterm):
    studies = []
    study = None
    lnum  = 0

    # Add newline before each occurrence of "Versions" if not already present
    lines = []
    for line in TOPMED_STUDIES_STR.split('\n'):
        m = re.match(r'^(\S+.*)(Versions.*)$', line)
        if m is None:
            lines.append(line)
        else:
            lines.append(m.group(1))
            lines.append(m.group(2))

    for line in lines:
        lnum += 1
        # blank line
        if re.match(r'^\s*$', line):
            continue
        # study id
        m = re.match('^(phs\S+)$', line)
        if m is not None:
            study = { 'id': m.group(1) }
            studies.append(study)
            continue
        # study description
        m = re.match(r'^NHLBI TOPMed: (.*)$', line)
        if m is not None:
            study['descr'] = m.group(1)
            continue
        # embargo release(s)
        m = re.match(r'^(Version.*)$', line)
        if m is not None:
            if 'versions' not in study:
                study['versions'] = []
            study['versions'].append(m.group(1))
            continue
        # details/participants/type of study
        m = re.match('^VDAS(\d+)(\S.*)Links$', line)
        if m is not None:
            study['n_participants'] = int(m.group(1))
            study['study_type'] = m.group(2)
            continue
        # platform
        m = re.match(r'^(HiSeq.*)$', line)
        if m is not None:
            study['platform'] = m.group(1)
            continue
        # parse error
        logging.fatal("unexpected content at line " + str(lnum) + " of dbGaP studies: " + line)
        sys.exit(1)

    n_studies = len(studies)
    logging.info("found " + str(n_studies) + " TOPMed studies in dbGaP")

    # convert studies to DATS Datasets
    datasets = []
    for s in studies:
        m = re.match(r'^phs\d+\.(v\d+)\.p\d+$', s['id'])
        if m is None:
            logging.fatal("unable to parse dataset/study version from study id " + s['id'])
            sys.exit(1)
        version = m.group(1)

        dimensions = [
            DatsObj("Dimension", [
                    ("name", { "value": "Actual Subject Count" } ),
                    ("description", "The actual number of subjects entered into a clinical trial."),
                    ("types", [ N_SUBJECTS_TYPE ]),
                    ("values", [ s['n_participants'] ])
                    ])
            ]

        types = [OrderedDict([
            ("information", DNA_SEQUENCING_TYPE),
            ("method", WGS_ASSAY_TYPE),
            ("platform", HISEQ_TYPES[s['platform']])
            ])]

        # TODO - Specify creators and release date(s) of this particular dataset.
        #  This may require parsing some of the metadata files and/or documents.
        creators = []

        # TODO - find better location for study_type?
        extra_props = [ DatsObj("CategoryValuesPair", [("category", "study_type"), ("values", [s['study_type']])]) ]

        # Dataset
        dataset = DatsObj("Dataset", [
                ("identifier", DatsObj("Identifier", [("identifier", s['id'])])),
                ("version", version),
#                ("dates", []),
                ("title", s['descr']),
                ("storedIn", DB_GAP),
                ("types", types),
                ("creators", creators),
                ("dimensions", dimensions),
                ("extraProperties", extra_props)
#                ("producedBy", data_analysis),
 #               ("distributions", [DatsObj("DatasetDistribution", [
#                                ("access", DatsObj("Access", [
#                                            ("landingPage", GTEX_DATASETS_URL)
#                                            ]))
#                                ])]),
                ])

        datasets.append(dataset)
        
    return datasets

def get_dataset_json():
    # individual datasets corresponding to studies within TOPMed
    data_subsets = [];

    # pull studies from dbGaP
    data_subsets = get_dbgap_studies("topmed")

    # parent TOPMed dataset
    parent_topmed_dataset = DatsObj("Dataset", [
            ("identifier", DatsObj("Identifier", [
                        # GTEx value - "GTEx_Analysis_2016-01-15_v7_RNA-SEQ"
                        ("identifier", "TOPMed")
                        ])),
            ("title",  "Trans-Omics for Precision Medicine (TOPMed)"),
            ("description", TOPMED_DESCRIPTION),
            ("storedIn", DB_GAP),
            ("types", TOPMED_TYPES),
            ("creators", [NIH_NHLBI]),
            ("distributions", [DatsObj("DatasetDistribution", [
                                    ("access", DatsObj("Access", [
                                                ("landingPage", DBGAP_TOPMED_QUERY_URL)
                                                ]))
                                    ])]),
            ("hasPart", data_subsets)
            ])

    # TODO - add 'licenses', 'availability', 'dimensions', 'primaryPublications'?

    return parent_topmed_dataset

