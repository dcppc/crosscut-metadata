#!/usr/bin/env python3

from collections import OrderedDict
from ccmm.dats.datsobj import DatsObj
import json
import logging
import re

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

DATS_TAXON_HUMAN =  [
    DatsObj("TaxonomicInformation", [
            ("name", "Homo sapiens"),
            ("identifier", OrderedDict([
                        ("identifier", "ncbitax:9606"),
                        ("identifierSource", "ncbitax")]))
            ])
    ]

DATS_DONOR_ROLES = [
    OrderedDict([
            ("value", "patient"),
            ("valueIRI",  "")]),
    OrderedDict([
            ("value", "donor"),
            ("valueIRI", "")])
    ]

# ------------------------------------------------------
# util
# ------------------------------------------------------

def get_alt_id(id, source):
    return DatsObj("AlternateIdentifier", [ {"identifier": id, "identifierSource": source } ])

def get_taxon_human():
    return DATS_TAXON_HUMAN

def get_donor_roles():
    return DATS_DONOR_ROLES
