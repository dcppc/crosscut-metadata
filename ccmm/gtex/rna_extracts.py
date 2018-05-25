#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
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

# SubjectPhenotype metadata file
SUBJ_PHEN_COLS = [
    {'id': 'SUBJID', 'regex': r'^(GTEX|K)\-[\dA-Z]+$' },
    {'id': 'SEX', 'integer_cv': { 1: 'male', 2:'female' }, 'empty_ok': False },
    {'id': 'AGE', 'cv': ['20-29', '30-39', '40-49', '50-59', '60-69', '70-79'], 'empty_ok': False },
    # Hardy scale
    {'id': 'DTHHRDY', 'integer_cv': { 0: 'Ventilator case', 1: 'Violent and fast death', 2: 'Fast death of natural causes', 3: 'Intermediate', 4: 'Slow death' }, 'empty_ok': True }
    ]

# SampleAttributes metadata file
SA_TISSUE_TYPES = [
    'Adipose Tissue', 'Adrenal Gland', 'Bladder','Blood','Blood Vessel','Bone Marrow','Brain','Breast',
    'Cervix Uteri','Colon','Esophagus','Fallopian Tube','Heart','Kidney','Liver','Lung','Muscle','Nerve',
    'Ovary','Pancreas','Pituitary','Prostate','Skin','Spleen','Stomach','Testis','Thyroid','Uterus','Vagina' 
    ]

SA_DETAILED_TISSUE_TYPES = [
    'Adipose - Subcutaneous','Adipose - Visceral (Omentum)','Adrenal Gland','Artery - Aorta',
    'Artery - Coronary','Artery - Tibial','Bladder','Brain - Amygdala','Brain - Anterior cingulate cortex (BA24)',
    'Brain - Caudate (basal ganglia)','Brain - Cerebellar Hemisphere','Brain - Cerebellum','Brain - Cortex',
    'Brain - Frontal Cortex (BA9)','Brain - Hippocampus','Brain - Hypothalamus','Brain - Nucleus accumbens (basal ganglia)',
    'Brain - Putamen (basal ganglia)','Brain - Substantia nigra','Brain - Spinal cord (cervical c-1)','Brain - Substantia nigra',
    'Breast - Mammary Tissue','Cervix - Ectocervix','Cervix - Endocervix','Colon - Transverse','Esophagus - Mucosa',
    'Esophagus - Muscularis','Fallopian Tube','Heart - Atrial Appendage','Heart - Left Ventricle','Kidney - Cortex',
    'Kidney - Medulla','Liver','Lung','Muscle - Skeletal','Nerve - Tibial','Ovary','Pancreas','Pituitary','Prostate',
    'Skin - Not Sun Exposed (Suprapubic)','Skin - Sun Exposed (Lower leg)','Spleen','Stomach','Testis','Thyroid',
    'Transformed fibroblasts','Uterus','Vagina','Whole Blood'
    ]

