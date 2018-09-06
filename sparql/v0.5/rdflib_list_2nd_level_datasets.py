#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru
import re
import sys

# Implementation of "list 2nd level datasets" query directly in Python using
# rdflib API calls. 121X faster than equivalent SPARQL query for current
# GTEx JSON-LD file.

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='List 2nd level Datasets in TOPMed or GTEx crosscut model instance using RDFLib API calls.')
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON-LD file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse JSON LD
    g = ru.read_json_ld_graph(args.dats_file)

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

    print()
    print("2nd-level DATS Datasets:")
    print()
    print("Dataset\tDescription")

    nt = len(titles)
    for i in range(0, nt):
        print("%s\t%s" % (idents[i], titles[i]))

if __name__ == '__main__':
    main()
