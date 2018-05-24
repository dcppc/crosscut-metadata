#!/usr/bin/env python3

# Create DATS JSON description of TOPMed public data.

import argparse
from ccmm.dats.datsobj import DATSEncoder
import ccmm.topmed.wgs_datasets
import ccmm.topmed.public_metadata
import json
import logging
import os
import sys

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for TOPMed public metadata.')
    parser.add_argument('--output_file', default='.', help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    parser.add_argument('--dbgap_public_xml_path', required=True, help ='Path to directory that contains public dbGaP metadata files e.g., *.data_dict.xml and *.var_report.xml')
    parser.add_argument('--dbgap_protected_metadata_path', required=False, help ='Path to directory that contains access-controlled dbGaP tab-delimited metadata files.')
    args = parser.parse_args()

    # logging
#    logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)

    # create top-level dataset
    topmed_dataset = ccmm.topmed.wgs_datasets.get_dataset_json()

    # if not processing protected metadata then generate representative DATS JSON using only the public metadata
    pub_xp = args.dbgap_public_xml_path
    priv_mp = args.dbgap_protected_metadata_path

    # process public metadata only (i.e., data dictionaries and variable reports only)
    if priv_mp is None:
        study_md = ccmm.topmed.public_metadata.read_study_metadata(pub_xp)

        logging.debug("study_md = " + str(study_md))

        # TODO - create dummy/representative DATS instance based on variable reports

    # process both public metadata and access-controlled dbGaP metadata
    else:
        logging.fatal("processing access-controlled dbGaP metadata is not yet supported")
        sys.exit(1)

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(topmed_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
