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

# Pick representative and/or legal value for each variable in vars and place it in vdict
def pick_var_values(vars, vdict):
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
        elif (var['reported_type'] == 'encoded value') or (var['calculated_type'] == 'enum_integer'):
            values = var['total']['stats']['values']
        # take the median if defined
        elif (var['reported_type'] == 'integer') or (var['calculated_type'] == 'integer'):
            value = var['total']['stats']['median']
        elif (var['reported_type'] == 'decimal') or (var['calculated_type'] == 'decimal'):
            value = var['total']['stats']['median']
        else:
            logging.fatal("unexpected variable reported_type=" + var['reported_type'])
            sys.exit(1)

        if values is not None:
            # sort values by count and then alphanumerically
            sorted_values = sorted(values, key=lambda x: int(x['count']), reverse=True)
            sorted_values.sort(key=lambda x: x['name'])
            value = sorted_values[0]['name']
        
        if vname in vdict:
            logging.warn("previous value (" + vdict[vname]["value"] + ") for variable " + vname + " overwritten with " + value)

        vdict[vname] = { "value": value, "var": var }

    return vdict

# Generate DATS JSON for a single sample/DNA extract
def get_single_dna_extract_json(cache, study, study_md, subj_var_values, samp_var_values):
    # Almost all samples in TOPMed WGS phase are blood samples, named "Blood", "Peripheral Blood"...
    # Few samples are saliva samples probably due to sample collection issues
    name = None
    if 'BODY_SITE' in samp_var_values:
        name = 'BODY_SITE'
    elif 'Body_Site' in samp_var_values:
        name = 'Body_Site'
    elif 'Body Site' in samp_var_values:
        name = 'Body Site'

    anat_id = None
    anatomy_name = None
        
    if name is not None:
        if "blood" in samp_var_values[name]['value'].lower():
            anatomy_name = "blood"
            anat_id = "0000178"
        elif samp_var_values[name]['value'].lower() == "saliva":
            anatomy_name = "saliva"
            anat_id = "0001836"        
        else:
            logging.fatal("encountered BODY_SITE other than 'Blood' and 'Saliva' in TOPMed sample metadata - " + samp_var_values['BODY_SITE']['value'])
            sys.exit(1)

    if anat_id is not None:
        anatomy_identifier = OrderedDict([
            ("identifier",  "UBERON:" + str(anat_id)),
            ("identifierSource", "UBERON")])
        anatomy_alt_ids = [OrderedDict([
            ("identifier", "http://purl.obolibrary.org/obo/UBERON_" + str(anat_id)),
            ("identifierSource", "UBERON")])]

    # extract subject attributes
    gender = None
    age = None
    visit_year = None
    sys_bp = None
    dias_bp = None
    disease = {}
    disease['hypertension'] = "unknown"
    
    for name in subj_var_values:
        name_upper = name.upper()
        if name_upper == "GENDER" or name_upper == "SEX":
            gender = subj_var_values[name]['value'].lower()
        elif name_upper == "VISIT_AGE" or name_upper == "AGE" or name_upper == "AGE_ENROLL": #need to confirm that these  allmean the same thing
            age = subj_var_values[name]['value']
        elif name_upper == "VISIT_YEAR":
            visit_year =  subj_var_values[name]['value']
        elif name_upper == "SYSBP":
            sys_bp = subj_var_values[name]['value']
        elif name_upper == "DIASBP":
            dias_bp = subj_var_values[name]['value']
        elif name_upper == "HYPERTENSION" or name_upper == "HIGHBLOODPRES":
            if subj_var_values[name]['value'].lower() == "yes" or subj_var_values[name]['value'] == '1':
                disease['hypertension'] = "yes"
            elif re.match(r'\S', subj_var_values[name]['value']):
                disease['hypertension'] = "no"

    # anatomical part
    anatomical_part = None
    if anatomy_name is not None:
        anatomical_part = DatsObj("AnatomicalPart", [
            ("name", anatomy_name),
            ("identifier", anatomy_identifier),
            ("alternateIdentifiers", anatomy_alt_ids)
        ])

    subject_characteristics = []
    subject_bearerOfDisease = []

    # harmonized/standardized characteristics
    if gender is not None:
        subject_sex = DatsObj("Dimension", [
                ("name", DatsObj("Annotation", [("value", "Gender")])),
                ("description", "Gender of the subject"),
                ("values", [ gender ])
                ])
        subject_characteristics.append(subject_sex)

    if age is not None:
        subject_age = DatsObj("Dimension", [
                ("name", DatsObj("Annotation", [("value", "Age")])),
                ("description", "Age of the subject"),
                ("values", [ age ])
                ])
        subject_characteristics.append(subject_age)
    
    if visit_year is not None:
        subject_visitYear = DatsObj("Dimension", [
                ("name", DatsObj("Annotation", [("value", "Visit year")])),
                ("description", "Year of visit, to use for longitudinal analysis"),
                ("values", [ visit_year ])
                ])
        subject_characteristics.append(subject_visitYear)
    
    if sys_bp is not None:
        subject_sysBP = DatsObj("Dimension", [
                ("name", DatsObj("Annotation", [("value", "Systolic blood pressure")])),
                ("description", "Systolic blood pressure of subject, measured in mmHg"),
                ("values", [ sys_bp ])
                ])
        subject_characteristics.append(subject_sysBP)
        
    if dias_bp is not None:
        subject_diasBP = DatsObj("Dimension", [
                ("name", DatsObj("Annotation", [("value", "Diastolic blood pressure")])),
                ("description", "Diastolic blood pressure of subject, measured in mmHg"),
                ("values", [ dias_bp ])
                ])
        subject_characteristics.append(subject_diasBP)                                      
    
    if disease['hypertension'] != "unknown":
        disease_name = "hypertension"
        disease_id = "10763"
        disease_identifier = OrderedDict([
            ("identifier",  "DOID:" + str(disease_id)),
            ("identifierSource", "Disease Ontology")])
        disease_alt_ids = [OrderedDict([
            ("identifier", "http://purl.obolibrary.org/obo/DOID_" + str(disease_id)),
            ("identifierSource", "Disease Ontology")])]
        subject_hypertension = DatsObj("Disease", [
            ("name", "Hypertension"),
            ("identifier", disease_identifier),
            ("alternateIdentifiers", disease_alt_ids),
            ("diseaseStatus", DatsObj("Annotation", [("value", disease['hypertension'] ), ("valueIRI", "")])), 
            ])
        subject_bearerOfDisease.append(subject_hypertension)

    # create a DATS Dimension from a dbGaP variable value
    def make_var_dimension(name, var_value):
        value = var_value["value"]

        dim = DatsObj("Dimension", 
                      [("name", DatsObj("Annotation", [( "value",  name )])), 
                       ("values", [ value ])
                       ])

        # find existing DATS identifier for the corresponding Dataset Dimension 
        if "var" in var_value:
            id = var_value["var"]["id"]
            dbgap_var_dim = study_md['dbgap_vars'][id]
            dim.setProperty("identifier", dbgap_var_dim.get("identifier").getIdRef())

        return dim

    # create DATS Dimensions for dbGaP subject metadata
    subject_dimensions = [ make_var_dimension(vname, subj_var_values[vname]) for vname in sorted(subj_var_values) ]

    # create DATS Dimensions for dbGaP sample metadata
    sample_dimensions = [ make_var_dimension(vname, samp_var_values[vname]) for vname in sorted(samp_var_values) ]

    # "raw" characteristics from dbGaP metadata
    subject_characteristics.extend(subject_dimensions)
    sample_characteristics = sample_dimensions
    
    human_t = util.get_taxon_human(cache)
    subj_id = subj_var_values['SUBJECT_ID']['value']
    dbgap_subj_id = subj_var_values['dbGaP_Subject_ID']['value']
    samp_id = samp_var_values['SAMPLE_ID']['value']
    dbgap_samp_id = samp_var_values['dbGaP_Sample_ID']['value']

    study_title = study.get("title")

    # human experimental subject/patient
    subject_material = DatsObj("Material", [
            ("name", subj_id),
            ("identifier", { "identifier": subj_id }),
            ("alternateIdentifiers", [ util.get_alt_id(dbgap_subj_id, "dbGaP") ]),
            ("description", study_title + " subject " + subj_id),
            ("characteristics", subject_characteristics),
            ("bearerOfDisease", subject_bearerOfDisease),
            ("taxonomy", [ human_t ]),
            ("roles", util.get_donor_roles(cache))
            ])

    # TODO - use DatsObjCache
    specimen_annot = util.get_annotation("specimen")
    dna_extract_annot = util.get_annotation("DNA extract")

    # biological/tissue sample
    sample_name = samp_id
    sample_derives_from = [ subject_material ]
    sample_descr = "specimen collected from subject " + subj_id
    if anatomical_part is not None:
        sample_derives_from.append(anatomical_part)
        sample_descr = anatomy_name + " " + sample_descr

    biological_sample_material = DatsObj("Material", [
            ("name", sample_name),
            ("identifier", { "identifier": samp_id }),
            ("alternateIdentifiers", [ util.get_alt_id(dbgap_samp_id, "dbGaP") ]),
            ("description", sample_descr),
            ("characteristics", sample_characteristics),
            ("taxonomy", [ human_t ]),
            ("roles", [ specimen_annot ]),
            ("derivesFrom", sample_derives_from )
            ])

    # DNA extracted from tissue sample
    dna_descr = "DNA extracted from specimen collected from subject " + subj_id
    if anatomical_part is not None:
        dna_descr = "DNA extracted from " + anatomy_name + " specimen collected from subject " + subj_id

    dna_material = DatsObj("Material", [
            ("name", "DNA from " + sample_name),
            ("description", dna_descr),
            ("taxonomy", [ human_t ]),
            ("roles", [ dna_extract_annot ]),
            ("derivesFrom", [ biological_sample_material ])
            ])

    return dna_material

