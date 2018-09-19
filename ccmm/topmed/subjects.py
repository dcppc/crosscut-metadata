#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
import ccmm.dats.util as util
import ccmm.topmed.dna_extracts as dna_extracts
from collections import OrderedDict
import csv
import json
import logging
import os
import re
import sys

# Produce a DATS Material for a single subject/donor.

#def get_subject_dats_material(cache, p_subject, gh_subject, var_lookup):

#    # retrieve id reference for the Identifier of the DATS Dimension for the "all subjects" consent group version of the variable
#    def get_var_id(name):
#        return var_lookup[name]['dim'].get("identifier").getIdRef()

def get_subject_dats_material(cache, study, study_md, subj_var_values):

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
            if subj_var_values[name]['value'].lower() == "yes" or subj_var_values[name]['value'] == 1:
                disease['hypertension'] = "yes"
            else:
                disease['hypertension'] = "no"

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
            dbgap_var_dim = var_value["var"]["dim"]
            dim.setProperty("identifier", dbgap_var_dim.get("identifier").getIdRef())
        return dim

    # create DATS Dimensions for dbGaP subject metadata
    subject_dimensions = [ make_var_dimension(vname, subj_var_values[vname]) for vname in sorted(subj_var_values) ]

    # "raw" characteristics from dbGaP metadata
    subject_characteristics.extend(subject_dimensions)
    
    human_t = util.get_taxon_human(cache)
    subj_id = subj_var_values['SUBJECT_ID']['value']
    dbgap_subj_id = subj_var_values['dbGaP_Subject_ID']['value']

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

    # add to the cache
    subj_key = ":".join(["Material", subj_id])
    dats_subj = cache.get_obj_or_ref(subj_key, lambda: subject_material)

    return dats_subj

def get_synthetic_subject_dats_material_from_public_metadata(cache, study, study_md):
    # Subject summary data
    subj_var_values = {}
    for var_type in ('Subject', 'Subject_Phenotypes'):
        if var_type not in study_md:
            continue
        subj_data = study_md[var_type]['var_report']['data']
        subj_vars = subj_data['vars']
        # pick representative and/or legal value for each variable
        dna_extracts.pick_var_values(subj_vars, subj_var_values)

    # assign dummy ids: subject ids are protected data
    subj_var_values['dbGaP_Subject_ID'] = { "value" : "0000000" }
    subj_var_values['SUBJECT_ID'] = { "value" : "SU0000000" }

    return get_subject_dats_material(cache, study, study_md, subj_var_values)

def add_properties(o1, o2, vars1, vars2):
    for p in o2:
        if p in o1:
            if o1[p] != o2[p]:
                logging.fatal("property add/merge failed: o1[p]=" + o1[p] + " o2[p]=" + o2[p])
                sys.exit(1)
        else:
            o1[p] = o2[p]
            vars1[p] = vars2[p]

def get_subjects_dats_materials_from_restricted_metadata(cache, study, pub_md, restricted_md):
    dats_subjects = {}
    
    def lookup_var_ids(d, typename, consent_group):
        var_ids = {}
        for k in d:
            cg_key = k + consent_group
            if cg_key in pub_md['type_name_cg_to_var'][typename]:
                var_ids[k] = pub_md['type_name_cg_to_var'][typename][cg_key]
            else:
                logging.warn("unable to find dbGaP id for " + cg_key)
        return var_ids

    # Subject
    # e.g., ['dbGaP_Subject_ID', 'SUBJECT_ID', 'CONSENT', 'AFFECTION_STATUS']
    subject_md = restricted_md['Subject']
    # subjects indexed by dbGaP ID
    logging.debug("indexing restricted Subject")
    subjects = dna_extracts.index_dicts(subject_md['data']['rows'], 'dbGaP_Subject_ID')
    # TODO - use either table_accession or comment line in file to get variable -> dbGaP variable id mapping
    # i.e., subject_md['data']['table_accession']
    # look up variable ids. assumes all subjects have same attributes.
    subjects_vars = lookup_var_ids(subject_md['data']['rows'][0], 'Subject', '')

    subject_phens = None
    subject_phens_vars = None

    # Subject_Phenotypes
    # e.g., ['dbGaP_Subject_ID', 'SUBJECT_ID', 'GENDER', 'RACE', 'VISIT_AGE', 'DNA_AGE', 'FORMER_SMOKER', 'CURRENT_SMOKER', 'CIGSPERDAY', 'CIGSPERDAY_AVERAGE', 'PACKYEARS', 'PREGNANCY', 'WEIGHT', 'HEIGHT', 'BMI']
    if 'Subject_Phenotypes' in restricted_md:
        subject_phen_md = restricted_md['Subject_Phenotypes']
        logging.debug("indexoxing restricted Subject_Phenotype file")
        subject_phens = dna_extracts.index_dicts(subject_phen_md['data']['rows'], 'dbGaP_Subject_ID')
        subject_phens_vars = lookup_var_ids(subject_phen_md['data']['rows'][0], 'Subject_Phenotypes', '')

    n_found = 0
    for dbgap_subj_id in subjects:
        subject = subjects[dbgap_subj_id]

        # variable mappings after merging the two sets of attributes
        combined_vars = subjects_vars.copy()

        if subject_phens is not None and dbgap_subj_id in subject_phens:
            n_found +=1
            subject_phen = subject_phens[dbgap_subj_id]
            add_properties(subject, subject_phen, combined_vars, subject_phens_vars)

        subject_atts = {}

        for sa in subject:
            subject_atts[sa] = { "value" : subject[sa] }
            if sa in combined_vars:
                subject_atts[sa]["var"] = combined_vars[sa]

        dats_subject = get_subject_dats_material(cache, study, pub_md, subject_atts)
        if dbgap_subj_id in dats_subjects:
            logging.fatal("duplicate dbGaP_subject_ID=" + dbgap_subj_id)
            sys.exit(1)
        dats_subjects[dbgap_subj_id] = dats_subject

    logging.info("found " + str(n_found) + "/" + str(len(subjects)) + " subjects in Subject_Phenotype file")
    return dats_subjects
