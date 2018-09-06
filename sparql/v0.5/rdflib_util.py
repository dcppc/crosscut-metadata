#!/usr/bin/env python3

import logging
import rdflib
import re
import sys

# A collection of functions to facilitate emulation of SPARQL queries with RDFLib API calls.

# ------------------------------------------------------
# Globals
# ------------------------------------------------------

RDF_TYPE_TERM = rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')

CENTRAL_ID_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000577')
NAME_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000590')
DESCR_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000300')
DERIVES_FROM_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0001000')
TITLE_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/OBI_0001622')
HAS_PART_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000051')
PRODUCED_BY_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0003001')
HAS_INPUT_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002233')
HAS_MEMBER_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0002351')
HAS_QUALITY_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/RO_0000086')
DATA_ITEM_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000027')

DATS_ANATOMICAL_ENTITY_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/UBERON_0001062')
DATS_DATASET_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000100')
DATS_DATA_ACQUISITION_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/OBI_0600013') # information acquisition
DATS_DIMENSION_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/STATO_23367')
DATS_MATERIAL_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000040') # "material entity"
DATS_STUDY_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/OBI_0000066') # "investigation"
DATS_STUDY_GROUP_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/STATO_0000193') # "study group population"

SDO_ACTION_TERM = rdflib.term.URIRef('https://schema.org/Action')
SDO_SIZE_TERM = rdflib.term.URIRef('https://schema.org/contentSize')
SDO_ANATOMICAL_STRUCTURE_TERM = rdflib.term.URIRef('https://schema.org/AnatomicalStructure')
SDO_DATA_DOWNLOAD_TERM = rdflib.term.URIRef('https://schema.org/DataDownload')
SDO_DISTRIBUTIONS_TERM = rdflib.term.URIRef('https://schema.org/distribution')
SDO_IDENT_TERM = rdflib.term.URIRef('https://schema.org/identifier')
SDO_VALUE_TERM = rdflib.term.URIRef('https://schema.org/value')

# ------------------------------------------------------
# rdflib_util
# ------------------------------------------------------

def read_json_ld_graph(file):
    logging.info("Reading DATS JSON metadata from " + file)
    with open(file, "r") as f:
        json_data = f.read()
    logging.info("read JSON data")
    logging.info("parsing JSON data")
    g = rdflib.Graph().parse(data=json_data, format='json-ld')
    logging.info("parsing complete")
    logging.info("read " + str(len(g)) + " RDF triple(s)")
    return g

    
