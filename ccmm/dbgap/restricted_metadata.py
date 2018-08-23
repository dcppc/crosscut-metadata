#!/usr/bin/env python3

import ccmm.dbgap.public_metadata
import csv
import logging
import os 
import re
import sys
import xml.etree.ElementTree as ET

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------


# ------------------------------------------------------
# restricted_metadata
# ------------------------------------------------------

# Read dbGaP tab-delimited text file of restricted metadata
def read_dbgap_restricted_metadata_txt(txt_file):
    logging.info("reading " + txt_file)
    data = { "rows": [] }

    with open(txt_file) as tfile:
        reader = csv.reader(tfile, delimiter='\t')
        lnum = 0

        for row in reader:
            lnum += 1
            nc = len(row)
            if nc == 0:
                continue
            m = re.match(r'^\# (Study|Table) accession: (ph[st]\d+\.v\d+\.p\d+)', row[0])
            if m is not None:
                data[m.group(1).lower() + "_accession"] = m.group(2)
                continue
            # skip any other comments or blank lines
            if re.match(r'^(\s*|\#.*)$', row[0]):
                continue
            # should either be the header line or data
            if 'headers' not in data:
                data['headers'] = row
                pass
            else:
                # build dict from row
                rd = {}
                cnum = 0
                for c in row:
                    rd[data['headers'][cnum]] = c
                    cnum += 1
                data['rows'].append(rd)
    return data

def read_study_metadata(dir):
    study_md = {}
    fileype = []
    study_files = ccmm.dbgap.public_metadata.get_study_metadata_files(dir, "txt")

    n_studies = len(study_files)
    logging.info("found restricted metadata file(s) for " + str(n_studies) + " study/studies in " + dir)

    # process one study at a time
    for study_id in study_files:
        logging.info("processing restricted metadata for study " + study_id)
        sd = study_files[study_id]
        md = { 'files': {} }
        study_md[study_id] = md

        # study_name may include a consent group prefix
        # TODO - ignoring consent group in this iteration
        for study_name in sd:
            ssd = sd[study_name]
        
            for datatype in ('Subject', 'Sample', 'Sample_Attributes', 'Subject_Phenotypes'):
                if datatype not in ssd:
                    logging.info("no XML found for " + datatype)
                    continue

                # this is a consequence of ignoring the consent group prefix:
                if datatype in md:
                    logging.warn("ignoring file for duplicate datatype " + datatype )
                    continue

                # consent_type e.g., MULTI, HMB
                consent_type = list(ssd[datatype].keys())[0]
                file_path = ssd[datatype][consent_type]['path']
                txt_data = read_dbgap_restricted_metadata_txt(file_path)
                md[datatype] = { 'file': file_path, 'data': txt_data }
                md['files'][datatype] = ssd[datatype]

    return study_md

