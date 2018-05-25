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

# Generate DATS JSON for access-restricted TOPMed data
def get_single_sample_json():
    pass

# Generate synthetic data for a single sample based on the public variable summaries.
def get_synthetic_single_sample_json_from_public_metadata(study_md):

    # generate subject and sample id - these are protected data
    subj_id = "dummy_subj_id" # TODO
    samp_id = "dummy_samp_id" # TODO

    # blood
    anatomy_name = "blood"
    anat_id = "0000178"

    anatomy_identifier = OrderedDict([
            ("identifier",  "UBERON:" + str(anat_id)),
            ("identifierSource", "UBERON")])
    anatomy_alt_ids = [OrderedDict([
                ("identifier", "http://purl.obolibrary.org/obo/UBERON_" + str(anat_id)),
                ("identifierSource", "UBERON")])]

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

    # human experimental subject/patient
    subject_material = DatsObj("Material", [
            ("name", subj_id),
            ("identifier", { "identifier": subj_id }),
            # TODO - use study-specific description?
            ("description", "TOPMed subject " + subj_id),
            ("characteristics", subject_characteristics),
            ("taxonomy", human_t),
            ("roles", util.get_donor_roles())
            ])

    # biological/tissue sample
    sample_name = samp_id
    biological_sample_material = DatsObj("Material", [
            ("name", sample_name),
            ("identifier", { "identifier": samp_id }),
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
