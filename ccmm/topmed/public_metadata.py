#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
from collections import OrderedDict
import logging
import os
import re
import sys

# TODO - move non-TOPMed-specific code into 'dbgap' package?

# nested dicts not natively supported in Python3?
def make_multilevel_dict(items, keys):
    md = {}
    for item in items:
        d = md
        for k in keys[:-1]:
            kv = item[k]
            if kv not in d:
                d[kv] = {}
            d = d[kv]
        d[item[keys[-1]]] = item

    return md

# identify dbGaP XML metadata files in a directory and group them by study id and metadata type
def find_metadata_files(dir):
    filenames = os.listdir(dir)
    files = []

    for f in filenames:
        # ignore anything that doesn't start with a study id
        if re.match(r'^phs\d+\.', f):
            # list of possible file types (Subject, Sample, etc.) may vary from study to study
            m = re.match(r'^(phs\d+\.v\d+)\.((\S+)_(Subject|Sample|Sample_Attributes|Subject_Phenotypes)).(data_dict|var_report)\.xml$', f)
            if m is None:
                logging.fatal("unable to parse file type and study name from dbGaP file " + f)
                sys.exit(1)

            file = {
                "name": f, 
                "path": os.path.join(dir, f), 
                "study_id": m.group(1), 
                "study_name": m.group(3), 
                "metadata_type": m.group(4), 
                "file_type": m.group(5) 
                }
            files.append(file)

    return make_multilevel_dict(files, ["study_id", "metadata_type", "file_type"])
