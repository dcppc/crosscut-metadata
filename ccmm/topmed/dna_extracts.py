#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
import ccmm.dats.util as util
from collections import OrderedDict
import csv
import json
import logging
import os
import re
import sys

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

# ------------------------------------------------------
# DATS JSON Output
# ------------------------------------------------------

# Pick representative and/or legal value for each variable
def pick_var_values(vars):
    res = {}

    for var in vars:
        vname = var['var_name']
        values = None
        value = None

        # these variables are handled elsewhere
        if re.match(r'(SUBJECT|SAMPLE)_ID', vname):
            continue
        # controlled vocabulary
        elif re.match(r'encoded values?', var['reported_type']):
            values = var['total']['stats']['values']
        elif (var['reported_type'] == 'string') or (var['calculated_type'] == 'string'):
            values = var['total']['stats']['values']
        # take the median if defined
        elif (var['reported_type'] == 'integer') or (var['calculated_type'] == 'integer'):
            value = var['total']['stats']['median']
        else:
            logging.fatal("unexpected variable reported_type=" + var['reported_type'])
            sys.exit(1)

        if values is not None:
            # sort values by count and then alphanumerically
            sorted_values = sorted(values, key=lambda x: int(x['count']), reverse=True)
            sorted_values.sort(key=lambda x: x['name'])
            value = sorted_values[0]['name']

        res[vname] = value

    return res

# Generate DATS JSON for a single sample/DNA extract
def get_single_dna_extract_json(study, subj_var_values, samp_var_values):

    # all samples in TOPMed WGS phase are blood samples
    if samp_var_values['BODY_SITE'] != 'Blood':
        logging.fatal("encountered BODY_SITE other than 'Blood' in TOPMed sample metadata - " + samp_var_values['BODY_SITE'])
        sys.exit(1)

    anatomy_name = "blood"
    anat_id = "0000178"

    anatomy_identifier = OrderedDict([
            ("identifier",  "UBERON:" + str(anat_id)),
            ("identifierSource", "UBERON")])
    anatomy_alt_ids = [OrderedDict([
                ("identifier", "http://purl.obolibrary.org/obo/UBERON_" + str(anat_id)),
                ("identifierSource", "UBERON")])]

    # extract subject attributes
    gender = None
    age = None
    for name in subj_var_values:
        if name == "GENDER":
            gender = subj_var_values[name].lower()
        elif name == "VISIT_AGE":
            age = subj_var_values[name]
    # TODO - determine what other subject attributes can be mapped directly to core DATS objects

    # place original dbGaP subject metadata into extraProperties
    # TODO - consider alternative of doing this only for un-harmonized metadata 
    subj_extra_props = [DatsObj("CategoryValuesPair", [("category", xp), ("values", subj_var_values[xp])]) for xp in subj_var_values ]

    # extract sample attributes
    for name in samp_var_values:
        if name == 'SEQUENCING_CENTER':
            # TODO - determine which DATS objects (e.g., biological sample, DNA prep, sequence data) this property should attach to
            pass

    # TODO - determine what other subject attributes can be mapped directly to core DATS objects
    # e.g., IS_TUMOR -> bearerOfDisease ("the pathology affecting the material...")

    # place original dbGaP sample metadata into extraProperties
    samp_extra_props = [DatsObj("CategoryValuesPair", [("category", xp), ("values", samp_var_values[xp])]) for xp in samp_var_values ]

    # anatomical part
    anatomical_part = DatsObj("AnatomicalPart", [
            ("name", anatomy_name),
            ("identifier", anatomy_identifier),
            ("alternateIdentifiers", anatomy_alt_ids)
            ])

    subject_sex = DatsObj("Dimension", [
            ("name", { "value": "Gender" }),
            ("description", "Gender of the subject"),
            ("values", [ gender ])
            ])

    subject_age = DatsObj("Dimension", [
            ("name", { "value": "Age" }),
            ("description", "Age of the subject"),
            ("values", [ age ])
            ])
    
    subject_characteristics = [
        subject_sex,
        subject_age
        ]

    human_t = util.get_taxon_human()
    subj_id = subj_var_values['SUBJECT_ID']
    dbgap_subj_id = subj_var_values['dbGaP_Subject_ID']
    samp_id = samp_var_values['SAMPLE_ID']
    dbgap_samp_id = samp_var_values['dbGaP_Sample_ID']

    study_title = study.get("title")

    # human experimental subject/patient
    subject_material = DatsObj("Material", [
            ("name", subj_id),
            ("identifier", { "identifier": subj_id }),
            ("alternateIdentifiers", [ util.get_alt_id(dbgap_subj_id, "dbGaP") ]),
            ("description", study_title + " subject " + subj_id),
            ("characteristics", subject_characteristics),
            ("taxonomy", human_t),
            ("roles", util.get_donor_roles()),
            ("extraProperties", subj_extra_props)
            ])

    # biological/tissue sample
    sample_name = samp_id
    biological_sample_material = DatsObj("Material", [
            ("name", sample_name),
            ("identifier", { "identifier": samp_id }),
            ("alternateIdentifiers", [ util.get_alt_id(dbgap_samp_id, "dbGaP") ]),
            ("description", anatomy_name + " specimen collected from subject " + subj_id),
            ("taxonomy", human_t),
            ("roles", [ OrderedDict([("value", "specimen"), ("valueIRI", "")]) ]),
            ("derivesFrom", [ subject_material, anatomical_part ]),
            ("extraProperties", samp_extra_props)
            ])

    # DNA extracted from tissue sample
    dna_material = DatsObj("Material", [
            ("name", "DNA from " + sample_name),
            ("description", "DNA extracted from " + anatomy_name + " specimen collected from subject " + subj_id),
            ("taxonomy", human_t),
            ("roles", [ OrderedDict([("value", "DNA extract"), ("valueIRI", "")])]),
            ("derivesFrom", [ biological_sample_material ])
            ])

    return dna_material

