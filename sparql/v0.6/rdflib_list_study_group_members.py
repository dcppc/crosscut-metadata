#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru
import re
import sys

# Implementation of "list study group members" query directly in Python using
# rdflib API calls.

def list_study_group_members(g, dataset_id, study_group_name):
    
    # obo:IAO_0000100 - "data set"
    # obo:IAO_0000577 - "centrally registered identifier symbol"
    # obo:RO_0003001 - "produced by"
    # obo:OBI_0000066 - "investigation"
    # obo:BFO_0000051 - "has part"
    # obo:STATO_0000193 - "study group population"
    # obo:RO_0002351 - "has member"
    # obo:IAO_0000590 - "a textual entity that denotes a particular in reality"
    # obo:BFO_0000040 - "material entity"

    #            SELECT ?dbgap_study_acc ?study_group_name ?subject_name
    #            WHERE {
    #  ---->         ?dataset a obo:IAO_0000100.
    #  ---->         ?dataset obo:IAO_0000577 ?dataset_id.
    #  ---->         ?dataset_id sdo:identifier ?dbgap_study_acc.
    #                ?dataset obo:RO_0003001 ?study.
    #                ?study a obo:OBI_0000066.
    #                ?study obo:BFO_0000051 ?study_group.
    #                ?study_group a obo:STATO_0000193.
    #                ?study_group obo:IAO_0000590 ?study_group_name.
    #                ?study_group obo:RO_0002351 ?subject.
    #                ?subject a obo:BFO_0000040.
    #                ?subject obo:IAO_0000590 ?subject_name.
    #            }
    #            ORDER BY ?dbgap_study_acc ?study_group_name ?subject_name
    
    # find ALL Datasets, retain those with a DATS identifier
    all_datasets = [s for (s,p,o) in g.triples((None, None, ru.DATS_DATASET_TERM))]
    dataset_ids = {}
    datasets = []
    for d in all_datasets:
        for (s,p,o) in g.triples((d, ru.CENTRAL_ID_TERM, None)):
            for (s2,p2,o2) in g.triples((o, ru.SDO_IDENT_TERM, None)):
                dataset_ids[d] = o2
        if d in dataset_ids:
            datasets.append(d)

    # filter datasets by id if one was specified
    datasets = [d for d in datasets if (dataset_id is None) or (rdflib.term.Literal(dataset_id) == dataset_ids[d])]

    #            SELECT ?dbgap_study_acc ?study_group_name ?subject_name
    #            WHERE {
    #                ?dataset a obo:IAO_0000100.
    #                ?dataset obo:IAO_0000577 ?dataset_id.
    #                ?dataset_id sdo:identifier ?dbgap_study_acc.
    #  ---->         ?dataset obo:RO_0003001 ?study.
    #  ---->         ?study a obo:OBI_0000066.
    #                ?study obo:BFO_0000051 ?study_group.
    #                ?study_group a obo:STATO_0000193.
    #                ?study_group obo:IAO_0000590 ?study_group_name.
    #                ?study_group obo:RO_0002351 ?subject.
    #                ?subject a obo:BFO_0000040.
    #                ?subject obo:IAO_0000590 ?subject_name.
    #            }
    #            ORDER BY ?dbgap_study_acc ?study_group_name ?subject_name

    # link each Dataset to Study (should be 1-1)
    ds_to_study = {}
    for d in datasets:
        for (s,p,o) in g.triples((d, ru.PRODUCED_BY_TERM, None)):
            for (s2,p2,o2) in g.triples((o, ru.RDF_TYPE_TERM, ru.DATS_STUDY_TERM)):
                ds_to_study[d] = o

    # filter Datasets not linked to a study
    datasets = [d for d in datasets if d in ds_to_study]

    #            SELECT ?dbgap_study_acc ?study_group_name ?subject_name
    #            WHERE {
    #                ?dataset a obo:IAO_0000100.
    #                ?dataset obo:IAO_0000577 ?dataset_id.
    #                ?dataset_id sdo:identifier ?dbgap_study_acc.
    #                ?dataset obo:RO_0003001 ?study.
    #                ?study a obo:OBI_0000066.
    #  ---->         ?study obo:BFO_0000051 ?study_group.
    #  ---->         ?study_group a obo:STATO_0000193.
    #  ---->         ?study_group obo:IAO_0000590 ?study_group_name.
    #                ?study_group obo:RO_0002351 ?subject.
    #                ?subject a obo:BFO_0000040.
    #                ?subject obo:IAO_0000590 ?subject_name.
    #            }
    #            ORDER BY ?dbgap_study_acc ?study_group_name ?subject_name

    # link each Study to StudyGroup (1-many) and get StudyGroup name
    study_to_groups = {}
    study_group_to_name = {}
    for s in ds_to_study.values():
        groups = []
        for (s,p,o) in g.triples((s, ru.HAS_PART_TERM, None)):
            for (s2,p2,o2) in g.triples((o, ru.RDF_TYPE_TERM, ru.DATS_STUDY_GROUP_TERM)):
                # get name
                n_names = 0
                for (s3,p3,o3) in g.triples((o, ru.NAME_TERM, None)):
                    study_group_to_name[o] = o3
                    n_names += 1

                if n_names == 1:
                    groups.append(o)

        study_to_groups[s] = groups

    #            SELECT ?dbgap_study_acc ?study_group_name ?subject_name
    #            WHERE {
    #                ?dataset a obo:IAO_0000100.
    #                ?dataset obo:IAO_0000577 ?dataset_id.
    #                ?dataset_id sdo:identifier ?dbgap_study_acc.
    #                ?dataset obo:RO_0003001 ?study.
    #                ?study a obo:OBI_0000066.
    #                ?study obo:BFO_0000051 ?study_group.
    #                ?study_group a obo:STATO_0000193.
    #                ?study_group obo:IAO_0000590 ?study_group_name.
    #  ---->         ?study_group obo:RO_0002351 ?subject.
    #  ---->         ?subject a obo:BFO_0000040.
    #  ---->         ?subject obo:IAO_0000590 ?subject_name.
    #            }
    #            ORDER BY ?dbgap_study_acc ?study_group_name ?subject_name
    
    # find subjects in each study group and retrieve their names
    study_group_to_subjects = {}
    subject_to_name = {}
    for sg in study_group_to_name.keys():
        subjects = []
        for (s,p,o) in g.triples((sg, ru.HAS_MEMBER_TERM, None)):
            for (s2,p2,o2) in g.triples((o, ru.RDF_TYPE_TERM, ru.DATS_MATERIAL_TERM)):
                for (s3,p3,o3) in g.triples((o, ru.NAME_TERM, None)):
                    subject_to_name[o] = o3
                subjects.append(o)
        study_group_to_subjects[sg] = subjects

    #            SELECT ?dbgap_study_acc ?study_group_name ?subject_name
    #            WHERE {
    #                ?dataset a obo:IAO_0000100.
    #                ?dataset obo:IAO_0000577 ?dataset_id.
    #                ?dataset_id sdo:identifier ?dbgap_study_acc.
    #                ?dataset obo:RO_0003001 ?study.
    #                ?study a obo:OBI_0000066.
    #                ?study obo:BFO_0000051 ?study_group.
    #                ?study_group a obo:STATO_0000193.
    #                ?study_group obo:IAO_0000590 ?study_group_name.
    #                ?study_group obo:RO_0002351 ?subject.
    #                ?subject a obo:BFO_0000040.
    #                ?subject obo:IAO_0000590 ?subject_name.
    #            }
    #  ---->     ORDER BY ?dbgap_study_acc ?study_group_name ?subject_name

    members_l = []

    # sort datasets
    datasets.sort(key=lambda x: dataset_ids[x])
    for d in datasets:
        dataset_id = dataset_ids[d]
        study = ds_to_study[d]
        groups = study_to_groups[study]
        
        # sort study groups
        groups.sort(key=lambda x: study_group_to_name[x])
        for g in groups:
            group_name = study_group_to_name[g]
            subjects = study_group_to_subjects[g]

            # filter by study group
            if (study_group_name is not None) and group_name != rdflib.term.Literal(study_group_name, lang="en"):
                continue
            
            # sort subjects
            subjects.sort(key=lambda x: subject_to_name[x])
            for s in subjects:
                subject_name = subject_to_name[s]
                members_l.append({"dataset_id": dataset_id, "group_name": group_name, "subject_name": subject_name})
    
    return members_l

def print_results(members, dataset_id, study_group_name):
    title = "StudyGroup members"
    conditions = []
    if dataset_id is not None:
        conditions.append("dataset " + dataset_id)
    if study_group_name is not None:
        conditions.append("study group name " + study_group_name)
    if len(conditions) > 0:
        title += " for " + ", ".join(conditions)
    title += ":"

    print()
    print(title)
    print()
    print("dbGaP Study\tStudy Group\tSubject ID")

    for m in members:
        print("%s\t%s\t%s" % (m["dataset_id"], m["group_name"], m["subject_name"]))

    print()

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

    # run query
    members = list_study_group_members(g, args.dataset_id, args.study_group_name)
    print_results(members, args.dataset_id, args.study_group_name)

if __name__ == '__main__':
    main()
