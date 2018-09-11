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
        
        res[vname] = { "value": value, "var": var }

    return res

# Update a single DATS subject MAterial
def update_single_subject(study, study_md, subj, subj_var_values, use_all_dbgap_vars):

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
        elif name_upper == "HYPERTENSION" or name_upper == "MHHTN":
            if subj_var_values[name]['value'].lower() == "yes" or subj_var_values[name]['value'] == 1:
                disease['hypertension'] = "yes"
            else:
                disease['hypertension'] = "no"

    subject_characteristics = []
    subject_bearerOfDisease = []

    # harmonized/standardized characteristics
    if gender is not None:
        subject_sex = DatsObj("Dimension", [
                ("name", { "value": "Gender" }),
                ("description", "Gender of the subject"),
                ("values", [ gender ])
                ])
        subject_characteristics.append(subject_sex)

    if age is not None:
        subject_age = DatsObj("Dimension", [
                ("name", { "value": "Age" }),
                ("description", "Age of the subject"),
                ("values", [ age ])
                ])
        subject_characteristics.append(subject_age)
    
    if visit_year is not None:
        subject_visitYear = DatsObj("Dimension", [
                ("name", { "value": "Visit year" }),
                ("description", "Year of visit, to use for longitudinal analysis"),
                ("values", [ visit_year ])
                ])
        subject_characteristics.append(subject_visitYear)
    
    if sys_bp is not None:
        subject_sysBP = DatsObj("Dimension", [
                ("name", { "value": "Systolic blood pressure" }),
                ("description", "Systolic blood pressure of subject, measured in mmHg"),
                ("values", [ sys_bp ])
                ])
        subject_characteristics.append(subject_sysBP)
        
    if dias_bp is not None:
        subject_diasBP = DatsObj("Dimension", [
                ("name", { "value": "Diastolic blood pressure" }),
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
            ("diseaseStatus", OrderedDict([("value", disease['hypertension'] ), ("valueIRI", "")])), 
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

    # add "raw" characteristics / DATS Dimensions for _all_ dbGaP subject metadata
    # create DATS Dimensions for dbGaP subject metadata
    if use_all_dbgap_vars:
        subject_dimensions = [ make_var_dimension(vname, subj_var_values[vname]) for vname in sorted(subj_var_values) ]
        subject_characteristics.extend(subject_dimensions)
    
    # update subject
    dbgap_subj_id = subj_var_values['dbGaP_Subject_ID']['value']
    subj.set("alternateIdentifiers", [ util.get_alt_id(dbgap_subj_id, "dbGaP") ])
    subj.get("characteristics").extend(subject_characteristics)
    subj.set("bearerOfDisease", subject_bearerOfDisease)

# Generate DATS JSON for a single sample/DNA extract
def get_single_dna_extract_json(study, study_md, subj_var_values, samp_var_values):

    #Assign sample anatomy - tissue or blood   
    if "blood" in samp_var_values['SMMTRLTP']['value'].lower():
        anatomy_name = "blood"
        anat_id = "0000178"
    elif "tissue" in samp_var_values['SMMTRLTP']['value'].lower():
        anatomy_name = "tissue"
        anat_id = "0000479"
    elif "cells" in samp_var_values['SMMTRLTP']['value'].lower():
        anatomy_name = "cell group"
        anat_id = "0014778"  
    else:
        logging.fatal("encountered Sample type (SMMTRLTP) other than 'Blood', 'Tissue', 'Cells' in GTEx sample metadata - " + samp_var_values['SMMTRLTP']['value'])
        sys.exit(1)
        
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
        elif name_upper == "HYPERTENSION" or name_upper == "MHHTN":
            if subj_var_values[name]['value'].lower() == "yes" or subj_var_values[name]['value'] == 1:
                disease['hypertension'] = "yes"
            else:
                disease['hypertension'] = "no"

    # anatomical part
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
                ("name", { "value": "Gender" }),
                ("description", "Gender of the subject"),
                ("values", [ gender ])
                ])
        subject_characteristics.append(subject_sex)

    if age is not None:
        subject_age = DatsObj("Dimension", [
                ("name", { "value": "Age" }),
                ("description", "Age of the subject"),
                ("values", [ age ])
                ])
        subject_characteristics.append(subject_age)
    
    if visit_year is not None:
        subject_visitYear = DatsObj("Dimension", [
                ("name", { "value": "Visit year" }),
                ("description", "Year of visit, to use for longitudinal analysis"),
                ("values", [ visit_year ])
                ])
        subject_characteristics.append(subject_visitYear)
    
    if sys_bp is not None:
        subject_sysBP = DatsObj("Dimension", [
                ("name", { "value": "Systolic blood pressure" }),
                ("description", "Systolic blood pressure of subject, measured in mmHg"),
                ("values", [ sys_bp ])
                ])
        subject_characteristics.append(subject_sysBP)
        
    if dias_bp is not None:
        subject_diasBP = DatsObj("Dimension", [
                ("name", { "value": "Diastolic blood pressure" }),
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
            ("diseaseStatus", OrderedDict([("value", disease['hypertension'] ), ("valueIRI", "")])), 
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
    
    human_t = util.get_taxon_human()
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
            ("roles", util.get_donor_roles())
            ])

    # TODO - use DatsObjCache
    specimen_annot = util.get_annotation("specimen")
    dna_extract_annot = util.get_annotation("DNA extract")

    # biological/tissue sample
    sample_name = samp_id
    biological_sample_material = DatsObj("Material", [
            ("name", sample_name),
            ("identifier", { "identifier": samp_id }),
            ("alternateIdentifiers", [ util.get_alt_id(dbgap_samp_id, "dbGaP") ]),
            ("description", anatomy_name + " specimen collected from subject " + subj_id),
            ("characteristics", sample_characteristics),
            ("taxonomy", human_t),
            ("roles", [ specimen_annot ]),
            ("derivesFrom", [ subject_material, anatomical_part ])
            ])

    # DNA extracted from tissue sample
    dna_material = DatsObj("Material", [
            ("name", "DNA from " + sample_name),
            ("description", "DNA extracted from " + anatomy_name + " specimen collected from subject " + subj_id),
            ("taxonomy", human_t),
            ("roles", [ dna_extract_annot ]),
            ("derivesFrom", [ biological_sample_material ])
            ])

    return dna_material

