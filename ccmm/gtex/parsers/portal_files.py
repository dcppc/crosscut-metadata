#!/usr/bin/env python3

# Parsers for the public metadata files available from the GTEx Portal.

from ccmm.dats.datsobj import DatsObj
import ccmm.gtex.parsers.util as util
import csv
import logging
import re

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

# CVs for Gender, Age Range, and Hardy Scale.
# Not currently represented in the instance, but could be defined in the accompanying model:
#            ("values", ["male", "female"])
#            ("values", SUBJ_PHEN_COLS[2]['cv'])
#            ("values", [str(x) for x in SUBJ_PHEN_COLS[3]['integer_cv'].values()])

# ------------------------------------------------------
# Metadata file parsing
# ------------------------------------------------------

# Read tab-delimited GTEx subject phenotype file
def read_subject_phenotypes_file(subj_phen_file):
    subjects = util.read_csv_metadata_file(subj_phen_file, SUBJ_PHEN_COLS, 'SUBJID')
    logging.info("Read " + str(len(subjects)) + " subject(s) from " + subj_phen_file)
    return subjects

# Read tab-delimited GTEx sample attribute file
def read_sample_attributes_file(samp_att_file):
    samples = util.read_csv_metadata_file(samp_att_file, SAMPLE_ATT_COLS, 'SAMPID')
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
            util.fatal_error("Unable to parse subject id from SAMPID '" + sampid + "'")
        subjid = m.group(1)
        sample['SUBJID'] = { "raw_value": sampid, "mapped_value": subjid }
        if subjid not in subjects:
            util.fatal_error("Found reference to nonexistent SUBJID '" + subjid + "' from SAMPID '" + + "'")
        sample['subject'] = subjects[subjid]