# Generate synthetic data for a single sample based on the public variable summaries.
def get_synthetic_single_dna_extract_json_from_public_metadata(study, study_md):

    # Subject summary data
    subj_data = study_md['Subject_Phenotypes']['var_report']['data']
    subj_vars = subj_data['vars']
    # pick representative and/or legal value for each variable
    subj_var_values = pick_var_values(subj_vars)
    logging.debug("subj_var_values=" + json.dumps(subj_var_values, indent=2))

    # Sample summary data
    samp_data = study_md['Sample_Attributes']['var_report']['data']
    samp_vars = samp_data['vars']
    # pick representative and/or legal value for each variable
    samp_var_values = pick_var_values(samp_vars)
    logging.debug("samp_var_values=" + json.dumps(samp_var_values, indent=2))

    # assign dummy ids: subject and sample ids are protected data
    samp_var_values['dbGaP_Sample_ID'] = "0000000"
    samp_var_values['SAMPLE_ID'] = "SA0000000"

    subj_var_values['dbGaP_Subject_ID'] = "0000000"
    subj_var_values['SUBJECT_ID'] = "SU0000000"

    return get_single_dna_extract_json(study, subj_var_values, samp_var_values)

def index_dicts(dict_list, key):
    index = {}
    for d in dict_list:
        keyval = d[key]
        if keyval in index:
            logging.fatal("duplicate key value (" + keyval + ") building index")
        index[keyval] = d
    return index

def link_samples_to_subjects(samples, subjects):
    for s in samples:
        sample = samples[s]
        dbgap_samp_id = sample['dbGaP_Sample_ID']
        dbgap_subj_id = sample['dbGaP_Subject_ID']
        sample['subject'] = subjects[dbgap_subj_id]

# TODO - cut and paste from ccmm.gtex.rna_extracts
def print_subject_sample_count_histogram(samples):
    print("Histogram of number of subjects that have a given number of samples")

    # count samples per subject
    subject_sample_count = {}
    for s in samples:
        sample = samples[s]
        subject = sample['dbGaP_Subject_ID']
        if subject in subject_sample_count:
            subject_sample_count[subject] += 1
        else:
            subject_sample_count[subject] = 1

    # convert to histogram
    ssc_hist = {}
    for s in subject_sample_count:
        ct = subject_sample_count[s]
        if ct in ssc_hist:
            ssc_hist[ct] += 1
        else:
            ssc_hist[ct] = 1
