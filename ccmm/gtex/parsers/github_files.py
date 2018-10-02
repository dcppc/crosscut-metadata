#!/usr/bin/env python3

# Parsers for the public id dumps and manifest files available from https://github.com/dcppc/data-stewards/tree/master/gtex/v7

from ccmm.dats.datsobj import DatsObj
import ccmm.gtex.parsers.util as util
import logging

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

MD5_REGEX = r'^[a-f\d+]{32}$'
SUBJECT_ID_REGEX = r'^(GTEX|K)-[0-9A-Z]+$'
SAMPLE_ID_REGEX = r'^GTEX-[0-9A-Z]+-\d+-([A-Za-z0-9]+-)?[A-Z]+-[A-Z0-9]+|K-\d+-[A-Z]+-[0-9A-Z]+$'
DOI_REGEX = r'^https:\/\/doi\.org\/[\d\.]+/[\d0-9a-z\-]+$'

# gtex_v7_subject_ids.txt
#Native form	Prefixed form	URI	Destination URL	Outgoing URI	Entity Type
#GTEX-1117F	GTEX-1117F		https://gtexportal.org/rest/v1/dataset/subject?datasetId=gtex_v7&subjectId=GTEX-1117F		individual_organism
#GTEX-111CU	GTEX-111CU		https://gtexportal.org/rest/v1/dataset/subject?datasetId=gtex_v7&subjectId=GTEX-111CU		individual_organism
SUBJECT_ID_COLS = [
    {'id': 'Native form', 'regex': SUBJECT_ID_REGEX, 'empty_ok': False },
    {'id': 'Prefixed form', 'regex': SUBJECT_ID_REGEX, 'empty_ok': False },
    {'id': 'URI', 'empty_ok': True },
    {'id': 'Destination URL', 'empty_ok': False },
    {'id': 'Outgoing URI', 'empty_ok': True },
    {'id': 'Entity Type', 'regex': r'^individual_organism$', 'empty_ok': False }
]

# gtex_v7_sample_ids.txt
#Native form	Prefixed form	URI	Destination URL	Outgoing URI	Entity Type
#GTEX-1117F-0226-SM-5GZZ7	GTEX-1117F-0226-SM-5GZZ7		https://gtexportal.org/rest/v1/dataset/sample?datasetId=gtex_v7&sampleId=GTEX-1117F-0226-SM-5GZZ7		biosample
#GTEX-1117F-0426-SM-5EGHI	GTEX-1117F-0426-SM-5EGHI		https://gtexportal.org/rest/v1/dataset/sample?datasetId=gtex_v7&sampleId=GTEX-1117F-0426-SM-5EGHI		biosample
SAMPLE_ID_COLS = [
    {'id': 'Native form', 'regex': SAMPLE_ID_REGEX, 'empty_ok': False },
    {'id': 'Prefixed form', 'regex': SAMPLE_ID_REGEX, 'empty_ok': False },
    {'id': 'URI', 'empty_ok': True },
    {'id': 'Destination URL', 'empty_ok': False },
    {'id': 'Outgoing URI', 'empty_ok': True },
    {'id': 'Entity Type', 'regex': r'^biosample$', 'empty_ok': False }
]

# gtex_v7_tissue_ids
#Native form	Uberon id	Prefixed form	URI	Destination URL	Outgoing URI	Entity Type
#Adipose_Subcutaneous	0002190	Adipose_Subcutaneous	(not resolvable)	(not resolvable)	http://purl.obolibrary.org/obo/UBERON_0002190	gross_anatomical_structure
#Adipose_Visceral_Omentum	0010414	Adipose_Visceral_Omentum	(not resolvable)	(not resolvable)	http://purl.obolibrary.org/obo/UBERON_0010414	gross_anatomical_structure
TISSUE_ID_COLS = [
    {'id': 'Native form', 'regex': r'^[a-zA-Z\d+\-_]+$', 'empty_ok': False },
    {'id': 'Uberon id', 'regex': r'^\d+|EFO_\d+$', 'empty_ok': False },
    {'id': 'Prefixed form', 'regex': r'^[a-zA-Z\d+\-_]+$', 'empty_ok': False },
    {'id': 'URI', 'empty_ok': True },
    {'id': 'Destination URL', 'empty_ok': False },
    {'id': 'Outgoing URI', 'empty_ok': True },
    {'id': 'Entity Type', 'regex': r'^gross_anatomical_structure$', 'empty_ok': False }
]

