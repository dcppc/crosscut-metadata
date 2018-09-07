#!/usr/bin/env python3

# Create DATS JSON description of GTEx public data.

import argparse
from ccmm.dats.datsobj import DatsObj, DatsObjCache
from collections import OrderedDict
from ccmm.dats.datsobj import DATSEncoder
import ccmm.gtex.dna_extracts
import ccmm.gtex.wgs_datasets
import ccmm.gtex.public_metadata
import ccmm.gtex.restricted_metadata
import ccmm.gtex.samples
import ccmm.gtex.subjects
import ccmm.gtex.parsers.portal_files as portal_files
import ccmm.gtex.parsers.github_files as github_files
import json
import logging
import os
import re
import sys

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

V7_SUBJECT_PHENOTYPES_FILE = 'GTEx_v7_Annotations_SubjectPhenotypesDS.txt'
V7_SAMPLE_ATTRIBUTES_FILE = 'GTEx_v7_Annotations_SampleAttributesDS.txt'

# manifest files from dcppc/data-stewards GitHub repo:
WGS_MANIFEST_FILE = 'wgs_cram_files_v7_hg38_datacommons_011516.txt'
RNASEQ_MANIFEST_FILE = 'rnaseq_cram_files_v7_dbGaP_011516.txt'

# ------------------------------------------------------
# Check sample ids between files
# ------------------------------------------------------

# check for sample and subject ids that appear in the manifest files but not the id dumps
def cross_check_ids(subjects, samples, manifest, filename, manifest_descr, source_descr):
    n_samp_found = 0
    n_samp_not_found = 0
    sample_d = {}
    n_subj_found = 0
    n_subj_not_found = 0
    subject_d = {}

    n_id_dump_subjects = len(subjects.keys())
    n_id_dump_samples = len(samples.keys())

    # count distinct subject and sample ids from the specified manifest file
    for k in manifest:
        entry = manifest[k]

        # check manifest sample_id
        sample_id = entry['sample_id']['raw_value']
        # sample ids should be unique:
        if sample_id in sample_d:
            logging.error("found duplicate sample id '" + sample_id + "' in " + filename)
            continue
        sample_d[sample_id] = True
        if sample_id in samples:
            n_samp_found += 1
        else:
            n_samp_not_found += 1
#            logging.warn("found sample id '" + sample_id + "' in manifest file but not id_dump file")

        # check subject_id
        m = re.match(r'^((GTEX|K)-[A-Z0-9+]+).*$', sample_id)
        if m is None:
            fatal_parse_error("couldn't parse GTEx subject id from sample_id '" + sample_id + "'")
        subject_id = m.group(1)
        if subject_id in subject_d:
            continue
        else:
            subject_d[subject_id] = True
        if subject_id in subjects:
            n_subj_found += 1
        else:
            n_subj_not_found += 1
            logging.warn("found subject id '" + subject_id + "' in manifest file but not id_dump file")

    logging.info("comparing GitHub GTEx " + manifest_descr + " manifest files with " + source_descr)
    samp_compare_str = '{:>10s}  sample_ids in {:>20s}: {:-6} / {:-6}'.format(manifest_descr, source_descr, n_samp_found, n_id_dump_samples) 
    samp_compare_str += '           '
    samp_compare_str += '{:>10s}  sample_ids  NOT in {:>20s}: {:-6} / {:-6}'.format(manifest_descr, source_descr, n_samp_not_found, n_id_dump_samples)
    logging.info(samp_compare_str)

    subj_compare_str = '{:>10s} subject_ids in {:>20s}: {:-6} / {:-6}'.format(manifest_descr, source_descr, n_subj_found,n_id_dump_subjects)
    subj_compare_str += '           '
    subj_compare_str += '{:>10s} subject_ids  NOT in {:>20s}: {:-6} / {:-6}'.format(manifest_descr, source_descr, n_subj_not_found, n_id_dump_subjects)
    logging.info(subj_compare_str)


# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for dbGaP GTEx public metadata.')
    parser.add_argument('--output_file', required=True, help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    parser.add_argument('--dbgap_public_xml_path', required=True, help ='Path to directory that contains public dbGaP metadata files e.g., *.data_dict.xml and *.var_report.xml')
    parser.add_argument('--dbgap_protected_metadata_path', required=False, help ='Path to directory that contains access-controlled dbGaP tab-delimited metadata files.')
    parser.add_argument('--max_output_samples', required=False, type=int, help ='Impose a limit on the number of sample Materials in the output DATS. For testing purposes only.')
    parser.add_argument('--subject_phenotypes_path', default=V7_SUBJECT_PHENOTYPES_FILE, required=False, help ='Path to ' + V7_SUBJECT_PHENOTYPES_FILE)
    parser.add_argument('--sample_attributes_path', default=V7_SAMPLE_ATTRIBUTES_FILE, required=False, help ='Path to ' + V7_SAMPLE_ATTRIBUTES_FILE)
    parser.add_argument('--data_stewards_repo_path', default='data-stewards', required=False, help ='Path to local copy of https://github.com/dcppc/data-stewards')
    parser.add_argument('--no_circular_links', action='store_true', help ='Whether to disallow circular links/paths within the JSON-LD output.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)
#    logging.basicConfig(level=logging.DEBUG)

    # read portal metadata for subjects and samples
    p_subjects = portal_files.read_subject_phenotypes_file(args.subject_phenotypes_path)
    p_samples = portal_files.read_sample_attributes_file(args.sample_attributes_path)
    portal_files.link_samples_to_subjects(p_samples, p_subjects)

    # read id dump and manifest files from GitHub data-stewards repo

    # id dumps
    subject_id_file = args.data_stewards_repo_path + "/gtex/v7/id_dumps/gtex_v7_subject_ids.txt"
    gh_subjects = github_files.read_subject_id_file(subject_id_file)
    sample_id_file = args.data_stewards_repo_path + "/gtex/v7/id_dumps/gtex_v7_sample_ids.txt"
    gh_samples = github_files.read_sample_id_file(sample_id_file)
    tissue_id_file = args.data_stewards_repo_path + "/gtex/v7/id_dumps/gtex_v7_tissue_ids.txt"
    gh_tissues = github_files.read_tissue_id_file(tissue_id_file)

    # manifest files
    protected_rnaseq_manifest = args.data_stewards_repo_path + "/gtex/v7/manifests/protected_data/" + RNASEQ_MANIFEST_FILE
    protected_rnaseq_files = github_files.read_protected_rnaseq_manifest(protected_rnaseq_manifest)
    protected_wgs_manifest = args.data_stewards_repo_path + "/gtex/v7/manifests/protected_data/" + WGS_MANIFEST_FILE
    protected_wgs_files = github_files.read_protected_wgs_manifest(protected_wgs_manifest)

    # compare GitHub manifest files with GitHub id dumps
    cross_check_ids(gh_subjects, gh_samples, protected_rnaseq_files, protected_rnaseq_manifest, "RNA-Seq", "GitHub id dumps")
    cross_check_ids(gh_subjects, gh_samples, protected_wgs_files, protected_wgs_manifest, "WGS","GitHub id dumps")

    # compare GitHub manifest files with GTEx Portal metdata files
    cross_check_ids(p_subjects, p_samples, protected_rnaseq_files, protected_rnaseq_manifest, "RNA-Seq", "GTEx Portal metadata")
    cross_check_ids(p_subjects, p_samples, protected_wgs_files, protected_wgs_manifest, "WGS","GTEx Portal metadata")

    # create top-level dataset
    gtex_dataset = ccmm.gtex.wgs_datasets.get_dataset_json()

    # index dbGaP study Datasets by id
    dbgap_study_datasets_by_id = {}
    for tds in gtex_dataset.get("hasPart"):
        dbgap_study_id = tds.get("identifier").get("identifier")
        if dbgap_study_id in dbgap_study_datasets_by_id:
            logging.fatal("encountered duplicate study_id " + dbgap_study_id)
            sys.exit(1)
        m = re.match(r'^(phs\d+\.v\d+)\.p\d+$', dbgap_study_id)
        if m is None:
            logging.fatal("unable to parse study_id " + dbgap_study_id)
            sys.exit(1)
        dbgap_study_datasets_by_id[m.group(1)] = tds

    # read public dbGaP metadata
    pub_xp = args.dbgap_public_xml_path
    restricted_mp = args.dbgap_protected_metadata_path
    # read public metadata
    dbgap_study_pub_md = ccmm.gtex.public_metadata.read_study_metadata(pub_xp)
    # there should be only one study
    study_ids = [k for k in dbgap_study_pub_md.keys()]
    n_study_ids =len(study_ids)
    study_id = study_ids[0]
    if n_study_ids != 1:
        logging.fatal("read " + str(n_study_ids) + " dbGaP studies from " + pub_xp)
        sys.exit(1)

    dbgap_study_dataset = dbgap_study_datasets_by_id[study_id]
    dbgap_study_md = dbgap_study_pub_md[study_id]
    dbgap_study_md['dbgap_vars'] = ccmm.gtex.public_metadata.add_study_vars(dbgap_study_dataset, dbgap_study_md)

    # build index into dbGaP variables - indexed by variable name and then consent group suffix ("", "c1", "c2")
    name_to_vars = {}
    logging.info("indexing " + str(len(dbgap_study_md['dbgap_vars'].keys())) + " dbGaP variables")

    for dbgap_id in sorted(dbgap_study_md['dbgap_vars']):
        dbv = dbgap_study_md['dbgap_vars'][dbgap_id]
        name = dbv.get("name").get("value")
        dbgap_id = dbv.get("identifier").get("identifier")
        m = re.match(r'^(.*)(\.(c\d+))$', dbgap_id)

        if m is None:
            prefix = dbgap_id
            suffix = ""
        else:
            prefix = m.group(1)
            suffix = m.group(3)

        if name not in name_to_vars:
            name_to_vars[name] = {}
        if suffix in name_to_vars[name]:
            name_to_vars[name][suffix].append(dbv)
        else:
            name_to_vars[name][suffix] = [ dbv ]

    # mapping may be ambiguous for SUBJID, SAMPID
    # workaround - use lexical order to break ties
    # TODO - explicitly use SUBJID mapping from Subject file, SAMPID from Sample file
    for n in name_to_vars:
        nv = name_to_vars[n]
        suffixes = [k for k in nv.keys()]
        for suffix in suffixes:
            list = nv[suffix]
            list.sort(key=lambda x: x.get("name").get("value"))
            nv[suffix] = list[0]
            
    # set 2nd level types to be the same as the top-level types: WGS and RNA-Seq
    dbgap_study_dataset.set("types", gtex_dataset.get("types"))

    # cache used to minimize duplication of JSON objects in JSON-LD output
    cache = DatsObjCache()

    # --------------------------
    # subjects
    # --------------------------

    # create subjects based on GTEx Portal subject phenotype file and GitHub data-stewards id dump
    dats_subjects_d = ccmm.gtex.subjects.get_subjects_dats_materials(cache, p_subjects, gh_subjects, name_to_vars)
    # sorted list of subjects
    dats_subjects_l = sorted([dats_subjects_d[s] for s in dats_subjects_d], key=lambda s: s.get("name"))

    # TODO - add consent groups, of which GTEx has 2: 0=didn't participate, 1=General Research Use (GRU)
    
    # create StudyGroup that lists all the subjects
    all_subjects = DatsObj("StudyGroup", [
            ("name", "all subjects"),
            # subjects appear in full here, but id references will be used elsewhere in the instance:
                ("members", dats_subjects_l)
            ])

    # create link back from each subject to the parent StudyGroup
    if args.no_circular_links:
        logging.warn("not creating Subject level circular links because of --no_circular_links option")
    else:
        for s in dats_subjects_l:
            cl = s.get("characteristics")
            cl.append(DatsObj("Dimension", [("name", "member of study group"), ("values", [ all_subjects.getIdRef() ])]))

    dats_study = DatsObj("Study", [
            ("name", "GTEx"),
            ("studyGroups", [ all_subjects ])
            ])

    # link Study to Dataset
    dbgap_study_dataset.set("producedBy", dats_study)

    # --------------------------
    # sample Materials
    # --------------------------

    # create samples based on GTEx Portal sample attributes file and GitHub data-stewards id dump
    dats_samples_d = ccmm.gtex.samples.get_samples_dats_materials(cache, dats_subjects_d, p_samples, gh_samples, name_to_vars)
    # sorted list of samples
    dats_samples_l = sorted([dats_samples_d[s] for s in dats_samples_d], key=lambda s: s.get("name"))
    if args.max_output_samples is not None:
        dats_samples_l = dats_samples_l[0:int(args.max_output_samples)]
        logging.warn("limiting output to " + str(len(dats_samples_l)) + " sample(s) due to value of --max_output_samples")
    dbgap_study_dataset.set("isAbout", dats_samples_l)

    # --------------------------
    # file Datasets
    # --------------------------

    file_datasets_l = []

    # WGS CRAM
    wgs_dats_file_datasets_l = ccmm.gtex.samples.get_files_dats_datasets(cache, dats_samples_d, p_samples, gh_samples, protected_wgs_files, args.no_circular_links)
    logging.info("adding Datasets for " + str(len(wgs_dats_file_datasets_l)) + " WGS CRAM files")
    file_datasets_l.extend(wgs_dats_file_datasets_l)

    # RNA-Seq CRAM
    rnaseq_dats_file_datasets_l = ccmm.gtex.samples.get_files_dats_datasets(cache, dats_samples_d, p_samples, gh_samples, protected_rnaseq_files, args.no_circular_links)
    logging.info("adding Datasets for " + str(len(rnaseq_dats_file_datasets_l)) + " RNA-Seq CRAM files")
    file_datasets_l.extend(rnaseq_dats_file_datasets_l)

    dbgap_study_dataset.set("hasPart", file_datasets_l)

    # TODO - handle restricted-access (meta)data
    if restricted_mp is not None:
        logging.fatal("restricted-access metadata conversion not yet supported in this version of the script")
        sys.exit(1)
#            study_restricted_md = ccmm.gtex.restricted_metadata.read_study_metadata(restricted_mp)
#            dna_extracts = ccmm.gtex.dna_extracts.get_dna_extracts_json_from_restricted_metadata(study, study_md, study_restricted_md[study_id])
#            study.set("isAbout", dna_extracts)

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(gtex_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
