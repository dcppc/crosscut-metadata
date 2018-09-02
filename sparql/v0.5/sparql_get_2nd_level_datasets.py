#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import re
import sys

# Implementation of "get 2nd level datasets" query in SPARQL/RDFLib.

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='List 2nd level Datasets in TOPMed or GTEx crosscut model instance using an RDFLib SPARQL query.');
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON file.')
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

    qres = g.query(
            """
            SELECT ?ident ?title
            WHERE {
                ?top_dataset a obo:IAO_0000100.
                ?top_dataset obo:OBI_0001622 ?top_title.
                FILTER ((str(?top_title) = "Genotype-Tissue Expression Project (GTEx)") || (str(?top_title) = "Trans-Omics for Precision Medicine (TOPMed)")).
                ?top_dataset obo:BFO_0000051 ?dataset.
                ?dataset a obo:IAO_0000100.
                ?dataset obo:OBI_0001622 ?title.
                ?dataset obo:IAO_0000577 ?identifier.
                ?identifier sdo:identifier ?ident.
             }
             """)

    print()
    print("2nd-level DATS Datasets:")
    print()
    print("Dataset\tDescription")
    for row in qres:
        print("%s\t%s" % row)
    print("\n")

if __name__ == '__main__':
    main()
