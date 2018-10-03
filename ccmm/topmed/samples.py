#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
import ccmm.dats.util as util
import ccmm.topmed.dna_extracts as dna_extracts
from collections import OrderedDict
import logging
import re
import sys

NIH_NHLBI = DatsObj("Organization", [
        ("name", "The National Institute of Health's National Heart, Lung and Blood Institute"),
        ("abbreviation", "NHLBI")
        ])

# Produce a DATS Material for a single sample.

def get_sample_dats_material(cache, dats_subject, study, study_md, samp_var_values):

    # Almost all samples in TOPMed WGS phase are blood samples, named "Blood", "Peripheral Blood"...
    # Few samples are saliva samples probably due to sample collection issues
    name = None
    if 'BODY_SITE' in samp_var_values:
        name = 'BODY_SITE'
    elif 'Body_Site' in samp_var_values:
        name = 'Body_Site'
    elif 'Body Site' in samp_var_values:
        name = 'Body Site'
        
    anat_id = None
    anatomy_name = None
        
    if name is not None:
        if "blood" in samp_var_values[name]['value'].lower():
            anatomy_name = "blood"
            anat_id = "0000178"
        elif samp_var_values[name]['value'].lower() == "saliva":
            anatomy_name = "saliva"
            anat_id = "0001836"        
        else:
            logging.fatal("encountered BODY_SITE other than 'Blood' and 'Saliva' in TOPMed sample metadata - " + samp_var_values['BODY_SITE']['value'])
            sys.exit(1)

    def make_anat_part(anat_id, anatomy_name):
        # anatomical part
        anatomical_part = DatsObj("AnatomicalPart", [
            ("name", anatomy_name)
        ])

        if anat_id is not None:
            anatomy_identifier = OrderedDict([
                ("identifier",  "UBERON:" + str(anat_id)),
                ("identifierSource", "UBERON")])
            anatomy_alt_ids = [OrderedDict([
                ("identifier", "http://purl.obolibrary.org/obo/UBERON_" + str(anat_id)),
                ("identifierSource", "UBERON")])]

            anatomical_part.set("identifier", anatomy_identifier)
            anatomical_part.set("alternateIdentifiers", anatomy_alt_ids)

        return anatomical_part

    if anatomy_name is not None:
        # use cached value for AnatomicalPart if possible
        anat_part_key = ":".join(["AnatomicalPart", anatomy_name])
        anatomical_part = cache.get_obj_or_ref(anat_part_key, lambda: make_anat_part(anat_id, anatomy_name))
    else:
        anatomical_part = None

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

    # create DATS Dimensions for dbGaP sample metadata
    sample_dimensions = [ make_var_dimension(vname, samp_var_values[vname]) for vname in sorted(samp_var_values) ]

    sample_characteristics = sample_dimensions
    samp_id = samp_var_values['SAMPLE_ID']['value']
    dbgap_samp_id = samp_var_values['dbGaP_Sample_ID']['value']
    study_title = study.get("title")
    specimen_annot = util.get_annotation("specimen", cache)

    # corresponding DATS subject Material
    subj_key = ":".join(["Material", dats_subject.get("name")])
    dats_subj = cache.get_obj_or_ref(subj_key, lambda: dats_subject)
    dats_subj_name = dats_subject.get("name")

    # biological/tissue sample
    sample_name = samp_id
    sample_derives_from = [ dats_subj ]

    sample_descr = "specimen collected from subject " + dats_subj_name
    if anatomical_part is not None:
        sample_derives_from.append(anatomical_part)
        sample_descr = anatomy_name + " " + sample_descr

    biological_sample_material = DatsObj("Material", [
            ("name", sample_name),
            ("identifier", { "identifier": samp_id }),
            ("alternateIdentifiers", [ util.get_alt_id(dbgap_samp_id, "dbGaP") ]),
            ("description", sample_descr),
            ("characteristics", sample_characteristics),
            ("taxonomy", [ util.get_taxon_human(cache) ]),
            ("roles", [ specimen_annot ]),
            ("derivesFrom", sample_derives_from )
            ])

    # RNA or DNA extracted from tissue sample
    stype = "DNA"
    # TODO - check if RNA, not DNA

    dna_or_rna_descr = stype + " extracted from specimen collected from subject " + dats_subj_name
    if anatomical_part is not None:
        dna_or_rna_descr = stype + " extracted from " + anatomy_name + " specimen collected from subject " + dats_subj_name

    dna_or_rna_material = DatsObj("Material", [
        ("name", stype + " from " + sample_name),
        ("description", dna_or_rna_descr),
        ("taxonomy", [ util.get_taxon_human(cache) ]),
        ("roles", [ util.get_annotation(stype + " extract", cache) ] ),
        ("derivesFrom", [ biological_sample_material ])
    ])
    return dna_or_rna_material

