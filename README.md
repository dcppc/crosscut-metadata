
v0.2 Release Notes

This is the v0.2 release of the KC7 crosscut metadata model instance for GTEx v7 public RNA-Seq metadata
and TOPMed public metadata for a single sample study, phs000946.v3. The Python scripts used to generate 
this release may also be run on the dbGAP protected metadata for phs000946.v3, in which case they 
will produce DATS JSON for the actual (meta)data. In the absence of the protected metadata files the 
script will use the public dbGaP variable summaries to produce a single "dummy" subject/sample entry 
in which attribute values are chosen according to which occurs most commonly in the data (i.e., the
median for numeric values.) This may result in nonsensical combinations of attribute values, but at 
least produces a DATS metadata instance that is syntactically correct and may be freely distributed.

Note that this release does not yet make use of the BDBag Research Object profile to link DATS JSON-LD 
files to data files. This will be added in the next release.

Also note that although the DATS JSON files have been validated against the JSON schemas in the master 
branch of https://github.com/biocaddie/WG3-MetadataSpecifications, they will NOT validate against the 
current (v2.2) DATS release. A fork of the DATS schemas and JSON-LD context files has been created at 
the following URI and will be used by this project going forward:

https://github.com/datatagsuite

The following files can be found in the v0.2 BDBag (in the releases/ subdir):

data/docs/ChangeLog       
  ChangeLog for the crosscut metadata model instance.

data/docs/RELEASE_NOTES  
  A copy of this file.

data/datasets/gtex_v7_rnaseq_public.json
  A single DATS JSON file that represents the parent RNA-Seq Dataset (for the public GTEx v7 data only) and 
  the individual sub-Datasets/data files associated with it (e.g., gene read counts, exon read counts, TPMs)
  That Dataset is linked in turn to the RNA extracts (represented by DATS Materials) that were sequenced 
  and analyzed as part of the RNA-Seq analysis protocol.

data/datasets/TOPMed_phs000946_wgs_public.json
  A single DATS JSON file that represents the parent TOPMed Dataset. Each TOPMed study is represented as a 
  sub-Dataset of the top-level TOPMed Dataset. For one of the studies, phs000946.v3, a sample encoding for
  a single subject and DNA extract/sample is provided, based on the public dbGaP variable summary data.
  In order to obtain the DATS JSON for protected metadata it is necessary to download the Python code
  and run the DATS conversion script on both the public and protected metadata files for phs000946.v3.


