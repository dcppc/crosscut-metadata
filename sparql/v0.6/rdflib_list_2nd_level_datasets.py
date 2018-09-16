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
    
    # run query
    datasets = ru.list_2nd_level_datasets(g)

    print()
    print("2nd-level DATS Datasets:")
    print()
    print("Dataset\tDescription")

    for d in datasets
        print("%s\t%s" % (d["dataset"], d["description"]))

if __name__ == '__main__':
    main()
