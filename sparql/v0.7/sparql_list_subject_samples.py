#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru 
import re
import sys

# Implementation of "list subject samples" query in SPARQL.

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='List subjects and samples in TOPMed or GTEs crosscut model instance using an RDFLib SPARQL query.');
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse JSON LD
    g = ru.read_json_ld_graph(args.dats_file)

    # ------------------------------------------
    # RNA/DNA extract / sample / subject triples
    # ------------------------------------------

    # obo:IAO_0000100 - "data set"
    # obo:BFO_0000040 - "material entity"
    # obo:IAO_0000136 - "is about"
    # obo:IAO_0000590 - "a textual entity that denotes a particular in reality"
    # obo:BFO_0000023 - "role"
    # obo:RO_0001000 - "derives from"
    # obo:IAO_0000300 - "textual entity"

    qres = g.query(
            """
            SELECT DISTINCT ?rna_or_dna_extract ?sample_name ?sample_descr ?subject_name ?subject_descr
            WHERE {
                ?dataset a obo:IAO_0000100.
                ?mat1 a obo:BFO_0000040.
                ?dataset obo:IAO_0000136 ?mat1.
                ?mat1 obo:IAO_0000590 ?rna_or_dna_extract.
                ?mat1 obo:BFO_0000023 ?role.
                ?role sdo:value ?rolename.
                ?mat1 obo:RO_0001000 ?sample.
                ?sample obo:IAO_0000590 ?sample_name.
                ?sample obo:IAO_0000300 ?sample_descr.
                ?sample obo:RO_0001000 ?subject.
                ?subject obo:IAO_0000590 ?subject_name.
                ?subject obo:IAO_0000300 ?subject_descr.
                FILTER ((str(?rolename) = "DNA extract") || (str(?rolename) = "RNA extract")).
            }
            ORDER BY ?subject_name ?sample_name
            """)

    print("Samples and subjects:\n")
    print("RNA/DNA extract\tSample ID\tSample\tSubject ID\tSubject")
    for row in qres:
        print("%s\t%s\t%s\t%s\t%s" % row)
    print("\n")

if __name__ == '__main__':
    main()