SAMPLE_ATT_COLS = [
    {'id': 'SAMPID', 'empty_ok': False },
    {'id': 'SMATSSCR', 'integer_cv': { 0: 'None', 1: 'Mild', 2: 'Moderate', 3: 'Severe' } , 'empty_ok': True },
    {'id': 'SMCENTER',  'cv': [ 'B1', 'C1', 'D1', 'B1, A1', 'C1, A1', 'D1, A1' ] , 'empty_ok': True },
    {'id': 'SMPTHNTS', 'empty_ok': True },
    {'id': 'SMRIN', 'empty_ok': True },
    {'id': 'SMTS', 'cv': SA_TISSUE_TYPES , 'empty_ok': False },
    {'id': 'SMTSD', 'cv': SA_DETAILED_TISSUE_TYPES , 'empty_ok': False },
    # Uberon id e.g., 0002190 or EFO id e.g., EFO_0002009 (undocumented)
    {'id': 'SMUBRID', 'regex': r'^\d{7}|EFO_\d+$', 'empty_ok': False },
    {'id': 'SMTSISCH', 'empty_ok': True },
    {'id': 'SMTSPAX', 'empty_ok': True },
    {'id': 'SMNABTCH', 'empty_ok': False },
    {'id': 'SMNABTCHT', 'empty_ok': False },
    {'id': 'SMNABTCHD', 'empty_ok': False },
    {'id': 'SMGEBTCH', 'empty_ok': True },
    {'id': 'SMGEBTCHD', 'empty_ok': True },
    {'id': 'SMGEBTCHT', 'empty_ok': False },
    {'id': 'SMAFRZE', 'cv': ['RNASEQ','WGS','WES','OMNI','EXCLUDE'] , 'empty_ok': False },
    {'id': 'SMGTC', 'empty_ok': True },
    {'id': 'SME2MPRT', 'empty_ok': True },
    {'id': 'SMCHMPRS', 'empty_ok': True },
    {'id': 'SMNTRART', 'empty_ok': True },
    {'id': 'SMNUMGPS', 'empty_ok': True },
    {'id': 'SMMAPRT', 'empty_ok': True },
    {'id': 'SMEXNCRT', 'empty_ok': True },
    {'id': 'SM550NRM', 'empty_ok': True },
    {'id': 'SMGNSDTC', 'empty_ok': True },
    {'id': 'SMUNMPRT', 'empty_ok': True },
    {'id': 'SM350NRM', 'empty_ok': True },
    {'id': 'SMRDLGTH', 'empty_ok': True },
    {'id': 'SMMNCPB', 'empty_ok': True },
    {'id': 'SME1MMRT', 'empty_ok': True },
    {'id': 'SMSFLGTH', 'empty_ok': True },
    {'id': 'SMESTLBS', 'empty_ok': True },
    {'id': 'SMMPPD', 'empty_ok': True },
    {'id': 'SMNTERRT', 'empty_ok': True },
    {'id': 'SMRRNANM', 'empty_ok': True },
    {'id': 'SMRDTTL', 'empty_ok': True },
    {'id': 'SMVQCFL', 'empty_ok': True },
    {'id': 'SMMNCV', 'empty_ok': True },
    {'id': 'SMTRSCPT', 'empty_ok': True },
    {'id': 'SMMPPDPR', 'empty_ok': True },
    {'id': 'SMCGLGTH', 'empty_ok': True },
    {'id': 'SMGAPPCT', 'empty_ok': True },
    {'id': 'SMUNPDRD', 'empty_ok': True },
    {'id': 'SMNTRNRT', 'empty_ok': True },
    {'id': 'SMMPUNRT', 'empty_ok': True },
    {'id': 'SMEXPEFF', 'empty_ok': True },
    {'id': 'SMMPPDUN', 'empty_ok': True },
    {'id': 'SME2MMRT', 'empty_ok': True },
    {'id': 'SME2ANTI', 'empty_ok': True },
    {'id': 'SMALTALG', 'empty_ok': True },
    {'id': 'SME2SNSE', 'empty_ok': True },
    {'id': 'SMMFLGTH', 'empty_ok': True },
    {'id': 'SME1ANTI', 'empty_ok': True },
    {'id': 'SMSPLTRD', 'empty_ok': True },
    {'id': 'SMBSMMRT', 'empty_ok': True },
    {'id': 'SME1SNSE', 'empty_ok': True },
    {'id': 'SME1PCTS', 'empty_ok': True },
    {'id': 'SMRRNART', 'empty_ok': True },
    {'id': 'SME1MPRT', 'empty_ok': True },
    {'id': 'SMNUM5CD', 'empty_ok': True },
    {'id': 'SMDPMPRT', 'empty_ok': True }
]

DATS_TAXON_HUMAN =  [
    DatsObj("TaxonomicInformation", [
            ("name", "Homo sapiens"),
            ("identifier", OrderedDict([
                        ("identifier", "ncbitax:9606"),
                        ("identifierSource", "ncbitax")]))
            ])
    ]

DATS_DONOR_ROLES = [
    OrderedDict([
            ("value", "patient"),
            ("valueIRI",  "")]),
    OrderedDict([
            ("value", "donor"),
            ("valueIRI", "")])
    ]

