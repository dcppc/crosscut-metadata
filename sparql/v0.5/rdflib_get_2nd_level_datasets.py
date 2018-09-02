#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import re
import sys

# Implementation of "get 2nd level datasets" query directly in Python using
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
    logging.info("Reading DATS JSON metadata from " + args.dats_file)
    with open(args.dats_file, "r") as f:
        json_data = f.read()
    logging.info("read JSON data")

    logging.info("parsing JSON data")
    g = rdflib.Graph().parse(data=json_data, format='json-ld')
    logging.info("parsing complete")

    # count triples
    n_triples = 0
    # find all Datasets
    dataset_ids = {}

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

    # need to specify None, None, None, otherwise...
    # TypeError: triples() missing 1 required positional argument: 'xxx_todo_changeme2'
    for t in g.triples((None, None, None)):
        (a,b,c) = t
        if (re.search("IAO_0000100", str(c))):
            dataset_ids[a] = a
        n_triples += 1
    logging.info("read " + str(n_triples) + " RDF triple(s)")

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
    
    # Look for Dataset whose title matches a particular string
    gtex_title_term = rdflib.term.Literal('Genotype-Tissue Expression Project (GTEx)', datatype=rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000300'))
    topmed_title_term = rdflib.term.Literal('Trans-Omics for Precision Medicine (TOPMed)', datatype=rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000300'))
    top_datasets = []

    for id in dataset_ids:
        term = dataset_ids[id]
        # obo:OBI_0001622 - "a textual entity that denotes an investigation" - links DATS entity to title
        for t in g.triples((term, rdflib.term.URIRef('http://purl.obolibrary.org/obo/OBI_0001622'), gtex_title_term)):
            top_datasets.append(t)
        for t in g.triples((term, rdflib.term.URIRef('http://purl.obolibrary.org/obo/OBI_0001622'), topmed_title_term)):
            top_datasets.append(t)

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

    dataset_parts = []
    for td in top_datasets:
        (a, b, c) = td
        # obo:BFO_0000051 - "has part"
        for t in g.triples((a, rdflib.term.URIRef('http://purl.obolibrary.org/obo/BFO_0000051'), None)):
            (sa, sb, sc) = t
            dataset_parts.append(sc)

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

    type_term = rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')

    sub_datasets = []
    for dp in dataset_parts:
        is_dataset = False
        for t in g.triples((dp, type_term, rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000100'))):
            (sa, sb, sc) = t
            is_dataset = True
        if is_dataset:
            sub_datasets.append(dp)

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

    titles = []
    ids = []

    id_term = rdflib.term.Literal('Genotype-Tissue Expression Project (GTEx)', datatype=rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000577'))
    for sd in sub_datasets:

        for t in g.triples((sd, rdflib.term.URIRef('http://purl.obolibrary.org/obo/OBI_0001622'), None)):
            (a, b, c) = t
            titles.append(c)
        for t in g.triples((sd, rdflib.term.URIRef('http://purl.obolibrary.org/obo/IAO_0000577'), None)):
            (a, b, c) = t
            ids.append(c)

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

    idents = []
    for i in ids:
        for t in g.triples((i, rdflib.term.URIRef('https://schema.org/identifier'), None)):
            (a, b, c) = t
            idents.append(c)

    print()
    print("2nd-level DATS Datasets:")
    print()
    print("Dataset\tDescription")

    nt = len(titles)
    for i in range(0, nt):
        print("%s\t%s" % (idents[i], titles[i]))

if __name__ == '__main__':
    main()
