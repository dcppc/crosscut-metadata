#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru 
import re
import sys

# Implementation of "list study group members" query in SPARQL/RDFLib.

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='List subjects in a given DATS Dataset and StudyGroup.')
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON file.')
    parser.add_argument('--dataset_id', required=False, help ='DATS identifier of the Dataset linked to the StudyGroup of interest.')
    parser.add_argument('--study_group_name', required=False, help ='DATS identifier of the StudyGroup of interest.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse JSON LD
    g = ru.read_json_ld_graph(args.dats_file)

    # obo:IAO_0000100 - "data set"
    # obo:IAO_0000577 - "centrally registered identifier symbol"
    # obo:RO_0003001 - "produced by"
    # obo:OBI_0000066 - "investigation"
    # obo:BFO_0000051 - "has part"
    # obo:STATO_0000193 - "study group population"
    # obo:RO_0002351 - "has member"
    # obo:IAO_0000590 - "a textual entity that denotes a particular in reality"
    # obo:BFO_0000040 - "material entity"

    bindings = {}
    if args.dataset_id is not None:
        bindings['dbgap_study_acc'] = rdflib.term.Literal(args.dataset_id)
    if args.study_group_name is not None:
        bindings['study_group_name'] = rdflib.term.Literal(args.study_group_name, lang="en")

    qres = g.query(
            """
            SELECT ?dbgap_study_acc ?study_group_name ?subject_name
            WHERE {
                ?dataset a obo:IAO_0000100.
                ?dataset obo:IAO_0000577 ?dataset_id.
                ?dataset_id sdo:identifier ?dbgap_study_acc.
                ?dataset obo:RO_0003001 ?study.
                ?study a obo:OBI_0000066.
                ?study obo:BFO_0000051 ?study_group.
                ?study_group a obo:STATO_0000193.
                ?study_group obo:IAO_0000590 ?study_group_name.
                ?study_group obo:RO_0002351 ?subject.
                ?subject a obo:BFO_0000040.
                ?subject obo:IAO_0000590 ?subject_name.
            }
            ORDER BY ?dbgap_study_acc ?study_group_name ?subject_name
            """, initBindings = bindings)

    print()
    print("StudyGroup members:")
    print()
    print("dbGaP Study\tStudy Group\tSubject ID")
    for row in qres:
        print("%s\t%s\t%s" % row)
    print()

if __name__ == '__main__':
    main()
