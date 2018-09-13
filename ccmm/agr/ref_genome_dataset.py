#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
import ccmm.mgd.human_homologs
from collections import OrderedDict
import csv
import gzip
import logging
import re
import sys

AGR_DESCRIPTION = """The Alliance (AGR) develops and maintains sustainable genome information resources \
that facilitates the use of diverse model organisms in understanding the genetic and genomic basis of \
human biology, health and disease. """


# List of AGR Genome builds
AGR_ref_genomes = {
    "MGI_1.0.4": "Mouse Genome (Mouse Genome Informatics)",
    "RGD_1.0.4": "Rat Genome (Rat Genome Database)"
    }


AGR = DatsObj("Organization", [("abbreviation", "AGR"),("name", "Alliance of Genome Resources")])
AGR_BUCKET = DatsObj("DataRepository", [
        ("name", "AGR"),
        ("description", "The Alliance AWS S3 BUCKET"),
        ("publishers", [AGR])
        ])

## Ontology for Biomedical Investigations
# "DNA sequencing"
DNA_SEQUENCING_TYPE = OrderedDict([("value", "DNA sequencing"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000626")])
WGS_ASSAY_TYPE = OrderedDict([("value", "whole genome sequencing assay"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002117")])

NIH_NHLBI = DatsObj("Organization", [
        ("name", "The National Institute of Health's National Heart, Lung and Blood Institute"),
        ("abbreviation", "NHLBI")
        ])

NIH_NHGRI = DatsObj("Organization", [
        ("name", "The National Institute of Health's National Human Genome Research Institute"),
        ("abbreviation", "NHGRI")
        ])

AGR_TYPES = [
    #WGS sequencing
    OrderedDict([
        ("information", DNA_SEQUENCING_TYPE)
        ])
    # TODO - add other types e.g., genes, human homologs, other feature types
    ]

STRAND_CHADO2SO = {
    '+': 'forward',
    '-': 'reverse'
}

AGR_DOWNLOAD_URL = "https://www.alliancegenome.org/api/swagger-ui/"



def get_ref_genomes(acc_d):
    ref_genomes = []
    ref_genome = None

    for arf in AGR_ref_genomes:
        m = re.match(r'^(\w+_)(\d+\.\d+\.\d+)$', arf)
        if m is not None:
            ref_genome = { 'id': m.group(1) + m.group(2) }
            ref_genome['versions'] = m.group(2)
            ref_genomes.append(ref_genome)
            continue
    
    # filter ref_genomes by acc_d
    filtered_ref_genomes = [r for r in ref_genomes if r['id'] in acc_d]
    ref_genomes = filtered_ref_genomes

    n_ref_genomes = len(ref_genomes)
    logging.info("found " + str(n_ref_genomes) + " Reference genomes in AGR Directory")

    # convert ref_genomes to DATS Datasets        
    datasets = []
    for r in ref_genomes:
        m = re.match(r'^\w+_(\d+\.\d+\.\d+)$', r['id'])
        if m is None:
            logging.fatal("unable to parse reference genome version from id " + r['id'])
            sys.exit(1)         
        version = m.group(1)
        
        types = [OrderedDict([
            ("information", DNA_SEQUENCING_TYPE)
            ])]
        
        creators = [NIH_NHLBI, NIH_NHGRI ]
        
        # Dataset
        dataset = DatsObj("Dataset", [
                ("identifier", DatsObj("Identifier", [("identifier", r['id'])])),
                ("version", version),
                ("title",  AGR_ref_genomes[r['id']]),
                ("storedIn", AGR_BUCKET),
                ("types", types),
                ("creators", creators)
               # ("dimensions", dimensions)
                ])
        datasets.append(dataset)
        
    return datasets



# acc_d - dict whose keys are the identifiers of entities to include
def get_dataset_json(acc_d):
    
    # individual datasets corresponding to model organisms within AGR data dump
    dats_subsets = [];
    
    # pull genome build from AWS files
    data_subsets = get_ref_genomes(acc_d)
    
    # parent AGR reference genome dataset
    parent_agr_dataset = DatsObj("Dataset", [
            ("identifier", DatsObj("Identifier", [
                        ("identifier", "AGR")
                        ])),
            ("title",  "Alliance of Genome Resources (AGR)"),
            ("description", AGR_DESCRIPTION),
            ("storedIn", AGR_BUCKET),
            ("types", AGR_TYPES),
            ("creators", [AGR]),
            ("distributions", [DatsObj("DatasetDistribution", [
                                    ("access", DatsObj("Access", [
                                                ("landingPage", AGR_DOWNLOAD_URL)
                                                ]))
                                    ])]),
            ("hasPart", data_subsets)
            ])

    # TODO - add 'licenses', 'availability', 'dimensions', 'primaryPublications'?
    
    return parent_agr_dataset
