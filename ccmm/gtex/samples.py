#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
import ccmm.dats.util as util
from collections import OrderedDict
import logging
import re
import sys

# Produce a DATS Material for a single sample.

def get_sample_dats_material(cache, dats_subject, p_sample, gh_sample):
    samp_id = p_sample['SAMPID']['mapped_value']
    subj_id = p_sample['SUBJID']['mapped_value']

    # Uberon id (or EFO id, contrary to the documentation)
    anat_id = p_sample['SMUBRID']['mapped_value']
    if anat_id is None:
        print("No Uberon/anatomy ID specified for sample " + samp_id)
        sys.exit(1)

    anatomy_identifier = None
    anatomy_alt_ids = None
    # TODO - query anatomy term from UBERON/EFO instead?
    anatomy_name = p_sample['SMTSD']['mapped_value']

    def make_anat_part(anat_id, anatomy_name):
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

        return anatomical_part

    # use cached value for AnatomicalPart if possible
    anat_part_key = ":".join(["AnatomicalPart", anatomy_name])
    anatomical_part = cache.get_obj_or_ref(anat_part_key, lambda: make_anat_part(anat_id, anatomy_name))

    # use URI from GitHub GTEx id dump if available
    identifier = samp_id
    if gh_sample is not None:
        identifier_id = gh_sample['Destination URL']['raw_value']
        
    # biological/tissue sample
    biological_sample_material = DatsObj("Material", [
            ("name", samp_id),
            ("identifier", { "identifier": identifier }),
            ("description", anatomy_name + " specimen collected from subject " + subj_id),
            # TODO - use id refs for these too:
            ("taxonomy", util.get_taxon_human()),
            ("roles", [ util.get_annotation("specimen") ]),
            ("derivesFrom", [ dats_subject.getIdRef(), anatomical_part ])
            ])

    # sample type
    smafrze = p_sample['SMAFRZE']['mapped_value']
    stype = None
    if smafrze == "RNASEQ":
        stype = "RNA"
    elif smafrze == "WGS":
        stype = "DNA"
    elif smafrze == "WES":
        stype = "DNA"
    elif smafrze == "EXCLUDE":
        # TODO - other options here?
        return None
    # Illumina OMNI SNP Array
    elif smafrze == "OMNI":
        stype = "DNA"
    else:
        print("unknown stype")
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print("p_sample=")
        pp.pprint(p_sample)
        print("g_sample=")
        pp.pprint(gh_sample)
        sys.exit(1)

    # DNA or RNA extract
    dna_or_rna_material = DatsObj("Material", [
            ("name", stype + " from " + samp_id),
            ("description", "total " + stype + " extracted from " + anatomy_name + " specimen collected from subject " + subj_id),
            # TODO - use id ref for this:
            ("taxonomy", util.get_taxon_human()),
            ("roles", [ util.get_annotation(stype + " extract") ]),
            ("derivesFrom", [ biological_sample_material ])
            ])

    return dna_or_rna_material

# Produce a dict of DATS subject/donor Materials, indexed by GTEx sample id.

def get_samples_dats_materials(cache, dats_subjects, p_samples, gh_samples):
    dats_samples = {}

    for s in p_samples:
        # sample attribute info from GTEx Portal file
        p_sample = p_samples[s]
        # sample info from GTEx GitHub id dump (may be None)
        gh_sample = None
        if gh_sample in gh_samples:
            gh_sample = gh_samples[s]
        samp_id = p_sample['SAMPID']['mapped_value']
        subj_id = p_sample['SUBJID']['mapped_value']
        dats_subject = dats_subjects[subj_id]
        samp_material = get_sample_dats_material(cache, dats_subject, p_sample, gh_sample)
        if samp_material is None:
            continue
        dats_samples[samp_id] = samp_material
    
    return dats_samples

