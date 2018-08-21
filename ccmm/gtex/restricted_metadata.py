#!/usr/bin/env python3

import ccmm.dbgap.restricted_metadata 
import logging

# Read all dbGaP restricted .txt metadata files in a given directory and parse their contents.
def read_study_metadata(dir):
    return ccmm.dbgap.restricted_metadata.read_study_metadata(dir)
