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

def print_subject_sample_count_histogram(samples):
    print("Histogram of number of subjects that have a given number of samples")

    # count samples per subject
    subject_sample_count = {}
    for s in samples:
        sample = samples[s]
        subject = sample['subject']['SUBJID']['mapped_value']
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


# ------------------------------------------------------
# DATS JSON Output
# ------------------------------------------------------

def get_single_sample_json(sample, dats_obj_cache):
#    print("converting sample to json: " + str(sample))
    samp_id = sample['SAMPID']['mapped_value']
    subj_id = sample['SUBJID']['mapped_value']
    subject = sample['subject']

    # Uberon id (or EFO id, contrary to the documentation)
    anat_id = sample['SMUBRID']['mapped_value']
    if anat_id is None:
        print("No Uberon/anatomy ID specified for sample " + samp_id)
        sys.exit(1)

    anatomy_identifier = None
    anatomy_alt_ids = None
    # TODO - query anatomy term from UBERON/EFO instead?
    anatomy_name = sample['SMTSD']['mapped_value']

    # EFO id
    if re.match(r'^EFO_\d+', anat_id):
        anatomy_identifier = OrderedDict([
                ("identifier",  anat_id),
                ("identifierSource",  "EFO")])
        anatomy_alt_ids = [OrderedDict([
                    ("identifier", "https://www.ebi.ac.uk/ols/ontologies/efo/terms?short_form=" + str(anat_id)),
                    ("identifierSource", "EFO")])]
    # Uberon id
    else:
        anatomy_identifier = OrderedDict([
                ("identifier",  "UBERON:" + str(anat_id)),
                ("identifierSource", "UBERON")])
        anatomy_alt_ids = [OrderedDict([
                    ("identifier", "http://purl.obolibrary.org/obo/UBERON_" + str(anat_id)),
                    ("identifierSource", "UBERON")])]

    # anatomical part
    anat_part_key = ":".join(["AnatomicalPart", anatomy_name])
    if anat_part_key in dats_obj_cache:
        anatomical_part = dats_obj_cache[anat_part_key]
    else:
        anatomical_part = DatsObj("AnatomicalPart", [
                ("name", anatomy_name),
                ("identifier", anatomy_identifier),
                ("alternateIdentifiers", anatomy_alt_ids)
                ])
        dats_obj_cache[anat_part_key] = anatomical_part

    # human experimental subject/patient
    subject_sex = DatsObj("Dimension", [
            ("name", DatsObj("Annotation", [("value", "Gender")])),
            ("description", "Gender of the subject"),
            ("identifier", DatsObj("Identifier", [("identifier", "SEX"), ("identifierSource", "GTEx")])),
            ("values", [ subject['SEX']['mapped_value'] ])
            ])

    subject_age = DatsObj("Dimension", [
            ("name", DatsObj("Annotation", [("value", "Age range")])),
            ("description", "Age range of the subject"),
            ("identifier", DatsObj("Identifier", [("identifier", "AGE"), ("identifierSource", "GTEx")])),
            ("values", [ subject['AGE']['mapped_value'] ])
            ])

    subject_hardy_scale = DatsObj("Dimension", [
            ("name", DatsObj("Annotation", [("value", "Hardy scale")])),
            ("description", "Hardy scale death classification for the subject"),
            ("identifier", DatsObj("Identifier", [("identifier", "DTHHRDY"), ("identifierSource", "GTEx")])),
            ("values", [ subject['DTHHRDY']['mapped_value'] ])
            ])

    subject_characteristics = [
        subject_sex,
        subject_age,
        subject_hardy_scale
        ]

    # human experimental subject/patient
    subj_key = ":".join(["Material", subj_id])
    if subj_key in dats_obj_cache:
        subject_material = dats_obj_cache[subj_key]
    else:
        subject_material = DatsObj("Material", [
                ("name", subj_id),
                ("identifier", { "identifier": subj_id }),
                ("description", "GTEx subject " + subj_id),
                ("characteristics", subject_characteristics),
                ("taxonomy", util.get_taxon_human()),
                ("roles", util.get_donor_roles())
                ])
        dats_obj_cache[subj_key] = subject_material

    specimen_annot = util.get_annotation("specimen")
    rna_extract_annot = util.get_annotation("RNA extract")

    # biological/tissue sample
    sample_name = samp_id
    biological_sample_material = DatsObj("Material", [
            ("name", sample_name),
            ("identifier", { "identifier": samp_id }),
            ("description", anatomy_name + " specimen collected from subject " + subj_id),
            ("taxonomy", util.get_taxon_human()),
            ("roles", [ specimen_annot ]),
            ("derivesFrom", [ subject_material, anatomical_part ])
            ])

    # RNA extracted from tissue sample
    rna_material = DatsObj("Material", [
            ("name", "RNA from " + sample_name),
            ("description", "total RNA extracted from " + anatomy_name + " specimen collected from subject " + subj_id),
            ("taxonomy", util.get_taxon_human()),
            ("roles", [ rna_extract_annot ]),
            ("derivesFrom", [ biological_sample_material ])
            ])

    return rna_material

def write_single_sample_json(sample, output_file, dats_obj_cache):
    rna_material = get_single_sample_json(sample, dats_obj_cache)
    with open(output_file, mode="w") as jf:
        jf.write(json.dumps(rna_material, indent=2))

def get_samples_json(samples, subjects):
    samples_json = []
    # track which DATS objects have already been added to the structure
    # maps ":".join([<type>, <name>]) to DatsObj
    dats_obj_cache = {}
    for s in sorted(samples):
        sample_json = get_single_sample_json(samples[s], dats_obj_cache)
        samples_json.append(sample_json)
    return samples_json

# write separate JSON file for each sample
def write_samples_json(subjects, samples, output_dir):
    # track which DATS objects have already been added to the structure
    # maps ":".join([<type>, <name>]<) to DatsObj
    dats_obj_cache = {}
    for s in sorted(samples):
        sample = samples[s]
        samp_id = sample['SAMPID']['mapped_value']
        output_file = os.path.join(output_dir, samp_id + ".json")
        write_single_sample_json(sample, output_file, dats_obj_cache)

def filter_samples(samples, smafrze):
    if smafrze is None:
        return samples
    filtered_samples = {}
    for s in samples:
        sample = samples[s]
        samp_smafrze = sample['SMAFRZE']['mapped_value']
        if samp_smafrze == smafrze:
            filtered_samples[s] = sample
    nfs = len(filtered_samples)
    logging.info("Found " + str(nfs) + "/" + str(len(samples)) + " sample(s) with SMAFRZE=" + smafrze)
    return filtered_samples
