#!/usr/bin/env python3

import argparse
import logging
import rdflib 
import rdflib_util as ru
import re
import sys

# Create tabular dump of DATS-encoded GTEx metadata using rdflib API calls.

def print_tabular_dump(g):
        
    # find ALL Datasets, retain those with a DATS identifier
    all_datasets = [s for (s,p,o) in g.triples((None, ru.RDF_TYPE_TERM, ru.DATS_DATASET_TERM))]
    dataset_ids = {}
    datasets = []
    for d in all_datasets:
        for (s,p,o) in g.triples((d, ru.CENTRAL_ID_TERM, None)):
            for (s2,p2,o2) in g.triples((o, ru.SDO_IDENT_TERM, None)):
                dataset_ids[d] = o2
        if d in dataset_ids:
            datasets.append(d)

    # retrieve top-level Dataset
    # filter Datasets, get those with a title matching one of these two strings:
    titles = ['Genotype-Tissue Expression Project (GTEx)', 'Trans-Omics for Precision Medicine (TOPMed)']
    title_terms = [rdflib.term.Literal(t, datatype=ru.DESCR_TERM) for t in titles]
    tl_datasets = []
    project_name = None

    for d in all_datasets:
        for tt in title_terms:
            for (s,p,o) in g.triples((d, ru.TITLE_TERM, tt)):
                tl_datasets.append(d)
                project_name = tt

    if len(tl_datasets) != 1:
        logging.fatal("found " + str(len(tl_datasets)) + " top-level DATS Datasets")
        sys.exit(1)

    # link each Dataset to Study (should be 1-1)
    ds_to_study = {}
    for d in datasets:
        for (s,p,o) in g.triples((d, ru.PRODUCED_BY_TERM, None)):
            for (s2,p2,o2) in g.triples((o, ru.RDF_TYPE_TERM, ru.DATS_STUDY_TERM)):
                ds_to_study[d] = o

    # filter Datasets not linked to a study
    datasets = [d for d in datasets if d in ds_to_study]

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

    # subject characteristics
    subject_to_chars = {}
    # all known characteristic names
    all_char_names = {}

    # retrieve subject characteristics

    #                ?subj1 obo:RO_0000086 ?chars.               X
    #                ?chars obo:IAO_0000027 ?propvalue.          X
    #                ?chars obo:IAO_0000577 ?chars_id.
    #                ?chars_id sdo:identifier ?dbgap_var_acc.
    #                ?chars obo:IAO_0000590 ?propname.           X
    #                ?propname sdo:value ?pname.                 X
    #                FILTER (str(?rolename) = "donor").

    for s in subject_to_name.keys():
        chars = {}
        for (s,p,o) in g.triples((s, ru.HAS_QUALITY_TERM, None)):
            char_names = []
            char_values = []
            dbgap_ids = []

            # characteristic value(s)
            for (s2,p2,o2) in g.triples((o, ru.DATA_ITEM_TERM, None)):
                char_values.append(o2)
            # characteristic name(s)
            for (s2,p2,o2) in g.triples((o, ru.NAME_TERM, None)):
                for (s3,p3,o3) in g.triples((o2, ru.SDO_VALUE_TERM, None)):
                    char_names.append(o3)