#        print(s + " has " + str(ct) + " sample(s)")

    # print histogram
    n_total_samples = 0
    n_total_subjects = 0
    print("n_samples\tn_subjects")
    for n_samples in sorted(ssc_hist):
        n_subjects = ssc_hist[n_samples]
        print(str(n_samples) + "\t" + str(n_subjects))
        n_total_subjects += n_subjects
        n_total_samples += (n_subjects * n_samples)
    print("n_total_samples=" + str(n_total_samples))
    print("n_total_subjects=" + str(n_total_subjects))

def add_properties(o1, o2):
    for p in o2:
        if p in o1:
            if o1[p] != o2[p]:
                logging.fatal("property add/merge failed: o1[p]=" + o1[p] + " o2[p]=" + o2[p])
                sys.exit(1)
        else:
            o1[p] = o2[p]    

def get_dna_extracts_json_from_restricted_metadata(study, pub_md, restricted_md):
    dna_extracts = []

    # Subject
    # e.g., ['dbGaP_Subject_ID', 'SUBJECT_ID', 'CONSENT', 'AFFECTION_STATUS']
    subject_md = restricted_md['Subject']
    # subjects indexed by dbGaP ID
    logging.debug("indexing restricted Subject")
    subjects = index_dicts(subject_md['data']['rows'], 'dbGaP_Subject_ID')

    # Sample
    # e.g., ['dbGaP_Subject_ID', 'dbGaP_Sample_ID', 'BioSample Accession', 'SUBJECT_ID', 'SAMPLE_ID', 'SAMPLE_USE']
    sample_md = restricted_md['Sample']
    # samples indexed by dbGaP ID
    logging.debug("indexing restricted Sample")
    samples = index_dicts(sample_md['data']['rows'], 'dbGaP_Sample_ID')

    # Sample_Attributes
    # e.g., ['dbGaP_Sample_ID', 'SAMPLE_ID', 'BODY_SITE', 'ANALYTE_TYPE', 'IS_TUMOR', 'SEQUENCING_CENTER', 'Funding_Source', 'TOPMed_Phase', 'TOPMed_Project', 'Study_Name']
    sample_att_md = restricted_md['Sample_Attributes']
    logging.debug("indexing restricted Sample_Attributes file")
    sample_atts = index_dicts(sample_att_md['data']['rows'], 'dbGaP_Sample_ID')
    
    # Subject_Phenotypes
    # e.g., ['dbGaP_Subject_ID', 'SUBJECT_ID', 'GENDER', 'RACE', 'VISIT_AGE', 'DNA_AGE', 'FORMER_SMOKER', 'CURRENT_SMOKER', 'CIGSPERDAY', 'CIGSPERDAY_AVERAGE', 'PACKYEARS', 'PREGNANCY', 'WEIGHT', 'HEIGHT', 'BMI']
    subject_phen_md = restricted_md['Subject_Phenotypes']
    logging.debug("indexing restricted Subject_Phenotype file")
    subject_phens = index_dicts(subject_phen_md['data']['rows'], 'dbGaP_Subject_ID')

    # link subjects and samples
    link_samples_to_subjects(samples, subjects)

    # merge sample attribute info
    for dbgap_samp_id in samples:
        sample = samples[dbgap_samp_id]
        sample_att = sample_atts[dbgap_samp_id]
        add_properties(sample, sample_att)

    # merge subject phenotype info
    for dbgap_subj_id in subjects:
        subject = subjects[dbgap_subj_id]
        subject_phen = subject_phens[dbgap_subj_id]
        add_properties(subject, subject_phen)

    # generate JSON for each sample
    for dbgap_samp_id in samples:
        sample = samples[dbgap_samp_id]
        subject = sample['subject']
        # filter out any attributes that don't belong in extraProperties
        sample_atts = {}
        for sa in sample:
            if sa != 'subject':
                sample_atts[sa] = sample[sa]

        subject_atts = {}
        for sa in subject:
            subject_atts[sa] = subject[sa]

        dna_extract = get_single_dna_extract_json(study, subject_atts, sample_atts)
        dna_extracts.append(dna_extract)

    return dna_extracts
