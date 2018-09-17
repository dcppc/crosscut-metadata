#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru
import rdflib_list_2nd_level_datasets
import rdflib_list_dataset_variables
import rdflib_list_study_group_members
import rdflib_tabular_dump
import re
import sys

# Run test queries on TOPMed instance.

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():
    
    # input
    parser = argparse.ArgumentParser(description='Run test queries on TOPMed instance.')
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON-LD file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse JSON LD
    g = ru.read_json_ld_graph(args.dats_file)

    # list 2nd-level datasets
    datasets = rdflib_list_2nd_level_datasets.list_2nd_level_datasets(g)
    rdflib_list_2nd_level_datasets.print_results(datasets)
    
    # list dataset variables
    for dataset_id in (['phs001024.v3.p1', 'phs000951.v2.p2', 'phs000179.v5.p2']):
        variables = rdflib_list_dataset_variables.list_dataset_variables(g, dataset_id)
        rdflib_list_dataset_variables.print_results(variables, dataset_id)
    
    # list study group members
    for dataset_id in (['phs001024.v3.p1', 'phs000951.v2.p2', 'phs000179.v5.p2']):
        for study_group in (['all subjects']):
            members = rdflib_list_study_group_members.list_study_group_members(g, dataset_id, study_group)
            rdflib_list_study_group_members.print_results(members, dataset_id, study_group)

if __name__ == '__main__':
    main()
