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
DATS_DIMENSION_TERM = rdflib.term.URIRef('http://purl.obolibrary.org/obo/STATO_0000258')
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

# ------------------------------------------------------
# list 2nd level DATS Datasets
# ------------------------------------------------------

def list_2nd_level_datasets(g):
    
    #    SELECT ?ident ?title
    #            WHERE {
    #  ---->         ?top_dataset a obo:IAO_0000100.
    #                ?top_dataset obo:OBI_0001622 ?top_title.
    #                FILTER ((str(?top_title) = "Genotype-Tissue Expression Project (GTEx)") || (str(?top_title) = "Trans-Omics for Precision Medicine (TOPMed)")).
    #                ?top_dataset obo:BFO_0000051 ?dataset.
    #                ?dataset a obo:IAO_0000100.
    #                ?dataset obo:OBI_0001622 ?title.
    #                ?dataset obo:IAO_0000577 ?identifier.
    #                ?identifier sdo:identifier ?ident.
    #            }

    # find ALL Datasets
    all_datasets = [s for (s,p,o) in g.triples((None, ru.RDF_TYPE_TERM, ru.DATS_DATASET_TERM))]

    #    SELECT ?ident ?title
    #            WHERE {
    #                ?top_dataset a obo:IAO_0000100.
    #  ---->         ?top_dataset obo:OBI_0001622 ?top_title.
    #  ---->         FILTER ((str(?top_title) = "Genotype-Tissue Expression Project (GTEx)") || (str(?top_title) = "Trans-Omics for Precision Medicine (TOPMed)")).
    #                ?top_dataset obo:BFO_0000051 ?dataset.
    #                ?dataset a obo:IAO_0000100.
    #                ?dataset obo:OBI_0001622 ?title.
    #                ?dataset obo:IAO_0000577 ?identifier.
    #                ?identifier sdo:identifier ?ident.
    #            }
    
    # filter Datasets, get those with a title matching one of these two strings:
    titles = ['Genotype-Tissue Expression Project (GTEx)', 'Trans-Omics for Precision Medicine (TOPMed)']
    title_terms = [rdflib.term.Literal(t, datatype=ru.DESCR_TERM) for t in titles]
    datasets = []

    for d in all_datasets:
        for tt in title_terms:
            for (s,p,o) in g.triples((d, ru.TITLE_TERM, tt)):
                datasets.append(d)

    #    SELECT ?ident ?title
    #            WHERE {
    #                ?top_dataset a obo:IAO_0000100.
    #                ?top_dataset obo:OBI_0001622 ?top_title.
    #                FILTER ((str(?top_title) = "Genotype-Tissue Expression Project (GTEx)") || (str(?top_title) = "Trans-Omics for Precision Medicine (TOPMed)")).
    #  ---->         ?top_dataset obo:BFO_0000051 ?dataset.
    #                ?dataset a obo:IAO_0000100.
    #                ?dataset obo:OBI_0001622 ?title.
    #                ?dataset obo:IAO_0000577 ?identifier.
    #                ?identifier sdo:identifier ?ident.
    #            }

    # find all entities linked by "has part" to the top-level GTEx and TOPMed Datasets
    l2_entities = []
    for d in datasets:
        for (s,p,o) in g.triples((s, ru.HAS_PART_TERM, None)):
            l2_entities.append(o)

    #    SELECT ?ident ?title
    #            WHERE {
    #                ?top_dataset a obo:IAO_0000100.
    #                ?top_dataset obo:OBI_0001622 ?top_title.
    #                FILTER ((str(?top_title) = "Genotype-Tissue Expression Project (GTEx)") || (str(?top_title) = "Trans-Omics for Precision Medicine (TOPMed)")).
    #                ?top_dataset obo:BFO_0000051 ?dataset.
    #  ---->         ?dataset a obo:IAO_0000100.
    #                ?dataset obo:OBI_0001622 ?title.
    #                ?dataset obo:IAO_0000577 ?identifier.
    #                ?identifier sdo:identifier ?ident.
    #            }

    # filter l2_entities, keeping only those that are Datasets
    l2_datasets = []
    for e in l2_entities:
        l = [t for t in g.triples((e, ru.RDF_TYPE_TERM, ru.DATS_DATASET_TERM))]
        if len(l) > 0:
            l2_datasets.append(e)

    #    SELECT ?ident ?title
    #            WHERE {
    #                ?top_dataset a obo:IAO_0000100.
    #                ?top_dataset obo:OBI_0001622 ?top_title.
    #                FILTER ((str(?top_title) = "Genotype-Tissue Expression Project (GTEx)") || (str(?top_title) = "Trans-Omics for Precision Medicine (TOPMed)")).
    #                ?top_dataset obo:BFO_0000051 ?dataset.
    #                ?dataset a obo:IAO_0000100.
    #  ---->         ?dataset obo:OBI_0001622 ?title.
    #  ---->         ?dataset obo:IAO_0000577 ?identifier.
    #                ?identifier sdo:identifier ?ident.
    #            }

    # Retrieve title and id for each 2nd-level Dataset. Using parallel arrays, which assumes
    # that each Dataset will have exactly one of each.
    titles = []
    ids = []

    id_term = rdflib.term.Literal('Genotype-Tissue Expression Project (GTEx)', datatype=ru.CENTRAL_ID_TERM)
    for d in l2_datasets:
        for (s,p,o) in g.triples((d, ru.TITLE_TERM, None)):
            titles.append(o)
        for (s,p,o) in g.triples((d, ru.CENTRAL_ID_TERM, None)):
            ids.append(o)

    #    SELECT ?ident ?title
    #            WHERE {
    #                ?top_dataset a obo:IAO_0000100.
    #                ?top_dataset obo:OBI_0001622 ?top_title.
    #                FILTER ((str(?top_title) = "Genotype-Tissue Expression Project (GTEx)") || (str(?top_title) = "Trans-Omics for Precision Medicine (TOPMed)")).
    #                ?top_dataset obo:BFO_0000051 ?dataset.
    #                ?dataset a obo:IAO_0000100.
    #                ?dataset obo:OBI_0001622 ?title.
    #                ?dataset obo:IAO_0000577 ?identifier.
    #  ---->         ?identifier sdo:identifier ?ident.
    #            }

    # One more step needed to get from DATS Identifier to the actual id.
    idents = []
    for i in ids:
        for (s,p,o) in g.triples((i, ru.SDO_IDENT_TERM, None)):
            idents.append(o)

    datasets_l = []

    nt = len(titles)
    for i in range(0, nt):
        datasets_l.append({"dataset": idents[i], "description": titles[i] })

    return datasets_l
