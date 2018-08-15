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
    DatsObj("Annotation", 
            [
            ("value", "patient"),
            ("valueIRI",  "http://purl.obolibrary.org/obo/OBI_0000093")
            ]
            ),
    DatsObj("Annotation",
            [
            ("value", "donor"),
            ("valueIRI", "http://purl.obolibrary.org/obo/OBI_1110087")
            ]
            )
    ]

# commonly-used Annotation objects
DATS_ANNOTATIONS = {
    "specimen" : DatsObj("Annotation", [("value", "specimen"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0100051")]),
    "DNA extract" : DatsObj("Annotation", [("value", "DNA extract"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0001051")]),
    "RNA extract" : DatsObj("Annotation", [("value", "RNA extract"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000880")])
}

# ------------------------------------------------------
# util
# ------------------------------------------------------

def get_alt_id(id, source):
    return DatsObj("AlternateIdentifier", [ ("identifier", id), ("identifierSource", source) ])

def get_taxon_human():
    return DATS_TAXON_HUMAN

def get_donor_roles():
    return DATS_DONOR_ROLES

def get_annotation(name):
    return DATS_ANNOTATIONS[name]
