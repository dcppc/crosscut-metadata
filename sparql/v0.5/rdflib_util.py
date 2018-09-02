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
NAME_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000300')
TITLE_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/OBI_0001622')
HAS_PART_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000051')

DATS_DATASET_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000100')

SDO_IDENT_TERM = rdflib.term.URIRef('https://schema.org/identifier')

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

    