# sample_id	cram_file	cram_file_md5	cram_file_size	cram_index	cram_file_aws	cram_index_aws
RNASEQ_MANIFEST_COLS = [
    {'id': 'sample_id', 'regex': SAMPLE_ID_REGEX, 'empty_ok': False },
    {'id': 'cram_file_gcp', 'regex': '^gs:\/\/\S+\.cram$', 'empty_ok': False },         # Google Storage URI
    {'id': 'cram_index_gcp', 'regex': '^gs:\/\/\S+\.cram.crai$', 'empty_ok': False },   # Google Storage URI
    {'id': 'cram_file_aws', 'regex': '^s3:\/\/\S+\.cram$', 'empty_ok': False },         # S3 URI
    {'id': 'cram_index_aws', 'regex': '^s3:\/\/\S+\.cram\.crai$', 'empty_ok': False },  # S3 URI
    {'id': 'cram_file_md5', 'regex': MD5_REGEX, 'empty_ok': False },
    {'id': 'cram_file_size', 'regex': r'\d+', 'empty_ok': False },
    {'id': 'cram_index_md5', 'regex': MD5_REGEX, 'empty_ok': False },                   # Google Storage URI
]

#sample_id	firecloud_id	cram_file	cram_file_md5	cram_file_size	cram_index	cram_file_aws	cram_index_aws
#
# almost identical to RNA-Seq file except for:
#  1. addition of firecloud_id
#  2. index file suffix of ".crai", not ".cram.crai"
WGS_MANIFEST_COLS = [
    {'id': 'sample_id', 'regex': SAMPLE_ID_REGEX, 'empty_ok': False },
    {'id': 'cram_file_gcp', 'regex': '^gs:\/\/\S+\.cram$', 'empty_ok': False },          # Google Storage URI
    {'id': 'cram_index_gcp', 'regex': '^gs:\/\/\S+\.crai$', 'empty_ok': False },         # Google Storage URI
    {'id': 'cram_file_aws', 'regex': '^s3:\/\/\S+\.cram$', 'empty_ok': False },          # S3 URI
    {'id': 'cram_index_aws', 'regex': '^s3:\/\/\S+\.crai$', 'empty_ok': False },         # S3 URI
    {'id': 'cram_file_md5', 'regex': MD5_REGEX, 'empty_ok': False },
    {'id': 'cram_file_size', 'regex': r'\d+', 'empty_ok': False },
    {'id': 'cram_index_md5', 'regex': MD5_REGEX, 'empty_ok': False }
]

# sample_id	Sodium_GUID_cram	Sodium_GUID_crai
DOIS_MANIFEST_COLS = [
    {'id': 'sample_id', 'regex': SAMPLE_ID_REGEX, 'empty_ok': False },
    {'id': 'Sodium_GUID_cram', 'regex': DOI_REGEX, 'empty_ok': False },
    {'id': 'Sodium_GUID_crai', 'regex': DOI_REGEX, 'empty_ok': False }
]

# ------------------------------------------------------
# Metadata file parsing
# ------------------------------------------------------

def read_csv_metadata_file(file, id_column):
    # rows indexed by the value in id_column
    rows = {}

    with open(file_path) as fh:
        reader = csv.reader(fh, delimiter='\t')
        lnum = 0
        for line in reader:
            lnum += 1

# ------------------------------------------------------
# ID dump file parsing
# ------------------------------------------------------

def read_subject_id_file(id_file):
    subject_ids = util.read_csv_metadata_file(id_file, SUBJECT_ID_COLS, 'Native form')
    logging.info("Read " + str(len(subject_ids)) + " subject id(s) from " + id_file)
    return subject_ids

def read_sample_id_file(id_file):
    sample_ids = util.read_csv_metadata_file(id_file, SAMPLE_ID_COLS, 'Native form')
    logging.info("Read " + str(len(sample_ids)) + " sample id(s) from " + id_file)
    return sample_ids

def read_tissue_id_file(id_file):
    tissue_ids = util.read_csv_metadata_file(id_file, TISSUE_ID_COLS, 'Native form')
    logging.info("Read " + str(len(tissue_ids)) + " tissue id(s) from " + id_file)
    return tissue_ids

# ------------------------------------------------------
# Manifest file parsing
# ------------------------------------------------------

def read_protected_rnaseq_manifest(manifest_file):
    rnaseq_cram_files = util.read_csv_metadata_file(manifest_file, RNASEQ_MANIFEST_COLS, 'sample_id')
    logging.info("Read " + str(len(rnaseq_cram_files)) + " CRAM file(s) from " + manifest_file)
    return rnaseq_cram_files

def read_protected_wgs_manifest(manifest_file):
    wgs_cram_files = util.read_csv_metadata_file(manifest_file, WGS_MANIFEST_COLS, 'sample_id')
    logging.info("Read " + str(len(wgs_cram_files)) + " CRAM file(s) from " + manifest_file)
    return wgs_cram_files

def read_dois_manifest(dois_file):
    dois = util.read_csv_metadata_file(dois_file, DOIS_MANIFEST_COLS, 'sample_id')
    logging.info("Read " + str(len(dois)) + " DOI(s) from " + dois_file)
    return dois