# Generate synthetic data for a single sample based on the public variable summaries.
def get_synthetic_single_dna_extract_json_from_public_metadata(cache, study, study_md):

    # Subject summary data
    subj_var_values = {}
    for var_type in ('Subject', 'Subject_Phenotypes'):
        if var_type not in study_md:
            continue
        subj_data = study_md[var_type]['var_report']['data']
        subj_vars = subj_data['vars']
        # pick representative and/or legal value for each variable
        pick_var_values(subj_vars, subj_var_values)

    # Sample summary data
    samp_var_values = {}
    for var_type in ('Sample', 'Sample_Attributes'):
        if var_type not in study_md:
            continue
        samp_data = study_md[var_type]['var_report']['data']
        samp_vars = samp_data['vars']
        # pick representative and/or legal value for each variable
        samp_var_values = pick_var_values(samp_vars, samp_var_values)

    # assign dummy ids: subject and sample ids are protected data
    samp_var_values['dbGaP_Sample_ID'] = { "value": "0000000" }
    samp_var_values['SAMPLE_ID'] = { "value" : "SA0000000" }

    subj_var_values['dbGaP_Subject_ID'] = { "value" : "0000000" }
    subj_var_values['SUBJECT_ID'] = { "value" : "SU0000000" }

    return get_single_dna_extract_json(cache, study, study_md, subj_var_values, samp_var_values)

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

