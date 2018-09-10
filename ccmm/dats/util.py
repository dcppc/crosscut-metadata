#!/usr/bin/env python3

from collections import OrderedDict
from ccmm.dats.datsobj import DatsObj
import json
import logging
import re

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

DATS_TAXON_HUMAN = DatsObj("TaxonomicInformation", [
        ("name", "Homo sapiens"),
        ("identifier", OrderedDict([
                    ("identifier", "ncbitax:9606"),
                    ("identifierSource", "ncbitax")]))
        ])

# commonly-used Annotation objects
DATS_ANNOTATIONS = {
    "Actual Subject Number": DatsObj("Annotation", [("value", "Actual Subject Number"), ("valueIRI", "http://purl.obolibrary.org/obo/NCIT_C98703")]),
    "count" : DatsObj("Annotation", [("value", "count"), ("valueIRI", "http://purl.obolibrary.org/obo/STATO_0000047")]),
    "donor" : DatsObj("Annotation", [("value", "donor"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_1110087")]),
    "DNA extract" : DatsObj("Annotation", [("value", "DNA extract"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0001051")]),
    "DNA sequencing": DatsObj("Annotation", [("value", "DNA sequencing"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000626")]),
    "exome sequencing assay": DatsObj("Annotation", [("value", "exome sequencing assay"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002118")]),
    "Illumina": DatsObj("Annotation", [("value", "Illumina"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000759")]),
    "Illumina HiSeq 2000": DatsObj("Annotation", [("value", "Illumina HiSeq 2000"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002001")]),
    "Illumina HiSeq X Ten": DatsObj("Annotation", [("value", "Illumina HiSeq X Ten"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002129")]),
    "patient": DatsObj("Annotation", [("value", "patient"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000093")]),
    "RNA extract" : DatsObj("Annotation", [("value", "RNA extract"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000880")]),
    "RNA-seq assay" : DatsObj("Annotation", [("value", "RNA-seq assay"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0001271")]),
    "specimen" : DatsObj("Annotation", [("value", "specimen"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0100051")]),
    "transcription profiling": DatsObj("Annotation", [("value", "transcription profiling"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000424")]),
    "whole genome sequencing assay": DatsObj("Annotation", [("value", "whole genome sequencing assay"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0002117")])
}

# ------------------------------------------------------
# util
# ------------------------------------------------------

def get_alt_id(id, source):
    return DatsObj("AlternateIdentifier", [ ("identifier", id), ("identifierSource", source) ])

def get_taxon_human(cache):
    if cache is not None:
        tkey = ".".join(["TaxonomicInformation", "Homo sapiens"])
        return cache.get_obj_or_ref(tkey, lambda: DATS_TAXON_HUMAN)
    return DATS_TAXON_HUMAN

def get_donor_roles(cache):
    roles = ["patient", "donor"]
    return [get_annotation(r, cache) for r in roles]

# retrieve one of a number of predefined Annotations with value and valueIRI
def get_annotation(name, cache=None):
    if cache is not None:
        key = ".".join(["Annotation", name])
        return cache.get_obj_or_ref(key, lambda: DATS_ANNOTATIONS[name])
    return DATS_ANNOTATIONS[name]

# retrieve a "bare" annotation with value but not valueIRI
def get_value_annotation(value, cache):
    key = ".".join(["Annotation", "Value", value])
    fn = lambda: DatsObj("Annotation", [("value", value)])
    return cache.get_obj_or_ref(key, fn)
