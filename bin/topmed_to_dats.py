#!/usr/bin/env python3

# Create DATS JSON description of TOPMed public data.

import argparse
from ccmm.dats.datsobj import DATSEncoder
import ccmm.topmed.dna_extracts
import ccmm.topmed.wgs_datasets
import ccmm.topmed.public_metadata
import json
import logging
import os
import re
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

    # index studies by id
    studies_by_id = {}
    for tds in topmed_dataset.get("hasPart"):
        study_id = tds.get("identifier").get("identifier")
        if study_id in studies_by_id:
            logging.fatal("encountered duplicate study_id " + study_id)
            sys.exit(1)
        m = re.match(r'^(phs\d+\.v\d+)\.p\d+$', study_id)
        if m is None:
            logging.fatal("unable to parse study_id " + study_id)
            sys.exit(1)
        studies_by_id[m.group(1)] = tds

    # if not processing protected metadata then generate representative DATS JSON using only the public metadata
    pub_xp = args.dbgap_public_xml_path
    priv_mp = args.dbgap_protected_metadata_path

    # process public metadata only (i.e., data dictionaries and variable reports only)
    if priv_mp is None:
        study_md = ccmm.topmed.public_metadata.read_study_metadata(pub_xp)
#        logging.debug("study_md = " + str(study_md))

        # generate sample entry for each study for which we have metadata
        for study_id in study_md:
            study = studies_by_id[study_id]
            # create dummy/representative DATS instance based on variable reports
            # TODO - signal somewhere directly in the DATS that this is not real subject-level data (subject/sample id may be sufficient)
            sample_sample = ccmm.topmed.dna_extracts.get_synthetic_single_sample_json_from_public_metadata(study, study_md[study_id])
            # insert synthetic sample into relevant study/Dataset
            is_about = study.set("isAbout", [sample_sample])

    # process both public metadata and access-controlled dbGaP metadata
    else:
        logging.fatal("processing access-controlled dbGaP metadata is not yet supported")
        sys.exit(1)

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(topmed_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
