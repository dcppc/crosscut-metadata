#!/usr/bin/env python3

# Create DATS JSON description of TOPMed public data.

import argparse
from ccmm.dats.datsobj import DatsObj, DatsObjCache
from collections import OrderedDict
from ccmm.dats.datsobj import DATSEncoder
import ccmm.topmed.samples
import ccmm.topmed.subjects
import ccmm.topmed.dna_extracts
import ccmm.topmed.wgs_datasets
import ccmm.topmed.public_metadata
import ccmm.topmed.restricted_metadata
import ccmm.topmed.parsers.manifest_files as manifest_files
import json
import logging
import os
import re
import sys

# synthetic subject and sample ids
SUBJ_ID = 1
SAMP_ID = 1

# ------------------------------------------------------
# Create DATS StudyGroups from restricted access data
# ------------------------------------------------------

# Create DATS StudyGroup corresponding to a consent group
def make_consent_group(args, group_name, group_index, subject_l, dats_subject_d):

    # find DATS subject that corresponds to each named subject
    dats_subjects_l = []
    # parallel array in which existing subjects are represented by idref
    dats_subjects_idrefs_l = []

    for s in subject_l:
        if s['dbGaP_Subject_ID'] not in dats_subject_d:
            logging.warn("Subject " + s['dbGaP_Subject_ID'] + " not found")
            sys.exit(1)

        ds = dats_subject_d[s['dbGaP_Subject_ID']]
        dats_subjects_l.append(ds)
        dats_subjects_idrefs_l.append(ds.getIdRef())

    # create StudyGroup and associated ConsentInfo

    # only 2 consent groups in GTEx study:
    #   0 - Subjects did not participate in the study, did not complete a consent document and 
    #       are included only for the pedigree structure and/or genotype controls, such as HapMap subjects
    #   1 - General Research Use (GRU)
    consent_info = None
    if group_name == "General Research Use (GRU)":
        # Data Use Ontology for consent info - http://www.obofoundry.org/ontology/duo.html
        #  http://purl.obolibrary.org/obo/DUO_0000005 - "general research use and clinical care"
        #  "This primary category consent code indicates that use is allowed for health/medical/biomedical 
        # purposes and other biological research, including the study of population origins or ancestry."
        consent_info = DatsObj("ConsentInfo", [
            ("name", group_name),
            ("abbreviation", "GRU"),
            ("description", group_name),
            ("relatedIdentifiers", [
                DatsObj("RelatedIdentifier", [("identifier", "http://purl.obolibrary.org/obo/DUO_0000005")])
            ])
        ])
    elif group_name == "Health/Medical/Biomedical (HMB)":
        # http://purl.obolibrary.org/obo/DUO_0000006 - "health/medical/biomedical research and clinical care"
        # "This primary category consent code indicates that use is allowed for health/medical/biomedical purposes; 
        # does not include the study of population origins or ancestry."
        consent_info = DatsObj("ConsentInfo", [
            ("name", group_name),
            ("abbreviation", "HMB"),
            ("description", group_name),
            ("relatedIdentifiers", [
                DatsObj("RelatedIdentifier", [("identifier", "http://purl.obolibrary.org/obo/DUO_0000006")])
            ])
        ])
    elif group_name == "Disease-Specific (COPD and Smoking, RD) (DS-CS-RD)":
        # TODO -  use more specific DUO term
        # http://purl.obolibrary.org/obo/DUO_0000006 - "disease-specific research and clinical care"
        consent_info = DatsObj("ConsentInfo", [
            ("name", group_name),
            ("abbreviation", "DS-CS-RD"),
            ("description", group_name),
            ("relatedIdentifiers", [
                DatsObj("RelatedIdentifier", [("identifier", "http://purl.obolibrary.org/obo/DUO_0000007")])
            ])
        ])
    elif group_name == "Subjects did not participate in the study, did not complete a consent document and are included only for the pedigree structure and/or genotype controls, such as HapMap subjects":
        consent_info = DatsObj("ConsentInfo", [
            ("name", group_name),
            ("description", group_name)
        ])
    else:
        logging.fatal("unrecognized consent group " + group_name)
        sys.exit(1)

    group = DatsObj("StudyGroup", [
        ("name", group_name),
        ("members", dats_subjects_idrefs_l),
        ("size", len(dats_subjects_idrefs_l)),
        ("consentInformation", [ consent_info ])
    ])

    # create link back from each subject to the parent StudyGroup
    if args.no_circular_links:
        logging.warn("not creating Subject level circular links because of --no_circular_links option")
    else:
        for s in dats_subjects_l:
            cl = s.get("characteristics")
            cl.append(DatsObj("Dimension", [("name", "member of study group"), ("values", [ group.getIdRef() ])]))
    return group

