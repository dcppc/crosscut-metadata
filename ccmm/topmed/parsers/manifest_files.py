#!/usr/bin/env python3

# Parser for TOPMed manifest files

from ccmm.dats.datsobj import DatsObj
import ccmm.gtex.parsers.util as util
import logging

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

MD5_REGEX = r'^[a-f\d+]{32}$'
SAMPLE_ID_REGEX = r'^NWD\d+$'
CONSENT_REGEX = r'^(DS-CS-MDS-RD|DS-CS-RD|DS-LD|DS-LD-RD||HMB|HMB-MDS)$'
SEX_REGEX = r'^male|female$'
TOPMED_ABBREV_REGEX = r'^phs\d+$'

S3_CRAM_REGEX = r'^s3:\/\/.*\.cram$'
S3_CRAI_REGEX = r'^s3:\/\/.*\.cram\.crai$'
S3_VCF_REGEX = r'^s3:\/\/.*\.vcf\.gz$'
S3_CSI_REGEX = r'^s3:\/\/.*\.vcf\.gz\.csi$'

GS_CRAM_REGEX = r'^gs:\/\/.*\.cram$'
GS_CRAI_REGEX = r'^gs:\/\/.*\.cram\.crai$'
GS_VCF_REGEX = r'^gs:\/\/.*\.vcf\.gz$'
GS_CSI_REGEX = r'^gs:\/\/.*\.vcf\.gz\.csi$'

MANIFEST_COLS = [
    {'id': 'sample_id', 'regex': SAMPLE_ID_REGEX, 'empty_ok': False },
    {'id': 'consent_abbrev', 'regex': CONSENT_REGEX, 'empty_ok': False },
    {'id': 'sex', 'regex': SEX_REGEX, 'empty_ok': False },
    {'id': 'topmed_abbrev', 'regex': TOPMED_ABBREV_REGEX, 'empty_ok': False },

    {'id': 's3_cram', 'regex': S3_CRAM_REGEX, 'empty_ok': False },
    {'id': 's3_crai', 'regex': S3_CRAI_REGEX, 'empty_ok': False },
    {'id': 's3_vcf', 'regex': S3_VCF_REGEX, 'empty_ok': False },
    {'id': 's3_csi', 'regex': S3_CSI_REGEX, 'empty_ok': False },

    {'id': 'gs_cram', 'regex': GS_CRAM_REGEX, 'empty_ok': False },
    {'id': 'gs_crai', 'regex': GS_CRAI_REGEX, 'empty_ok': False },
    {'id': 'gs_vcf', 'regex': GS_VCF_REGEX, 'empty_ok': False },
    {'id': 'gs_csi', 'regex': GS_CSI_REGEX, 'empty_ok': False }
]

# ------------------------------------------------------
# Manifest file parsing
# ------------------------------------------------------

def read_manifest(manifest_file):
    samples = util.read_csv_metadata_file(manifest_file, MANIFEST_COLS, 'sample_id')
    logging.info("Read " + str(len(samples)) + " sample(s) from " + manifest_file)
    return samples