# CVs for Gender, Age Range, and Hardy Scale.
# Not currently represented in the instance, but could be defined in the accompanying model:
#            ("values", ["male", "female"])
#            ("values", SUBJ_PHEN_COLS[2]['cv'])
#            ("values", [str(x) for x in SUBJ_PHEN_COLS[3]['integer_cv'].values()])

# ------------------------------------------------------
# Error handling
# ------------------------------------------------------

def fatal_error(err_msg):
    logging.fatal(err_msg)
    sys.exit(1)

def fatal_parse_error(err_msg, file, lnum):
    msg = err_msg + " at line " + str(lnum) + " of " + file
    fatal_error(msg)

# ------------------------------------------------------
# Metadata file parsing
# ------------------------------------------------------

# Generic parser for subject/phenotype and sample/attribute metadata files
def read_metadata_file(file_path, column_metadata, id_column):
    # rows indexed by the value in id_column
    rows = {}

    with open(file_path) as fh:
        reader = csv.reader(fh, delimiter='\t')
        lnum = 0
        for line in reader:
            lnum += 1

            # check column headings match expected values
            if lnum == 1:
                cnum = 0
                for col in column_metadata:
                    if line[cnum] != col['id']:
                        fatal_parse_error("Unexpected column header '" + line[cnum] + "' in column " + str(cnum+1) + " ", file_path, lnum)
                    cnum += 1

            # parse column values
            else:
                cnum = 0
                parsed_row = {}

                for col in column_metadata:
                    colname = col['id']
                    colval = line[cnum]
                    parsed_col = { "raw_value": colval }

                    # check regex if present
                    if 'regex' in col:
                        regex = col['regex']
                        m = re.match(regex, colval)
                        if m is None:
                            fatal_parse_error("Value in column '" + str(cnum+1) + "' ('" + colval+ "') does not match regex " + str(regex), file_path, lnum)

                    # check for empty value
                    if colval == '':
                        if col['empty_ok']:
                            parsed_col['mapped_value'] = None
                        else:
                            fatal_parse_error("Missing value in column " + str(cnum+1) + "/" + colname + " but empty_ok = False.", file_path, lnum)

                    # integer_cv
                    elif 'integer_cv' in col:
                        m = re.match(r'^(\d+)', colval)
                        if m is None:
                            fatal_parse_error("Value in column '" + str(cnum+1) + "' ('" + colval+ "') is not an integer.", file_path, lnum)
                            
                        iv = int(m.group(1))
                        icv = col['integer_cv']
                        if iv not in icv:
                            fatal_parse_error("No mapping defined for integer value " + str(iv) + " in column " + str(cnum+1) + "/" + colname + " ", file_path, lnum)
                        val = icv[iv]
                        parsed_col["mapped_value"] = val

                    # cv
                    elif 'cv' in col:
                        # check that value is one of the allowed values
                        cv = col['cv']

                    if 'mapped_value' not in parsed_col:
                        parsed_col['mapped_value'] = parsed_col['raw_value']

                    cnum += 1
                    parsed_row[colname] = parsed_col

                # set row id
                row_id = parsed_row[id_column]['mapped_value']
                parsed_row['id'] = row_id
                logging.debug("read row " + str(parsed_row) + " from line " + str(lnum) + " of " + file_path)
                if row_id in rows:
                    fatal_parse_error("Duplicate " + id_column + " '" + rowid + "'", subj_phen_file, lnum)
                rows[row_id] = parsed_row

    return rows

# Read tab-delimited GTEx subject phenotype file
def read_subject_phenotypes_file(subj_phen_file):
    subjects = read_metadata_file(subj_phen_file, SUBJ_PHEN_COLS, 'SUBJID')
    logging.info("Read " + str(len(subjects)) + " subject(s) from " + subj_phen_file)
    return subjects

# Read tab-delimited GTEx sample attribute file
def read_sample_attributes_file(samp_att_file):
    samples = read_metadata_file(samp_att_file, SAMPLE_ATT_COLS, 'SAMPID')
    logging.info("Read " + str(len(samples)) + " sample(s) from " + samp_att_file)
    return samples

