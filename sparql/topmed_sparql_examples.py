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
    parser.add_argument('--topmed_file', default='.', help ='Path to TOPMed DATS JSON file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse TOPMed JSON LD
    logging.info("Reading TOPMed metadata from " + args.topmed_file)
    # TODO - use streaming API instead
    with open(args.topmed_file, "r") as f:
        json_data = f.read()

    g = rdflib.Graph().parse(data=json_data, format='json-ld')

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
                ?tm_dataset a sdo:Dataset.
                ?tm_dataset sdo:hasPart ?dataset.
                ?dataset a sdo:Dataset.             
                ?dataset sdo:name ?title.
                ?dataset sdo:identifier ?identifier.
                ?identifier sdo:identifier ?ident.
            }
            """)

    print("[QUERY 1] TOPMed studies:\n")
    print("TOPMed Study\tDescription")
    for row in qres:
        print("%s\t%s" % row)
    print("\n")

    # ------------------------------------------
    # List all DNA extracts
    # ------------------------------------------

    qres = g.query(
            """
            SELECT DISTINCT (group_concat( distinct ?dna_extract;separator="; ") as ?names)
            WHERE {
                ?dataset a sdo:Dataset.
                ?mat1 a sdo:Thing.
                ?dataset sdo:about ?mat1.
                ?mat1 sdo:name ?dna_extract.
                ?mat1 sdo:roleName ?role.
                ?role sdo:value ?rolename.
                FILTER (str(?rolename) = "DNA extract").
            }
            """)

    print("[QUERY 2] DNA extracts:\n")
    print("DNA extract")
    for row in qres:
        print("%s" % row)
    print("\n")

    # ------------------------------------------
    # List all subject metadata
    # ------------------------------------------

    # This query is incomplete and also nonfunctional due to limitations in the context files, notably:
    #  -no definition for derivesFrom, effectively hiding the specimens and subjects
    #  -no definition for either subject 'characteristics' or 'extraProperties'
    #    (DATS Material is mapped to sdo:Thing)
    # Once these issues are resolved it should be possible to enumerate the characteristics and/or extraProperties.

#    qres = g.query(
#            """
#            SELECT DISTINCT ?subject_name
#            WHERE {
#                ?mat1 a sdo:Thing.
#                ?mat1 sdo:name ?subject_name.
#                ?mat1 sdo:roleName ?role.
#                ?role sdo:value ?rolename.
#                FILTER (str(?rolename) = "donor").
#            }
#            """)
#
#    print("[QUERY 3] Subject metadata:\n")
#    print("Subject")
#    for row in qres:
#        print("%s" % row)
#    print("\n")

    # ------------------------------------------
    # DNA extract / sample / subject triples
    # ------------------------------------------

    # This query doesn't work with only the schema.org context files because of the lack of a derivesFrom relationship

#    qres = g.query(
#            """
#            SELECT DISTINCT ?dna_extract ?sample ?subject
#            WHERE {
#                ?mat1 a sdo:Material.
#                ?mat2 a sdo:Material.
#                ?mat3 a sdo:Material.
#                ?mat1 sdo:derivesFrom ?mat2.
#                ?mat2 sdo:derivesFrom ?mat3.
#                ?mat1 sdo:name ?dna_extract.
#                ?mat2 sdo:name ?sample.
#                ?mat3 sdo:name ?subject.
#            }
#            """)
#
#    print("[QUERY 4] DNA extract/sample/subject triples:\n")
#    print("DNA extract\tSample\tSubject")
#    for row in qres:
#        print("%s\t%s\t%s" % row)
#    print()

if __name__ == '__main__':
    main()