# Generate synthetic data for a single sample based on the public variable summaries.
def get_synthetic_single_dna_extract_json_from_public_metadata(study, study_md):

    # Subject summary data
    if 'Subject_Phenotypes' in study_md:
        subj_data = study_md['Subject_Phenotypes']['var_report']['data']
        subj_vars = subj_data['vars']
        # pick representative and/or legal value for each variable
        subj_var_values = pick_var_values(subj_vars)
        logging.debug("subj_var_values=" + json.dumps(subj_var_values, indent=2))
    else:
        subj_var_values = {}

    # Sample summary data
    samp_data = study_md['Sample_Attributes']['var_report']['data']
    samp_vars = samp_data['vars']
    # pick representative and/or legal value for each variable
    samp_var_values = pick_var_values(samp_vars)
    logging.debug("samp_var_values=" + json.dumps(samp_var_values, indent=2))

    # assign dummy ids: subject and sample ids are protected data
    samp_var_values['dbGaP_Sample_ID'] = { "value": "0000000" }
    samp_var_values['SAMPLE_ID'] = { "value" : "SA0000000" }

    subj_var_values['dbGaP_Subject_ID'] = { "value" : "0000000" }
    subj_var_values['SUBJECT_ID'] = { "value" : "SU0000000" }

    return get_single_dna_extract_json(study, study_md, subj_var_values, samp_var_values)

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

def add_properties(o1, o2):
    for p in o2:
        if p in o1:
            if o1[p] != o2[p]:
                logging.fatal("property add/merge failed: o1[p]=" + o1[p] + " o2[p]=" + o2[p])
                sys.exit(1)
        else:
            o1[p] = o2[p]    

def update_subjects_from_restricted_metadata(cache, study, pub_md, restricted_md, subjects_d, use_all_dbgap_vars):

    # Subject
    # e.g., ['dbGaP_Subject_ID', 'SUBJECT_ID', 'CONSENT', 'AFFECTION_STATUS']
    subject_md = restricted_md['Subject']
    # subjects indexed by GTEx subject ID
    subjects = index_dicts(subject_md['data']['rows'], 'SUBJID')

    # Subject_Phenotypes
    # e.g., ['dbGaP_Subject_ID', 'SUBJECT_ID', 'GENDER', 'RACE', 'VISIT_AGE', 'DNA_AGE', 'FORMER_SMOKER', 'CURRENT_SMOKER', 'CIGSPERDAY', 'CIGSPERDAY_AVERAGE', 'PACKYEARS', 'PREGNANCY', 'WEIGHT', 'HEIGHT', 'BMI']
    subject_phen_md = restricted_md['Subject_Phenotypes']
    logging.debug("indexing restricted Subject_Phenotype file")
    subject_phens = index_dicts(subject_phen_md['data']['rows'], 'SUBJID')

    for subj_id in subjects:
        # merge subject phenotype info
        subject = subjects[subj_id]
        if subj_id in subject_phens:
            subject_phen = subject_phens[subj_id]
            add_properties(subject, subject_phen)
        else:
            logging.warn("no subject phenotype data found for " + subj_id)
        # update DATS subject Material
        subj = subjects_d[subj_id]
        subject_atts = {}
        for sa in subject:
            subject_atts[sa] = { "value" : subject[sa] }
        update_single_subject(study, pub_md, subj, subject_atts, use_all_dbgap_vars)

def update_dna_extracts_from_restricted_metadata(cache, study, pub_md, restricted_md, samples_d):
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
        # filter out any attributes that don't belong in characteristics
        sample_atts = {}
        for sa in sample:
            if sa != 'subject':
                sample_atts[sa] = { "value": sample[sa] } # TODO - add corresponding dbgap var identifier from pub md

        subject_atts = {}
        for sa in subject:
            subject_atts[sa] = { "value" : subject[sa] } # TODO - add corresponding dbgap var identifier from pub md

        dna_extract = get_single_dna_extract_json(study, pub_md, subject_atts, sample_atts)
        dna_extracts.append(dna_extract)

    return dna_extracts