# Parse subject id from each sample id and link sample with subject
def link_samples_to_subjects(samples, subjects):
    for s in samples:
        sample = samples[s]
        sampid = sample['SAMPID']['raw_value']
        # sample id begins with the subject id
        # all subject ids except one (K-562) begin with "GTEX-"
        m = re.search(r'^((GTEX|K)-[^\-]+)', sampid)
        if m is None:
            fatal_error("Unable to parse subject id from SAMPID '" + sampid + "'")
        subjid = m.group(1)
        sample['SUBJID'] = { "raw_value": sampid, "mapped_value": subjid }
        if subjid not in subjects:
            fatal_error("Found reference to nonexistent SUBJID '" + subjid + "' from SAMPID '" + + "'")
        sample['subject'] = subjects[subjid]

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

def get_single_sample_json(sample):
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
    anatomical_part = DatsObj("AnatomicalPart", [
            ("name", anatomy_name),
            ("identifier", anatomy_identifier),
            ("alternateIdentifiers", anatomy_alt_ids)
            ])

    # human experimental subject/patient
    subject_sex = DatsObj("Dimension", [
            ("name", { "value": "Gender" }),
            ("description", "Gender of the subject"),
            ("values", [ subject['SEX']['mapped_value'] ])
            ])

    subject_age = DatsObj("Dimension", [
            ("name", { "value": "Age range" }),
            ("description", "Age range of the subject"),
            ("values", [ subject['AGE']['mapped_value'] ])
            ])

    subject_hardy_scale = DatsObj("Dimension", [
            ("name", { "value": "Hardy scale" } ),
            ("description", "Hardy scale death classification for the subject"),
            ("values", [ subject['DTHHRDY']['mapped_value'] ])
            ])

    subject_characteristics = [
        subject_sex,
        subject_age,
        subject_hardy_scale
        ]

    # human experimental subject/patient
    subject_material = DatsObj("Material", [
            ("name", subj_id),
            ("identifier", { "identifier": subj_id }),
            ("description", "GTEx subject " + subj_id),
            ("characteristics", subject_characteristics),
            ("taxonomy", DATS_TAXON_HUMAN),
            ("roles", DATS_DONOR_ROLES)
            ])

    # biological/tissue sample
    sample_name = samp_id
    biological_sample_material = DatsObj("Material", [
            ("name", sample_name),
            ("identifier", { "identifier": samp_id }),
            ("description", anatomy_name + " specimen collected from subject " + subj_id),
            ("taxonomy", DATS_TAXON_HUMAN),
            ("roles", [ OrderedDict([("value", "specimen"), ("valueIRI", "")]) ]),
            ("derivesFrom", [ subject_material, anatomical_part ])
            ])

    # RNA extracted from tissue sample
    rna_material = DatsObj("Material", [
            ("name", "RNA from " + sample_name),
#            ("identifier", {"identifier": tmpid()}),
            ("description", "total RNA extracted from " + anatomy_name + " specimen collected from subject " + subj_id),
            ("taxonomy", DATS_TAXON_HUMAN),
            ("roles", [ OrderedDict([("value", "RNA extract"), ("valueIRI", "")])]),
            ("derivesFrom", [ biological_sample_material ])
            ])

    return rna_material

def write_single_sample_json(sample, output_file):
    rna_material = get_single_sample_json(sample)
    with open(output_file, mode="w") as jf:
        jf.write(json.dumps(rna_material, indent=2))

def get_samples_json(samples, subjects):
    samples_json = []
    for s in sorted(samples):
        sample_json = get_single_sample_json(samples[s])
        samples_json.append(sample_json)
    return samples_json

def write_samples_json(subjects, samples, output_dir):
    # write separate JSON file for each sample
    for s in sorted(samples):
        sample = samples[s]
        samp_id = sample['SAMPID']['mapped_value']
        output_file = os.path.join(output_dir, samp_id + ".json")
        write_single_sample_json(sample, output_file)

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
