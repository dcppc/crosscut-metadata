#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru 
import re
import sys

# Implementation of "list variables for a dataset" query in SPARQL/RDFLib.
# Lists variables available in the DATS Dataset that corresponds to a given dbGaP study.

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='List variables available in the DATS Dataset that corresponds to a given dbGaP study.')
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON file.')
    parser.add_argument('--dataset_id', required=False, help ='DATS identifier of the Dataset whose variables should be retrieved.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse JSON LD
    g = ru.read_json_ld_graph(args.dats_file)

    # obo:IAO_0000100 - "data set"
    # obo:IAO_0000577 - "centrally registered identifier symbol"
    # obo:BFO_0000051 - "has part"
    # obo:STATO_23367 - ? (doesn't appear in stato.owl from https://www.ebi.ac.uk/ols/ontologies/stato, but CHEBI_23367 = molecular entity)
    # obo:IAO_0000300 - "textual entity"
    # obo:IAO_0000590 - "a textual entity that denotes a particular in reality"

    bindings = None
    if args.dataset_id is not None:
        bindings = {'dbgap_study_acc': rdflib.term.Literal(args.dataset_id)}

    qres = g.query(
            """
            SELECT ?dbgap_study_acc ?dbgap_var_acc ?pname ?descr
            WHERE {
                ?dataset a obo:IAO_0000100.
                ?dataset obo:IAO_0000577 ?dataset_id.
                ?dataset_id sdo:identifier ?dbgap_study_acc.
                ?dataset obo:BFO_0000051 ?dim1.
                ?dim1 a obo:STATO_23367.
                ?dim1 obo:IAO_0000300 ?descr.
                ?dim1 obo:IAO_0000577 ?dim1_id.
                ?dim1_id sdo:identifier ?dbgap_var_acc.
                ?dim1 obo:IAO_0000590 ?propname.
                ?propname sdo:value ?pname.
            }
            ORDER BY ?dbgap_study_acc ?dbgap_var_acc
            """, initBindings = bindings)

    print()
    print("Dataset variables:")
    print()
    print("dbGaP Study\tdbGaP variable\tName\tDescription")
    for row in qres:
        print("%s\t%s\t%s\t%s" % row)
    print()

if __name__ == '__main__':
    main()
