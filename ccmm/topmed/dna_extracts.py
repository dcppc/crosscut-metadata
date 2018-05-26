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
#        print("var=" + str(var))
        
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

# Generate DATS JSON for access-restricted TOPMed data
def get_single_sample_json():
    pass

# Generate synthetic data for a single sample based on the public variable summaries.
def get_synthetic_single_sample_json_from_public_metadata(study, study_md):

    # assign dummy ids: subject and sample ids are protected data
    dbgap_subj_id = "0000000"
    dbgap_samp_id = "0000000"
    subj_id = "SU0000000"
    samp_id = "SA0000000"

    # blood
    anatomy_name = "blood"
    anat_id = "0000178"

    anatomy_identifier = OrderedDict([
            ("identifier",  "UBERON:" + str(anat_id)),
            ("identifierSource", "UBERON")])
    anatomy_alt_ids = [OrderedDict([
                ("identifier", "http://purl.obolibrary.org/obo/UBERON_" + str(anat_id)),
                ("identifierSource", "UBERON")])]

    # Subject summary data
    subj_data = study_md['Subject_Phenotypes']['var_report']['data']
#    print("got subj_data=" + str(subj_data))
    subj_vars = subj_data['vars']
    # pick representative and/or legal value for each variable
    subj_var_values = pick_var_values(subj_vars)
    print("subj_var_values=" + json.dumps(subj_var_values, indent=2))

    # Sample summary data
    samp_data = study_md['Sample_Attributes']['var_report']['data']
#    print("got samp_data=" + str(samp_data))
    samp_vars = samp_data['vars']
    # pick representative and/or legal value for each variable
    samp_var_values = pick_var_values(samp_vars)
    print("samp_var_values=" + json.dumps(samp_var_values, indent=2))


    # anatomical part
    anatomical_part = DatsObj("AnatomicalPart", [
            ("name", anatomy_name),
            ("identifier", anatomy_identifier),
            ("alternateIdentifiers", anatomy_alt_ids)
            ])

    subject_sex = DatsObj("Dimension", [
            ("name", { "value": "Gender" }),
            ("description", "Gender of the subject"),
            ("values", [  ])
            ])

    subject_age = DatsObj("Dimension", [
            ("name", { "value": "Age" }),
            ("description", "Age of the subject"),
            ("values", [  ])
            ])
    
    subject_characteristics = [
        subject_sex,
        subject_age
        ]

    human_t = util.get_taxon_human()
    study_title = study.get("title")

    # human experimental subject/patient
    subject_material = DatsObj("Material", [
            ("name", subj_id),
            ("identifier", { "identifier": subj_id }),
            ("alternateIdentifiers", [ util.get_alt_id(dbgap_subj_id, "dbGaP") ]),
            ("description", study_title + " subject " + subj_id),
            ("characteristics", subject_characteristics),
            ("taxonomy", human_t),
            ("roles", util.get_donor_roles())
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
            ("derivesFrom", [ subject_material, anatomical_part ])
            ])

    # DNA extracted from tissue sample
    dna_material = DatsObj("Material", [
            ("name", "DNA from " + sample_name),
#            ("identifier", {"identifier": tmpid()}),
            ("description", "DNA extracted from " + anatomy_name + " specimen collected from subject " + subj_id),
            ("taxonomy", human_t),
            ("roles", [ OrderedDict([("value", "DNA extract"), ("valueIRI", "")])]),
            ("derivesFrom", [ biological_sample_material ])
            ])

    return dna_material