#                if len(char_names) == 0:
#                    char_names.append(o2)

            # dbGaP ids
            for (s2,p2,o2) in g.triples((o, ru.CENTRAL_ID_TERM, None)):
                for (s3,p3,o3) in g.triples((o2, ru.SDO_IDENT_TERM, None)):
                    dbgap_ids.append(o3)

            if len(char_values) == 0:
                char_values.append(None)

            if len(char_values) != 1 or len(char_names) != 1 or len(dbgap_ids) > 1:
                continue
                logging.fatal("subject=" + str(s) + " names=" + str(char_names) + " values=" + str(char_values) + " ids=" + str(dbgap_ids))
                sys.exit(1)

            cval = str(char_values[0])
            cname = str(char_names[0])
            chars[cname] = { "value": cval, "name": cname }
            all_char_names[cname] = True
        subject_to_chars[s] = chars

    # retrieve subject disease / diseaseStatus
    for s in subject_to_name.keys():
        for (s,p,o) in g.triples((s, ru.BEARER_OF_TERM, None)):
            for (s2,p2,o2) in g.triples((o, ru.RDF_TYPE_TERM, ru.DATS_DISEASE_TERM)):
                # name
                disease_name = None
                for (s3,p3,o3) in g.triples((o, ru.NAME_TERM, None)):
                    disease_name = o3
                # diseaseStatus
                disease_status = None
                for (s3,p3,o3) in g.triples((o, ru.DISEASE_STATUS_TERM, None)):
                    for (s4,p4,o4) in g.triples((o3, ru.SDO_VALUE_TERM, None)):
                        disease_status = o4

                if disease_name is not None and disease_status is not None:
                    all_char_names[disease_name] = True
                    subject_to_chars[s][disease_name] = { "value": disease_status, "name": disease_name }

    sorted_char_names = sorted(all_char_names.keys())
    subject_to_files = {}
    
    # retrieve data files
    for d in all_datasets:
        distribs = []  # file paths and sizes
        s3_URI = None
        gs_URI = None
        md5_checksum = None
        file_size = None

        # MD5 checksum
        # TODO - this is currently stored as a Dimension of Dataset, but will be moved
        md5_checksum = None

        for (s2,p2,o2) in g.triples((d, ru.HAS_PART_TERM, None)):
            for (s3,p3,o3) in g.triples((o2, ru.RDF_TYPE_TERM, ru.DATS_DIMENSION_TERM)):
                name = None
                value = None
                for (s4,p4,o4) in g.triples((o2, ru.NAME_TERM, None)):
                    for (s5,p5,o5) in g.triples((o4, ru.SDO_VALUE_TERM, None)):
                        name = str(o5)
                for (s4,p4,o4) in g.triples((o2, ru.DATA_ITEM_TERM, None)):
                    value = str(o4)
                if name == "MD5":
                    md5_checksum = value

        # link Dataset to DatasetDistributions
        for (s,p,o) in g.triples((d, ru.SDO_DISTRIBUTIONS_TERM, None)):

            # file size
            for (s2,p2,o2) in g.triples((o, ru.SDO_SIZE_TERM, None)):
                fsize = str(o2)
                if file_size is None:
                    file_size = fsize
                else:
                    if file_size != fsize:
                        logging.fatal("file size mismatch")
                        sys.exit(1)

            for (s2,p2,o2) in g.triples((o, ru.RDF_TYPE_TERM, ru.SDO_DATA_DOWNLOAD_TERM)):
                m = re.match(r'^(gs|s3):\/\/.*', str(o))
                if m is not None:
                    distribs.append({'URI': str(o), 'size': file_size})
                    if m.group(1) == "gs":
                        gs_URI = str(o)
                    else:
                        s3_URI = str(o)
                
        # link Dataset to DataAcquisition (should be 1-1)
        data_acqs = []
        for (s,p,o) in g.triples((d, ru.PRODUCED_BY_TERM, None)):
            # TODO - replace SDO_ACTION_TERM with DATS_DATA_ACQUISITION TERM when https://github.com/datatagsuite/context/issues/4 resolved
            for (s2,p2,o2) in g.triples((o, ru.RDF_TYPE_TERM, ru.DATS_DATA_ACQUISITION_TERM)):
                data_acqs.append(o)

        if len(data_acqs) != 1:
            continue

        data_acq = data_acqs[0]

        # link DataAcquisition to RNA/DNA extract Material via input 
        for (s,p,o) in g.triples((data_acq, ru.HAS_INPUT_TERM, None)):
            rna_dna_extract = o

            # type - RNA or DNA extract

            # link to sample Material via derivesFrom
            for (s2,p2,o2) in g.triples((rna_dna_extract, ru.DERIVES_FROM_TERM, None)):

                # get sample body site / anatomy term
                anatomical_parts = []
                for (s3,p3,o3) in g.triples((o2, ru.DERIVES_FROM_TERM, None)):
                    for (s4,p4,o4) in g.triples((o3, ru.RDF_TYPE_TERM, ru.SDO_ANATOMICAL_STRUCTURE_TERM)):
                        term_name = None
                        # anatomy term name
                        for (s5,p5,o5) in g.triples((o3, ru.NAME_TERM, None)):
                            term_name = str(o5)
                        # anatomy term id
                        term_ids = {}
                        for (s5,p5,o5) in g.triples((o3, ru.CENTRAL_ID_TERM, None)):
                            # need to filter duplicates due to duplicate AnatomicalPart definitions
                            for (s6,p6,o6) in g.triples((o5, ru.CENTRAL_ID_TERM, None)):
                                term_ids[str(o6)] = True

                        tids = [t for t in term_ids.keys()]
                        if len(tids) != 1:
                            logging.fatal("found " + str(len(tids)) + " term ids for AnatomicalPart " + term_name + " linked to sample " + str(o2), ", gs_URI " + gs_URI)
                            sys.exit(1)

                        anatomical_parts.append({'name': term_name, 'id': tids[0]})

                n_anat_parts = len(anatomical_parts)
                # don't always have this info
                if n_anat_parts == 0:
                    logging.warn("found " + str(n_anat_parts) + " AnatomicalParts for sample material " + str(o2) + ", gs_URI " + gs_URI)
                    anatomical_parts.append({ 'name': '', 'id': '' })
                elif n_anat_parts > 1:
                    logging.fatal("found " + str(n_anat_parts) + " AnatomicalParts for sample material " + str(o2) + ", gs_URI " + gs_URI)
                    sys.exit(1)

                # link to subject Material via derivesFrom
                for (s3,p3,o3) in g.triples((o2, ru.DERIVES_FROM_TERM, None)):

                    # track link back from subject to data file(s)
                    if o3 not in subject_to_files:
                        subject_to_files[o3] = []
                    
                    datatype = None
                    # GTEx-specific
                    if re.search(r'GTEx', project_name):
                        if re.search(r'\/wgs\/', s3_URI):
                            datatype = 'WGS'
                        elif re.search(r'\/rnaseq/', s3_URI):
                            datatype = 'RNA-Seq'
                        else:
                            logging.fatal("couldn't parse seq type from URI " + s3_URI)
                            sys.exit(1)
                    # TOPMed-specific
                    elif re.search(r'TOPMed', project_name):
                        if re.search(r'\.cram', s3_URI):
                            datatype = 'WGS'
                        elif re.search(r'\.vcf', s3_URI):
                            datatype = 'SNP/CNV'
                        else:
                            logging.fatal("couldn't parse seq type from URI " + s3_URI)
                            sys.exit(1)
                    else:
                        logging.fatal("couldn't determine seq datatype from URI " + s3_URI)
                        sys.exit(1)

                    file_info = { 
                        'anatomical_part_name': anatomical_parts[0]['name'],
                        'anatomical_part_id': anatomical_parts[0]['id'],
                        'S3_URI': s3_URI,
                        'GS_URI': gs_URI,
                        'datatype': datatype,
                        'distribs': distribs,
                        'file_size': file_size,
                        'md5_checksum': md5_checksum
                        }

                        # TODO - extract sample characteristics

                    subject_to_files[o3].append(file_info)

    # generate tabular output
    col_headings = ["Project", "dbGaP_Study", "Study_Group", "Subject_ID"]
    col_headings.extend(sorted_char_names)
    col_headings.extend(["Anatomical_Part", "Anatomical_Part_ID"])
    col_headings.extend(["Datatype"])
    col_headings.extend(["File_Size", "MD5_Checksum"])                                    
    col_headings.extend(["AWS_URI", "GCP_URI"])
    print("\t".join(col_headings))

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
            
            # sort subjects
            subjects.sort(key=lambda x: subject_to_name[x])
            for s in subjects:
                subject_name = subject_to_name[s]
                col_vals = [project_name, dataset_id, group_name, subject_name]

                # subject characteristics
                subject_chars = subject_to_chars[s]
                for k in sorted_char_names:
                    if k in subject_chars:
                        col_vals.append(subject_chars[k]['value'])
                    else:
                        col_vals.append("")

                # ensure that subjects with no data files still get printed
                if s not in subject_to_files:
                    n_extra_cols = len(col_headings) - len(col_vals)
                    for c in range(0, n_extra_cols):
                        col_vals.append("")
                    print("\t".join(col_vals))
                    continue
                
                # data files linked to the subject
                data_files = subject_to_files[s]
                data_files.sort(key=lambda d: (d['anatomical_part_name'], d['datatype'], d['S3_URI']))

                for d in data_files:
                    col_vals_copy = col_vals[:]

                    # add data file-specific columns

                    # body site 
                    col_vals_copy.append(d['anatomical_part_name'])
                    col_vals_copy.append(d['anatomical_part_id'])

                    # data/file type
                    col_vals_copy.append(d['datatype'])

                    # TODO - add sample characteristics 

                    # add file size and MD5 checksum
                    if d['file_size'] is None:
                        col_vals_copy.append("")
                    else:
                        col_vals_copy.append(d['file_size'])

                    if d['md5_checksum'] is None:
                        col_vals_copy.append("")
                    else:
                        col_vals_copy.append(d['md5_checksum'])

                    # TODO - add .crai index files? 

                    # URIs
                    col_vals_copy.append(d['S3_URI'])
                    col_vals_copy.append(d['GS_URI'])

                    print("\t".join(col_vals_copy))


# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create tabular dump of DATS metadata using rdflib API calls.')
    parser.add_argument('--dats_file', help ='Path to TOPMed or GTEx DATS JSON file.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # parse JSON LD
    g = ru.read_json_ld_graph(args.dats_file)
    print_tabular_dump(g)

if __name__ == '__main__':
    main()
