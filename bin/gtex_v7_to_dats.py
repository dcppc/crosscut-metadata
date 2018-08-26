#!/usr/bin/env python3

# Create DATS JSON description of GTEx public data.

import argparse
from ccmm.dats.datsobj import DatsObj
from collections import OrderedDict
from ccmm.dats.datsobj import DATSEncoder
import ccmm.gtex.dna_extracts
import ccmm.gtex.wgs_datasets
import ccmm.gtex.public_metadata
import ccmm.gtex.restricted_metadata
#import ccmm.gtex.parsers.github_files as github_files
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

#RNASEQ_SMAFRZE = 'RNASEQ'

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
#            logging.warn("found subject id '" + subject_id + "' in manifest file but not id_dump file")

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
##    parser.add_argument('--max_output_samples', required=False, help ='Impose a limit on the number of sample Materials in the output DATS. For testing purposes only.')
    parser.add_argument('--subject_phenotypes_path', default=V7_SUBJECT_PHENOTYPES_FILE, required=False, help ='Path to ' + V7_SUBJECT_PHENOTYPES_FILE)
    parser.add_argument('--sample_attributes_path', default=V7_SAMPLE_ATTRIBUTES_FILE, required=False, help ='Path to ' + V7_SAMPLE_ATTRIBUTES_FILE)
    parser.add_argument('--data_stewards_repo_path', default='data-stewards', required=False, help ='Path to local copy of https://github.com/dcppc/data-stewards')
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
    protected_rnaseq_manifest = args.data_stewards_repo_path + "/gtex/v7/manifests/protected_data/rnaseq_cram_files_v7_dbGaP_011516.txt"
    protected_rnaseq_files = github_files.read_protected_rnaseq_manifest(protected_rnaseq_manifest)
    protected_wgs_manifest = args.data_stewards_repo_path + "/gtex/v7/manifests/protected_data/wgs_cram_files_v7_hg38_dbGaP_011516.txt"
    protected_wgs_files = github_files.read_protected_wgs_manifest(protected_wgs_manifest)

    # compare GitHub manifest files with GitHub id dumps
    cross_check_ids(gh_subjects, gh_samples, protected_rnaseq_files, protected_rnaseq_manifest, "RNA-Seq", "GitHub id dumps")
    cross_check_ids(gh_subjects, gh_samples, protected_wgs_files, protected_wgs_manifest, "WGS","GitHub id dumps")

    # compare GitHub manifest files with GTEx Portal metdata files
    cross_check_ids(p_subjects, p_samples, protected_rnaseq_files, protected_rnaseq_manifest, "RNA-Seq", "GTEx Portal metadata")
    cross_check_ids(p_subjects, p_samples, protected_wgs_files, protected_wgs_manifest, "WGS","GTEx Portal metadata")

    # TODO - create DATS subjects and samples based on the manifest files

    # create top-level dataset
    gtex_dataset = ccmm.gtex.wgs_datasets.get_dataset_json()

    # index studies by id
    studies_by_id = {}
    for tds in gtex_dataset.get("hasPart"):
        study_id = tds.get("identifier").get("identifier")
        if study_id in studies_by_id:
            logging.fatal("encountered duplicate study_id " + study_id)
            sys.exit(1)
        m = re.match(r'^(phs\d+\.v\d+)\.p\d+$', study_id)
        if m is None:
            logging.fatal("unable to parse study_id " + study_id)
            sys.exit(1)
        studies_by_id[m.group(1)] = tds

    # read public dbGaP metadata
    pub_xp = args.dbgap_public_xml_path
    restricted_mp = args.dbgap_protected_metadata_path
    # read public metadata
    study_pub_md = ccmm.gtex.public_metadata.read_study_metadata(pub_xp)
    
    # record study variables as dimensions of the study/Dataset
    def add_study_vars(study, study_md):
        # Subject Phenotype study variables
        if 'Subject_Phenotypes' in study_md:
            subj_data = study_md['Subject_Phenotypes']['var_report']['data']
            subj_vars = subj_data['vars']
        else:
            subj_vars = []
        # Sample Attribute study variables
        samp_data = study_md['Sample_Attributes']['var_report']['data']
        samp_vars = samp_data['vars']
        all_vars = subj_vars[:]
        all_vars.extend(samp_vars)
        dbgap_vars = {}

        # create a Dimension for each one
        for var in all_vars:
            var_name = var['var_name']
            id = DatsObj("Identifier", [
                    ("identifier",  var['id']),
                    ("identifierSource", "dbGaP")])

            dim = DatsObj("Dimension", [
                    ("identifier", id),
                    ("name", DatsObj("Annotation", [("value", var_name)])),
                    ("description", var['description'])
                    #To do: include stats
                    ])  
            study.getProperty("dimensions").append(dim)

            # track dbGaP variable Dimensions by dbGaP id
            if var['id'] in dbgap_vars:
                logging.fatal("duplicate definition found for dbGaP variable " + var_name + " with accession=" + var['id'])
                sys.exit(1)
            dbgap_vars[var['id']] = dim

        return dbgap_vars

    # case 1: process public metadata only (i.e., data dictionaries and variable reports only)
    if restricted_mp is None:
        # generate sample entry for each study for which we have metadata
        for study_id in study_pub_md:
            study = studies_by_id[study_id]
            study_md = study_pub_md[study_id]
            study_md['dbgap_vars'] = add_study_vars(study, study_md)
            # create dummy/representative DATS instance based on variable reports
            # TODO - signal somewhere directly in the DATS that this is not real subject-level data (subject/sample id may be sufficient)
            dna_extract = ccmm.gtex.dna_extracts.get_synthetic_single_dna_extract_json_from_public_metadata(study, study_md)
            # insert synthetic sample into relevant study/Dataset
            study.set("isAbout", [dna_extract])

    # case 2: process both public metadata and access-controlled dbGaP metadata
    else:
        study_restricted_md = ccmm.gtex.restricted_metadata.read_study_metadata(restricted_mp)
        for study_id in study_pub_md:
            study = studies_by_id[study_id]
            study_md = study_pub_md[study_id]
            study_md['dbgap_vars'] = add_study_vars(study, study_md)
            dna_extracts = ccmm.gtex.dna_extracts.get_dna_extracts_json_from_restricted_metadata(study, study_md, study_restricted_md[study_id])
            study.set("isAbout", dna_extracts)

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(gtex_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