def add_properties(o1, o2, vars1, vars2):
    for p in o2:
        if p in o1:
            if o1[p] != o2[p]:
                logging.fatal("property add/merge failed: o1[p]=" + o1[p] + " o2[p]=" + o2[p])
                sys.exit(1)
        else:
            o1[p] = o2[p]
            vars1[p] = vars2[p]

def get_synthetic_sample_dats_material_from_public_metadata(cache, dats_subject, study, pub_md, dbgap_samp_id, samp_id):
    dats_samples_d = {}
    
    # Sample summary data
    samp_var_values = {}
    for var_type in ('Sample', 'Sample_Attributes'):
        if var_type not in pub_md:
            continue
        samp_data = pub_md[var_type]['var_report']['data']
        samp_vars = samp_data['vars']
        for sv in samp_vars:
            id = sv['id']
            m = re.match(r'^(phv\d+\.v\d+).*$', id)
            if m is not None:
                sv['dim'] = pub_md['id_to_var'][m.group(1)]['dim']
            else:
                logging.warn("failed to parse variable prefix from " + id)

        # pick representative and/or legal value for each variable
        samp_var_values = dna_extracts.pick_var_values(samp_vars, samp_var_values)

    # assign dummy ids: subject and sample ids are protected data
    samp_var_values['dbGaP_Sample_ID'] = { "value": dbgap_samp_id }
    samp_var_values['SAMPLE_ID'] = { "value" : samp_id }

    dats_extract = get_sample_dats_material(cache, dats_subject, study, pub_md, samp_var_values)
    dats_samples_d[samp_var_values['dbGaP_Sample_ID']['value']] = dats_extract

    return dats_samples_d

def get_samples_dats_materials_from_restricted_metadata(cache, dats_subjects, study, pub_md, restricted_md):
    dats_samples_d = {}

    def lookup_var_ids(d, typename, consent_group):
        var_ids = {}
        for k in d:
            cg_key = k + consent_group
            if cg_key in pub_md['type_name_cg_to_var'][typename]:
                var_ids[k] = pub_md['type_name_cg_to_var'][typename][cg_key]
            else:
                logging.warn("unable to find dbGaP id for " + cg_key)
        return var_ids

    # Sample
    # e.g., ['dbGaP_Subject_ID', 'dbGaP_Sample_ID', 'BioSample Accession', 'SUBJECT_ID', 'SAMPLE_ID', 'SAMPLE_USE']
    sample_md = restricted_md['Sample']
    # samples indexed by dbGaP ID
    logging.debug("indexing restricted Sample")
    samples = dna_extracts.index_dicts(sample_md['data']['rows'], 'dbGaP_Sample_ID')
    samples_vars = lookup_var_ids(sample_md['data']['rows'][0], 'Sample', '')

    sample_atts = None
    sample_atts_vars = None

    # Sample_Attributes
    # e.g., ['dbGaP_Sample_ID', 'SAMPLE_ID', 'BODY_SITE', 'ANALYTE_TYPE', 'IS_TUMOR', 'SEQUENCING_CENTER', 'Funding_Source', 'TOPMed_Phase', 'TOPMed_Project', 'Study_Name']
    if 'Sample_Attributes' in restricted_md:
        sample_atts_md = restricted_md['Sample_Attributes']
        logging.debug("indexing restricted Sample_Attributes file")
        sample_atts = dna_extracts.index_dicts(sample_atts_md['data']['rows'], 'dbGaP_Sample_ID')
        sample_atts_vars = lookup_var_ids(sample_atts_md['data']['rows'][0], 'Sample_Attributes', '')
    
    # generate JSON for each sample
    for dbgap_samp_id in samples:
        sample = samples[dbgap_samp_id]

        # variable mappings after merging the two sets of attributes
        combined_vars = samples_vars.copy()

        samp_id = sample['dbGaP_Sample_ID']
        if 'SAMPLE_ID' in sample:
            samp_id = sample['SAMPLE_ID']
        subj_id = sample['dbGaP_Subject_ID']
        dats_subject = dats_subjects[subj_id]
 
        # merge sample attribute info
        if sample_atts is not None and dbgap_samp_id in sample_atts:
            sample_att = sample_atts[dbgap_samp_id]
            add_properties(sample, sample_att, combined_vars, sample_atts_vars)

        sample_att_vals = {}

        for sa in sample:
            # filter out any attributes that don't belong in characteristics
            if sa != 'subject':
                sample_att_vals[sa] = { "value": sample[sa] }
                if sa in combined_vars:
                    sample_att_vals[sa]["var"] = combined_vars[sa]

        dats_sample = get_sample_dats_material(cache, dats_subject, study, pub_md, sample_att_vals)
        dats_samples_d[samp_id] = dats_sample

    return dats_samples_d

