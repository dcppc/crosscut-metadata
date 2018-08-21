#!/usr/bin/env python3

import argparse
import logging
import rdflib 

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Run test queries on public TOPMed crosscut model instance using RDF/SPARQL.')
    parser.add_argument('--topmed_file', help ='Path to TOPMed DATS JSON file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse TOPMed JSON LD
    logging.info("Reading TOPMed metadata from " + args.topmed_file)
    with open(args.topmed_file, "r") as f:
        json_data = f.read()

    g = rdflib.Graph().parse(data=json_data, format='json-ld')
    logging.info("Parsing complete")

    # Uncomment this to see the triples parsed from JSON-LD:
    print("Parsed JSON-LD:")
    print(g.serialize(format='n3', indent=4).decode('ascii'))
    print()

    # ------------------------------------------
    # Enumerate TOPMed studies
    # ------------------------------------------
    qres = g.query(
            """
            SELECT DISTINCT ?ident ?title
            WHERE {
                ?tm_dataset a obo:IAO_0000100.
                ?tm_dataset obo:BFO_0000051 ?dataset.
                ?dataset a obo:IAO_0000100.
                ?dataset obo:OBI_0001622 ?title.
                ?dataset obo:IAO_0000577 ?identifier.
                ?identifier sdo:identifier ?ident.
            }
            """)

    print("[QUERY 1] TOPMed studies:\n")
    print("TOPMed Study\tDescription")
    for row in qres:
        print("%s\t%s" % row)
    print("\n")

    # ------------------------------------------
    # DNA extract / sample / subject triples
    # ------------------------------------------

    qres = g.query(
            """
            SELECT DISTINCT ?dna_extract ?sample_name ?subject_name
            WHERE {
                ?dataset a obo:IAO_0000100.
                ?mat1 a obo:BFO_0000040.
                ?dataset obo:IAO_0000136 ?mat1.
                ?mat1 obo:IAO_0000590 ?dna_extract.
                ?mat1 obo:BFO_0000023 ?role.
                ?role sdo:value ?rolename.
                ?mat1 obo:RO_0001000 ?sample.
                ?sample obo:IAO_0000300 ?sample_name.
                ?sample obo:RO_0001000 ?subject.
                ?subject obo:IAO_0000300 ?subject_name.
                FILTER (str(?rolename) = "DNA extract").
            }
            """)

    print("[QUERY 2] DNA extracts:\n")
    print("DNA extract\tSample\tSubject")
    for row in qres:
        print("%s\t%s\t%s" % row)
    print("\n")

    # ------------------------------------------
    # List subject characteristics
    # ------------------------------------------

    # note that this query only retrieves 
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
            """)

    print("[QUERY 3] Subject characteristics:\n")
    print("Subject\tdbGaP variable\tCharacteristic\tValue")
    for row in qres:
        print("%s\t%s\t%s\t%s" % row)
    print("\n")

    # ------------------------------------------
    # List sample characteristics
    # ------------------------------------------

    # note that this query is identical to the previous one except that:
    #  1. the selected role name is "specimen", not "donor"
    #  2. the variable subj1 has been renamed to samp1
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
                FILTER (str(?rolename) = "specimen").
            }
            """)

    print("[QUERY 4] Sample characteristics:\n")
    print("Sample\tdbGaP variable\tCharacteristic\tValue")
    for row in qres:
        print("%s\t%s\t%s\t%s" % row)
    print("\n")

    # ------------------------------------------
    # Study variables (DATS dimensions)
    # ------------------------------------------

    # Query doesn't include the actual subject count, which looks like this:
    #
    # <tmpid:f661cd29-6cb1-4059-aaf9-de94b3913cc0> a obo:STATO_23367 ;
    #   obo:IAO_0000027 1134 ;
    #   obo:IAO_0000300 "The actual number of subjects entered into a clinical trial."@en ;
    #   obo:IAO_0000590 [ ] .

    qres = g.query(
            """
            SELECT DISTINCT ?dbgap_study_acc ?dbgap_var_acc ?pname ?descr
            WHERE {
                ?study a obo:IAO_0000100.
                ?study obo:IAO_0000577 ?study_id.
                ?study_id sdo:identifier ?dbgap_study_acc.
                ?study obo:BFO_0000051 ?dim1.
                ?dim1 a obo:STATO_23367.
                ?dim1 obo:IAO_0000300 ?descr.
                ?dim1 obo:IAO_0000577 ?dim1_id.
                ?dim1_id sdo:identifier ?dbgap_var_acc.
                ?dim1 obo:IAO_0000590 ?propname.
                ?propname sdo:value ?pname.
            }
            """)

    print("[QUERY 5] Study variables:\n")
    print("dbGaP Study\tdbGaP variable\tName\tDescription")
    for row in qres:
        print("%s\t%s\t%s\t%s" % row)
    print()

if __name__ == '__main__':
    main()
