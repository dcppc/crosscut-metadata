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

# Generate DATS JSON for a single sample
def get_single_sample_json(study, subj_var_values, samp_var_values):

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
    dbgap_subj_id = subj_var_values['DBGAP_SUBJECT_ID']
    samp_id = samp_var_values['SAMPLE_ID']
    dbgap_samp_id = samp_var_values['DBGAP_SAMPLE_ID']

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
def get_synthetic_single_sample_json_from_public_metadata(study, study_md):

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
    samp_var_values['DBGAP_SAMPLE_ID'] = "0000000"
    samp_var_values['SAMPLE_ID'] = "SA0000000"

    subj_var_values['DBGAP_SUBJECT_ID'] = "0000000"
    subj_var_values['SUBJECT_ID'] = "SU0000000"

    return get_single_sample_json(study, subj_var_values, samp_var_values)
