#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru 
import re
import sys

# Implementation of "list sample characteristics" query in SPARQL.

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='List sample characteristics using an RDFLib SPARQL query.');
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse JSON LD
    g = ru.read_json_ld_graph(args.dats_file)

    # ------------------------------------------
    # List sample characteristics
    # ------------------------------------------

    qres = g.query(
            """
            SELECT DISTINCT ?sample_name ?dbgap_var_acc ?pname ?propvalue
            WHERE {
                ?samp1 a obo:BFO_0000040.
                ?samp1 obo:IAO_0000590 ?sample_name.
                ?samp1 obo:BFO_0000023 ?role.
                ?role sdo:value ?rolename.
                ?samp1 obo:RO_0000086 ?chars.
                ?chars obo:IAO_0000027 ?propvalue.
                ?chars obo:IAO_0000577 ?chars_id.
                ?chars_id sdo:identifier ?dbgap_var_acc.
                ?chars obo:IAO_0000590 ?propname.
                ?propname sdo:value ?pname.
                FILTER (str(?rolename) = "specimen").
            }
            ORDER BY ?sample_name str(?pname)
            """)

    print("Sample characteristics:\n")
    print("Sample ID\tdbGaP variable\tCharacteristic\tValue")
    for row in qres:
        print("%s\t%s\t%s\t%s" % row)
    print("\n")

if __name__ == '__main__':
    main()
