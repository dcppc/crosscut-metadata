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

    subj_key = ":".join(["Material", dats_subject.get("name")])
    dats_subj = cache.get_obj_or_ref(subj_key, lambda: dats_subject)
        
    # biological/tissue sample
    biological_sample_material = DatsObj("Material", [
            ("name", samp_id),
            ("identifier", { "identifier": identifier }),
            ("description", anatomy_name + " specimen collected from subject " + subj_id),
            # TODO - use id refs for these too:
            ("taxonomy", [ util.get_taxon_human(cache) ]),
            ("roles", [ util.get_annotation("specimen", cache) ]),
            ("derivesFrom", [ dats_subj, anatomical_part ])
            ])

    # analysis freeze classification
    smafrze = p_sample['SMAFRZE']['mapped_value']
    # expected sequence type depending on data freeze classification
    expected_stype = None

    stype = None
    if smafrze == "RNASEQ":
        expected_stype = "RNA"
    elif smafrze == "WGS":
        expected_stype = "DNA"
    elif smafrze == "WES":
        expected_stype = "DNA"
    # Illumina OMNI SNP Array
    elif smafrze == "OMNI": 
        expected_stype = "DNA"
    elif smafrze == "EXCLUDE":
        pass
    else:
        logging.fatal("unknown SMAFRZE " + smafrze)
        sys.exit(1)

    # sample type - DNA or RNA
    stype = None
    smnabtcht = p_sample['SMNABTCHT']['mapped_value']
    if re.match(r'^DNA ([iI]solation|[eE]xtraction).*', smnabtcht):
        stype = 'DNA'
    elif re.match(r'^RNA ([iI]solation|[eE]xtraction).*', smnabtcht):
        stype = 'RNA'
    elif re.match(r'DNA or RNA Extraction from Paxgene-derived Lysate Plate Based', smnabtcht):
        stype = 'RNA'
    elif re.match(r'Transfer To Matrix \(Manual\)', smnabtcht):
        stype = 'DNA'

    if stype is None:
        if expected_stype is not None:
            stype = expected_stype
        else:
            print("couldn't determine sequence type for smafrze=" + smafrze + " smnabtcht=" + smnabtcht)
            return None
    else:
        if (expected_stype is not None) and (stype != expected_stype):
            logging.fatal("seq type " + stype + " doesn't match expected stype " + expected_stype)
            sys.exit(1)

    # DNA or RNA extract
    dna_or_rna_material = DatsObj("Material", [
            ("name", stype + " from " + samp_id),
            ("description", "total " + stype + " extracted from " + anatomy_name + " specimen collected from subject " + subj_id),
            # TODO - use id ref for this:
            ("taxonomy", [ util.get_taxon_human(cache) ]),
            ("roles", [ util.get_annotation(stype + " extract", cache) ]),
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
def get_files_dats_datasets(cache, dats_samples_d, p_samples, gh_samples, protected_cram_files, no_circular_links):
    file_datasets = []

    rnaseq_types = DatsObj("DataType", [
            ("information", util.get_annotation("transcription profiling", cache)),
            ("method", util.get_annotation("RNA-seq assay", cache)),
            ("platform", util.get_annotation("Illumina", cache))
            ])

    wgs_types = DatsObj("DataType", [
            ("information", util.get_annotation("DNA sequencing", cache)),
            ("method", util.get_annotation("whole genome sequencing assay", cache)),
            ("platform", util.get_annotation("Illumina", cache))
            ])

    broad_key = ":".join(["Organization", "Broad Institute"])
    broad = cache.get_obj_or_ref(broad_key, lambda: DatsObj("Organization", [("name", "Broad Institute")]))
    creators = [broad]

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
            gcp_suffix = '_gcp'
        elif re.search(r'rnaseq\/', file['cram_file_aws']['raw_value']):
            material_type = 'RNA'
            ds_types = rnaseq_types
            gcp_suffix = ''
        else:
            logging.fatal("unable to determine material/sequence type from cram_file_aws=" + file['cram_file_aws']['raw_value'])
            sys.exit(1)

        # RNA-Seq keys = sample_id	cram_file	cram_file_md5	cram_file_size	cram_index	cram_file_aws	cram_index_aws
        # WGS keys = same as above + firecloud_id
        cram_file = file['cram_file' + gcp_suffix]['raw_value']
        cram_file_md5 = file['cram_file_md5']['raw_value']

        # TODO - review the following encoding decisions:
        #  - storing .crai URI as relatedIdentifier of the DatasetDistribution for the .cram file
        #  - storing MD5 checksum of the .cram file as an extraProperty of the DatasetDistribution
        #  - storing firecloud_id as a relatedIdentifier of the Dataset (not the DatasetDistribution)

        # Google Cloud Platform / Google Storage copy
        gs_access = DatsObj("Access", [
                ("landingPage", file['cram_file' + gcp_suffix]['raw_value'])
                ])
        gs_distro = DatsObj("DatasetDistribution", [
                ("access", gs_access),
                ("identifier", DatsObj("Identifier", [("identifier", file['cram_file' + gcp_suffix]['raw_value'])])),
                ("relatedIdentifiers", [ DatsObj("RelatedIdentifier", [("identifier", file['cram_index' + gcp_suffix]['raw_value']), ("relationType", "cram_index") ])]),
                ("size", int(file['cram_file_size']['raw_value'])),
                # TODO - add unit for bytes
#                ("unit", DatsObj("Annotation", []))
                ("conformsTo", [cache.get_obj_or_ref(cram_ds_key, lambda: make_data_standard("CRAM"))])
                ])

        # AWS / S3 copy
        s3_access = DatsObj("Access", [
                ("landingPage", file['cram_file_aws']['raw_value'])
                ])
        s3_distro = DatsObj("DatasetDistribution", [
                ("access", s3_access),
                ("identifier", DatsObj("Identifier", [("identifier", file['cram_file_aws']['raw_value'])])),
                ("relatedIdentifiers", [ DatsObj("RelatedIdentifier", [("identifier", file['cram_index_aws']['raw_value']), ("relationType", "cram_index") ])]),
                ("size", int(file['cram_file_size']['raw_value'])),
                # TODO - add unit for bytes
#                ("unit", DatsObj("Annotation", []))
                ("conformsTo", [cache.get_obj_or_ref(cram_ds_key, lambda: make_data_standard("CRAM"))])
                ])

        m = re.match(r'^.*\/([^\/]+)$', cram_file)
        if m is None:
            logging.fatal("unable to parse filename from CRAM file URI " + cram_file)
            sys.exit(1)
        filename = m.group(1)
        
        # TODO - replace this with DATS-specific MD5 checksum encoding (TBD)
        md5_dimension = DatsObj("Dimension", [("name", "MD5"), ("values", [ file['cram_file_md5']['raw_value'] ])])

        ds = DatsObj("Dataset", [
                ("distributions", [gs_distro, s3_distro]),
                ("dimensions", [ md5_dimension ]),
                ("title", filename),
                ("types", [ ds_types ]),
                ("creators", creators),
                ])

        # add firecloud_id for WGS
        if 'firecloud_id' in file:
            f_id = DatsObj("RelatedIdentifier", [
                    ("identifier", file['firecloud_id']['raw_value']),
                    ("identifierSource", "FireCloud")
                    ])
            ds.set("relatedIdentifiers", [f_id])

        # input RNA/DNA extract that was sequenced
        if sample_id not in dats_samples_d:
            logging.fatal("no sample exists for " + sample_id + " found in file " + file['cram_file_aws']['raw_value'])
            sys.exit(1)

        dats_sample = dats_samples_d[sample_id]
        dats_samp_key = ":".join(["Material", dats_sample.get("name")])
        dats_samp = cache.get_obj_or_ref(dats_samp_key, lambda: dats_sample)

        da = DatsObj("DataAcquisition", [
                ("name", filename),
                ("input", [dats_samp])
#                ("uses", [])                          # software used
                ])

        if not no_circular_links:
            # circular link back to enclosing Dataset as the output
            da.set("output", [ds.getIdRef()])
            
        ds.set("producedBy", da)
        file_datasets.append(ds)

    return file_datasets
    