# create Datasets for file-level links based on GitHub manifest files
def get_files_dats_datasets(cache, dats_samples_d, p_samples, gh_samples, protected_cram_files):
    file_datasets = []

    # ideally these should be pointers to entities defined in the parent dataset:
    rnaseq_types = [] # TODO
    wgs_types = [] # TODO
    creators = [] # TODO

    def make_data_standard(format):
        return DatsObj("DataStandard", [
            ("name", format),
            ("type", DatsObj("Annotation", [("value", "format")])),
            ("description", format + " file format")
            ])
    
    cram_ds_key = ":".join(["DataStandard", "CRAM"])
    cram_ds = cache.get_obj_or_ref(cram_ds_key, lambda: make_data_standard("CRAM"))

    crai_ds_key = ":".join(["DataStandard", "CRAI"])
    crai_ds = cache.get_obj_or_ref(crai_ds_key, lambda: make_data_standard("CRAI"))

    for sample_id in protected_cram_files:
        file = protected_cram_files[sample_id]
        material_type = None
        ds_types = None
        
        # determine file type
        if re.search(r'wgs\/', file['cram_file_aws']['raw_value']):
            material_type = 'DNA'
            ds_types = wgs_types
        elif re.search(r'rnaseq\/', file['cram_file_aws']['raw_value']):
            material_type = 'RNA'
            ds_types = rnaseq_types
        else:
            logging.fatal("unable to determine material/sequence type from cram_file_aws=" + file['cram_file_aws']['raw_value'])
            sys.exit(1)

        # TODO - where to put .crai URIs?
        # TODO - where to put md5 checksum and firecloud_id?
        
        # RNA-Seq keys = sample_id	cram_file	cram_file_md5	cram_file_size	cram_index	cram_file_aws	cram_index_aws
        # WGS keys = same as above + firecloud_id
        cram_file = file['cram_file']['raw_value']
        cram_file_md5 = file['cram_file_md5']['raw_value']

        # Google Cloud Platform / Google Storage copy
        gs_access = DatsObj("Access", [
                ("landingPage", file['cram_file']['raw_value'])
                ])
        gs_distro = DatsObj("DatasetDistribution", [
                ("access", gs_access),
                ("identifier", DatsObj("Identifier", [("identifier", file['cram_file']['raw_value'])])),
                ("size", file['cram_file_size']['raw_value']),
                ("conformsTo", [cache.get_obj_or_ref(cram_ds_key, lambda: make_data_standard("CRAM"))])
                ])

        # AWS / S3 copy
        s3_access = DatsObj("Access", [
                ("landingPage", file['cram_file_aws']['raw_value'])
                ])
        s3_distro = DatsObj("DatasetDistribution", [
                ("access", s3_access),
                ("identifier", DatsObj("Identifier", [("identifier", file['cram_file_aws']['raw_value'])])),
                ("size", file['cram_file_size']['raw_value']),
                ("conformsTo", [cache.get_obj_or_ref(cram_ds_key, lambda: make_data_standard("CRAM"))])
                ])

        m = re.match(r'^.*\/([^\/]+)$', cram_file)
        if m is None:
            logging.fatal("unable to parse filename from CRAM file URI " + cram_file)
            sys.exit(1)
        filename = m.group(1)
        
        ds = DatsObj("Dataset", [
                ("distributions", [gs_distro, s3_distro]),
                ("title", filename),
                ("types", ds_types),
                ("creators", creators),
                ])

        # input RNA/DNA extract that was sequenced
        # TODO - these appear to be the samples marked 'EXCLUDE'
        if sample_id not in dats_samples_d:
            logging.warn("no sample exists for " + sample_id + " found in file " + file['cram_file_aws']['raw_value'])
            continue

        dats_sample = dats_samples_d[sample_id]
        da = DatsObj("DataAcquisition", [
                ("name", filename),
                ("input", [dats_sample.getIdRef()]),
                ("output", [ds.getIdRef()]),             # link back to Dataset
#                ("uses", [])                            # software used
                ])
        ds.set("producedBy", [da])
        file_datasets.append(ds)

    return file_datasets
    