def get_dna_extracts_json_from_restricted_metadata(cache, study, pub_md, restricted_md):
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
    if 'Sample_Attributes' in restricted_md:
        sample_att_md = restricted_md['Sample_Attributes']
        logging.debug("indexing restricted Sample_Attributes file")
        sample_atts = index_dicts(sample_att_md['data']['rows'], 'dbGaP_Sample_ID')
    else:
        sample_atts = {}
    
    # Subject_Phenotypes
    # e.g., ['dbGaP_Subject_ID', 'SUBJECT_ID', 'GENDER', 'RACE', 'VISIT_AGE', 'DNA_AGE', 'FORMER_SMOKER', 'CURRENT_SMOKER', 'CIGSPERDAY', 'CIGSPERDAY_AVERAGE', 'PACKYEARS', 'PREGNANCY', 'WEIGHT', 'HEIGHT', 'BMI']
    if 'Subject_Phenotypes' in restricted_md:
        subject_phen_md = restricted_md['Subject_Phenotypes']
        logging.debug("indexing restricted Subject_Phenotype file")
        subject_phens = index_dicts(subject_phen_md['data']['rows'], 'dbGaP_Subject_ID')
    else:
        subject_phens = {}

    # link subjects and samples
    link_samples_to_subjects(samples, subjects)

    # merge sample attribute info
    for dbgap_samp_id in samples:
        sample = samples[dbgap_samp_id]
        if dbgap_samp_id in sample_atts:
            sample_att = sample_atts[dbgap_samp_id]
            add_properties(sample, sample_att)

    # merge subject phenotype info
    if 'Subject_Phenotypes' in restricted_md:
        for dbgap_subj_id in subjects:
            subject = subjects[dbgap_subj_id]
            subject_phen = subject_phens[dbgap_subj_id]
            add_properties(subject, subject_phen)

    # generate JSON for each sample
    for dbgap_samp_id in samples:
        sample = samples[dbgap_samp_id]
        subject = sample['subject']
        # filter out any attributes that don't belong in characteristics
        sample_atts = {}
        for sa in sample:
            if sa != 'subject':
                sample_atts[sa] = { "value": sample[sa] } # TODO - add corresponding dbgap var identifier from pub md

        subject_atts = {}
        for sa in subject:
            subject_atts[sa] = { "value" : subject[sa] } # TODO - add corresponding dbgap var identifier from pub md

        dna_extract = get_single_dna_extract_json(cache, study, pub_md, subject_atts, sample_atts)
        dna_extracts.append(dna_extract)

    return dna_extracts