def add_study_groups(cache, args, study_md, study_restricted_md, subjects_l, dats_study, study_id):
    # index DATS subjects by dbGaP_Subject_ID
    subjects_d = {}
    for s in subjects_l:
        chars = s.get("characteristics")
        dbgap_id = None
        for c in chars:
            if c.get("name").get("value") == "dbGaP_Subject_ID":
                dbgap_id = c.get("values")[0]
                break
        if dbgap_id is None:
            logging.fatal("couldn't get dbGaP_Subject_ID for subject " + s.get("name"))
            sys.exit(1)
        subjects_d[dbgap_id] = s

    d = study_restricted_md
    # get subject info
    subj = d[study_id]['Subject']
    # group by consent group
    cid_to_subjects = {}
    for s in subj['data']['rows']:
        cg = s['CONSENT']
        if cg not in cid_to_subjects:
            cid_to_subjects[cg] = []
        cid_to_subjects[cg].append(s)
            
    # mapping for consent group codes
    c_vars = [c for c in study_md['Subject']['var_report']['data']['vars'] if c['var_name'] == "CONSENT" and not re.search(r'\.c\d+$', c['id'])]
    if len(c_vars) != 1:
        logging.fatal("found "+ str(len(c_vars)) + " CONSENT variables in Subject var_report XML")
        sys.exit(1)
    c_var = c_vars[0]
    c_var_codes = c_var['total']['stats']['values']
    code_to_c_var = {}
    for cvc in c_var_codes:
        code_to_c_var[cvc['code']] = cvc
           
    # create StudyGroup and ConsentInfo for each consent group
    sorted_cids = sorted(cid_to_subjects.keys())
    for cid in sorted_cids:
        slist = cid_to_subjects[cid]
        n_subjects = len(slist)
        cvc = code_to_c_var[cid]
        if n_subjects != int(cvc['count']):
            logging.fatal("subject count mismatch in consent group " + cid)
            sys.exit(1)
        logging.info("adding StudyGroup for " + str(n_subjects) + " subject(s) in consent group " + cid + ": " + cvc['name'])
        study_group = make_consent_group(args, cvc['name'], cid, slist, subjects_d)
        # add study group to DATS Study
        dats_study.get("studyGroups").append(study_group)

# ------------------------------------------------------
# Process a single study
# ------------------------------------------------------