# create Datasets for file-level links based on TOPMed manifest file
def get_files_dats_datasets(cache, dats_samples_d, sample_manifest, no_circular_links):
    file_datasets_l = []

    wgs_datatype = DatsObj("DataType", [
            ("information", util.get_annotation("DNA sequencing", cache)),
            ("method", util.get_annotation("whole genome sequencing assay", cache)),
            ("platform", util.get_annotation("Illumina", cache))
            ])

    def get_wgs_datatype():
        dkey = ".".join(["DataType", "WGS"])
        return cache.get_obj_or_ref(dkey, lambda: wgs_datatype)

    snp_datatype = DatsObj("DataType", [
            ("information", util.get_annotation("SNP", cache)),
            ("method", util.get_annotation("SNP analysis", cache))
            ])

    cnv_datatype = DatsObj("DataType", [
            ("information", util.get_annotation("CNV", cache)),
            ("method", util.get_annotation("CNV analysis", cache))
            ])

    def get_snp_datatype():
        dkey = ".".join(["DataType", "SNP"])
        return cache.get_obj_or_ref(dkey, lambda: snp_datatype)

    def get_cnv_datatype():
        dkey = ".".join(["DataType", "CNV"])
        return cache.get_obj_or_ref(dkey, lambda: cnv_datatype)

    nhlbi_key = ":".join(["Organization", "NHLBI"])
    nhlbi = cache.get_obj_or_ref(nhlbi_key, lambda: NIH_NHLBI)
    creators = [nhlbi]

    def make_data_standard(format):
        return DatsObj("DataStandard", [
            ("name", format),
            ("type", util.get_value_annotation("format", cache)),
            ("description", format + " file format")
            ])
    
    cram_ds_key = ":".join(["DataStandard", "CRAM"])
    cram_dstan = cache.get_obj_or_ref(cram_ds_key, lambda: make_data_standard("CRAM"))

    vcf_ds_key = ":".join(["DataStandard", "VCF"])
    vcf_dstan = cache.get_obj_or_ref(vcf_ds_key, lambda: make_data_standard("VCF"))

    n_samples = len(dats_samples_d)
    n_samples_found = 0

    for sample_id in dats_samples_d:
        dats_sample = dats_samples_d[sample_id]

        # look up corresponding file paths in manifest file
        if sample_id not in sample_manifest:
            logging.debug("sample not found in manifest - " + sample_id)
            continue

        n_samples_found += 1
        ms = sample_manifest[sample_id]

        material_type = 'DNA'
        wgs_type = get_wgs_datatype()
        snp_type = get_snp_datatype()
        cnv_type = get_cnv_datatype()

        # ------------------------------------------------
        # WGS sequence - CRAM and CRAI files
        # ------------------------------------------------

        # Google Cloud Platform / Google Storage copy
        gs_cram = ms['gs_cram']['mapped_value']
        gs_crai = ms['gs_crai']['mapped_value']
        gs_cram_access = DatsObj("Access", [ ("landingPage", gs_cram) ])
        gs_cram_distro = DatsObj("DatasetDistribution", [
            ("access", gs_cram_access),
            ("identifier", DatsObj("Identifier", [("identifier", gs_cram)])),
            ("relatedIdentifiers", [ DatsObj("RelatedIdentifier", [("identifier", gs_crai), ("relationType", "cram_index") ])]),
            # TODO - add file size and units, MD5 checksum
            ("conformsTo", [ cram_dstan ])
        ])

        # AWS / S3 copy
        s3_cram = ms['s3_cram']['mapped_value']
        s3_crai = ms['s3_crai']['mapped_value']
        s3_cram_access = DatsObj("Access", [ ("landingPage", s3_cram) ])
        s3_cram_distro = DatsObj("DatasetDistribution", [
            ("access", s3_cram_access),
            ("identifier", DatsObj("Identifier", [("identifier", s3_cram)])),
            ("relatedIdentifiers", [ DatsObj("RelatedIdentifier", [("identifier", s3_crai), ("relationType", "cram_index") ])]),
            # TODO - add file size and units, MD5 checksum
            ("conformsTo", [ cram_dstan ])
        ])

        m = re.match(r'^.*\/([^\/]+)$', gs_cram)
        if m is None:
            logging.fatal("unable to parse filename from CRAM file URI " + gs_cram)
            sys.exit(1)
        filename = m.group(1)

        cram_dataset = DatsObj("Dataset", [
            ("distributions", [gs_cram_distro, s3_cram_distro]),
#            ("dimensions", [ md5_dimension ]),
            ("title", filename),
            ("types", [ wgs_type ]),
            ("creators", creators),
        ])

        cram_da = DatsObj("DataAcquisition", [
            ("name", filename),
            ("input", [dats_sample.getIdRef()])
#            ("uses", [])                          # software used
        ])

        cram_dataset.set("producedBy", cram_da)
        # circular link back to enclosing Dataset as the output
        if not no_circular_links:
            cram_da.set("output", [cram_dataset.getIdRef()])
        file_datasets_l.append(cram_dataset)

        # ------------------------------------------------
        # Variant calls - VCF and CSI files
        # ------------------------------------------------

        # Google Cloud Platform / Google Storage copy
        gs_vcf = ms['gs_vcf']['mapped_value']
        gs_csi = ms['gs_csi']['mapped_value']
        gs_vcf_access = DatsObj("Access", [ ("landingPage", gs_vcf) ])
        gs_vcf_distro = DatsObj("DatasetDistribution", [
            ("access", gs_vcf_access),
            ("identifier", DatsObj("Identifier", [("identifier", gs_vcf)])),
            ("relatedIdentifiers", [ DatsObj("RelatedIdentifier", [("identifier", gs_csi), ("relationType", "vcf_index") ])]),
            # TODO - add file size and units, MD5 checksum
            ("conformsTo", [ vcf_dstan ])
        ])

        # AWS / S3 copy
        s3_vcf = ms['s3_vcf']['mapped_value']
        s3_csi = ms['s3_csi']['mapped_value']
        s3_vcf_access = DatsObj("Access", [ ("landingPage", s3_vcf) ])
        s3_vcf_distro = DatsObj("DatasetDistribution", [
            ("access", s3_vcf_access),
            ("identifier", DatsObj("Identifier", [("identifier", s3_vcf)])),
            ("relatedIdentifiers", [ DatsObj("RelatedIdentifier", [("identifier", s3_csi), ("relationType", "vcf_index") ])]),
            # TODO - add file size and units, MD5 checksum
            ("conformsTo", [ vcf_dstan ])
        ])

        m = re.match(r'^.*\/([^\/]+)$', gs_vcf)
        if m is None:
            logging.fatal("unable to parse filename from VCF file URI " + gs_vcf)
            sys.exit(1)
        filename = m.group(1)

        vcf_dataset = DatsObj("Dataset", [
            ("distributions", [gs_vcf_distro, s3_vcf_distro]),
#            ("dimensions", [ md5_dimension ]),
            ("title", filename),
            ("types", [ snp_type, cnv_type ]),
            ("creators", creators),
        ])

        vcf_da = DatsObj("DataAcquisition", [
            ("name", filename),
            ("input", [dats_sample.getIdRef()])
#            ("uses", [])                          # software used
        ])

        vcf_dataset.set("producedBy", vcf_da)
        # circular link back to enclosing Dataset as the output
        if not no_circular_links:
            vcf_da.set("output", [vcf_dataset.getIdRef()])
        file_datasets_l.append(vcf_dataset)

    logging.info("found " + str(n_samples_found) + " / " + str(n_samples) + " sample(s) in TOPMed file manifest")
    return file_datasets_l
    
