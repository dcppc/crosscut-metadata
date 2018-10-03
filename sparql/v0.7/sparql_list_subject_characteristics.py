#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru 
import re
import sys

# Implementation of "list subject characteristics" query in SPARQL.

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='List subject characteristics using an RDFLib SPARQL query.');
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse JSON LD
    g = ru.read_json_ld_graph(args.dats_file)

    # ------------------------------------------
    # List subject characteristics
    # ------------------------------------------

    # obo:BFO_0000040 - "material entity"
    # obo:IAO_0000590 - "a textual entity that denotes a particular in reality"
    # obo:BFO_0000023 - "role"
    # obo:RO_0000086 - "has quality"
    # obo:IAO_0000027 - "data item"
    # obo:IAO_0000577 - "centrally registered identifier symbol"

    qres = g.query(
            """
            SELECT DISTINCT ?subject_name ?dbgap_var_acc ?pname ?propvalue
            WHERE {
                ?subj1 a obo:BFO_0000040.
                ?subj1 obo:IAO_0000590 ?subject_name.
                ?subj1 obo:BFO_0000023 ?role.
                ?role sdo:value ?rolename.
                ?subj1 obo:RO_0000086 ?chars.
                ?chars obo:IAO_0000027 ?propvalue.
                ?chars obo:IAO_0000577 ?chars_id.
                ?chars_id sdo:identifier ?dbgap_var_acc.
                ?chars obo:IAO_0000590 ?propname.
                ?propname sdo:value ?pname.
                FILTER (str(?rolename) = "donor").
            }
            ORDER BY ?subject_name str(?pname)
            """)

    print("Subject characteristics:\n")
    print("Subject ID\tdbGaP variable\tCharacteristic\tValue")
    for row in qres:
        print("%s\t%s\t%s\t%s" % row)
    print("\n")

if __name__ == '__main__':
    main()