def process_study(args, cache, topmed_dataset, dbgap_study_dataset, study_id, study_pub_md, study_restricted_md, sample_manifest):
    global SUBJ_ID, SAMP_ID
    study_md = study_pub_md[study_id]        
    study_res_md = None

    # add DATS Dimensions for dbGaP study variables
    sv = ccmm.topmed.public_metadata.add_study_vars(dbgap_study_dataset, study_md)
    study_md['id_to_var'] = sv['id_to_var']
    study_md['type_name_cg_to_var'] = sv['type_name_cg_to_var']

    # --------------------------
    # subjects
    # --------------------------
    dats_subjects_d = {}

    # create DATS subject Materials
    if study_restricted_md is None:
        # create single dummy subject
        dbgap_subj_id = "{:07d}".format(SUBJ_ID)
        subj_id = "SU{:07d}".format(SUBJ_ID)
        SUBJ_ID += 1
        dats_subjects_d = ccmm.topmed.subjects.get_synthetic_subject_dats_material_from_public_metadata(cache, dbgap_study_dataset, study_md, dbgap_subj_id, subj_id)
    else:
        # create complete subject list from restricted metadata
        study_res_md = study_restricted_md[study_id]
        dats_subjects_d = ccmm.topmed.subjects.get_subjects_dats_materials_from_restricted_metadata(cache, dbgap_study_dataset, study_md, study_res_md)

    # sorted list of subjects
    dats_subjects_l = sorted([dats_subjects_d[s] for s in dats_subjects_d], key=lambda s: s.get("name"))
    logging.info("created " + str(len(dats_subjects_l)) + " subject Materials")

    # create 'all subjects' StudyGroup
    all_subjects = DatsObj("StudyGroup", [
        ("name", "all subjects"),
        # subjects appear in full here, but id references will be used elsewhere in the instance:
        ("members", dats_subjects_l),
        ("size", len(dats_subjects_l))
    ])
    logging.info("adding 'all subjects' StudyGroup for " + str(len(dats_subjects_l)) + " subject(s)")
                
    # create Study
    dats_study = DatsObj("Study", [
        ("name", dbgap_study_dataset.get("identifier").get("identifier")),
        ("studyGroups", [ all_subjects ])
    ])
    # link Study to Dataset
    dbgap_study_dataset.set("producedBy", dats_study)

    # create additional StudyGroups for protected metadata
    if study_restricted_md is not None:
        add_study_groups(cache, args, study_md, study_restricted_md, dats_subjects_l, dats_study, study_id)

    # --------------------------
    # samples
    # --------------------------
    dats_samples_d = {}

    # create DATS sample Materials (i.e., RNA/DNA extracts and biological samples)
    if study_restricted_md is None:
        # create single dummy sample
        dbgap_samp_id = "{:07d}".format(SAMP_ID)
        samp_id = "SA{:07d}".format(SAMP_ID)
        SAMP_ID += 1
        dats_samples_d = ccmm.topmed.samples.get_synthetic_sample_dats_material_from_public_metadata(cache, dats_subjects_l[0], dbgap_study_dataset, study_md, dbgap_samp_id, samp_id)
    else:
        # samples indexed by dbGaP_Sample_ID from restricted metadata
        dats_samples_d = ccmm.topmed.samples.get_samples_dats_materials_from_restricted_metadata(cache, dats_subjects_d, dbgap_study_dataset, study_md, study_res_md)

    dats_samples_l = sorted([dats_samples_d[s] for s in dats_samples_d], key=lambda s: s.get("name"))
    logging.info("created " + str(len(dats_samples_l)) + " sample Materials")
    dbgap_study_dataset.set("isAbout", dats_samples_l)

    # --------------------------
    # file Datasets
    # --------------------------

    if study_restricted_md is not None:
        file_datasets_l = ccmm.topmed.samples.get_files_dats_datasets(cache, dats_samples_d, sample_manifest, args.no_circular_links)
        logging.info("adding file Datasets for " + str(len(file_datasets_l)) + " sample(s)")
        dbgap_study_dataset.set("hasPart", file_datasets_l)

        # filter samples not referenced by Datasets
        referenced_samples = {}
        for fd in file_datasets_l:
            data_acq = fd.get("producedBy")
            for ds in data_acq.get("input"):
                ds_id = ds.get("@id")
                referenced_samples[ds_id] = True

        filtered_dats_samples_l = []
        for ds in dats_samples_l:
            if ds.get("@id") in referenced_samples:
                filtered_dats_samples_l.append(ds)

        nfs = len(filtered_dats_samples_l)
        logging.info(str(nfs) + " sample Materials remain after filtering non-TOPMed samples")
        dbgap_study_dataset.set("isAbout", filtered_dats_samples_l)

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for TOPMed public metadata.')
    parser.add_argument('--dbgap_accession_list', required=True, help ='Comma-delimited list of dbGaP accession numbers for the TOPMed studies to convert to DATS.')
    parser.add_argument('--output_file', required=True, help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    parser.add_argument('--dbgap_public_xml_path', required=True, help ='Path to directory that contains public dbGaP pheno_variable_summary files, grouped into subdirectories by accession number.')
    parser.add_argument('--dbgap_protected_metadata_path', required=False, help ='Path to directory that contains access-controlled dbGaP tab-delimited metadata files.')
    parser.add_argument('--manifest_file', required=False, help ='Path to directory that contains TOPMed file manifest for access-controlled data.')
    parser.add_argument('--no_circular_links', action='store_true', help ='Whether to disallow circular links/paths within the JSON-LD output.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)
#    logging.basicConfig(level=logging.DEBUG)

    # get accession list
    acc_l = []
    for acc in args.dbgap_accession_list.split(","):
        acc_l.append(acc)

    # create top-level dataset containing studies named in args.dbgap_accession_list
    topmed_dataset = ccmm.topmed.wgs_datasets.get_dataset_json(acc_l)

    # index studies by id
    studies_by_id = {}
    for tds in topmed_dataset.get("hasPart"):
        study_id = tds.get("identifier").get("identifier")
        if study_id in studies_by_id:
            logging.fatal("encountered duplicate study_id " + study_id)
            sys.exit(1)
        m = re.match(r'^(phs\d+\.v\d+)\.p\d+$', study_id)
        if m is None:
            logging.fatal("unable to parse study_id " + study_id)
            sys.exit(1)
        studies_by_id[m.group(1)] = tds
        logging.info("indexed study " + m.group(1))

    # read manifest file
    sample_manifest = None
    if args.dbgap_protected_metadata_path is not None:
        if args.manifest_file is None:
            logging.fatal("--dbgap_protected_metadata_path given, but no --manifest_file specified")
            sys.exit(1)
        sample_manifest = manifest_files.read_manifest(args.manifest_file)

    for acc in acc_l:
        # cache used to minimize duplication of JSON objects in JSON-LD output
        # TODO - note that this disallows sharing of subjects (for example) across studies
        cache = DatsObjCache()
        
        # read public metadata
        pub_xp = args.dbgap_public_xml_path + "/" + acc
        study_pub_md = ccmm.topmed.public_metadata.read_study_metadata(pub_xp)

        # read protected metadata
        restricted_mp = args.dbgap_protected_metadata_path
        study_restricted_md = None
        if restricted_mp is not None:
            restricted_mp = restricted_mp + "/" + acc
            study_restricted_md = ccmm.topmed.restricted_metadata.read_study_metadata(restricted_mp)

        for study_id in study_pub_md:
            dbgap_study_dataset = studies_by_id[study_id]
            process_study(args, cache, topmed_dataset, dbgap_study_dataset, study_id, study_pub_md, study_restricted_md, sample_manifest)

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(topmed_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
