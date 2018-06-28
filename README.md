
# KC7 Crosscut Metadata Model 

The aim of the crosscut metadata model is to provide a uniform encoding of metadata obtained 
from the following DCPPC data sources:

* AGR - [Alliance of Genome Resources](https://www.alliancegenome.org/)
* GTEx - [Genotype-Tissue Expression project](https://www.gtexportal.org/home/)
* TOPMed - [Trans-Omics for Precision Medicine](https://www.nhlbi.nih.gov/science/trans-omics-precision-medicine-topmed-program)


## Metadata Model versus Instance

The metadata _model_ specifies _how_ the various metadata will be transformed into a uniform representation,
whereas the metadata model _instance_ is the transformed representation itself. The metadata model is based
on a JSON-LD encoding of [DATS](https://www.nature.com/articles/sdata201759), the DatA Tag Suite data model 
developed through the Big Data To Knowledge (BD2K) initiative to support dataset discoverability. See below 
for a description of how each of the 3 main datasets' metadata are encoded in DATS.


## Downloading the Crosscut Metadata Model Instance

The crosscut metadata model instance, which is essentially a small set of JSON-LD files, is distributed as a
[BDBag](http://bd2k.ini.usc.edu/tools/bdbag/). BDBags for all current releases can be found in the 
[releases/](https://github.com/dcppc/crosscut-metadata/tree/master/releases)
subdirectory. Each BDBag is a gzipped tar file that can be retrieved, extracted and uncompressed with 
standard Unix or Mac OS command line utilities. On a Mac, for example, the latest (as of this writing) 
v0.3 release can be retrieved and uncompressed with the following commands:

````
$ curl -s -O 'https://raw.githubusercontent.com/dcppc/crosscut-metadata/master/releases/KC7-crosscut-metadata-v0.3.tgz'
$ tar xzvf KC7-crosscut-metadata-v0.3.tgz 
x KC7-crosscut-metadata-v0.3/
x KC7-crosscut-metadata-v0.3/tagmanifest-md5.txt
x KC7-crosscut-metadata-v0.3/bagit.txt
x KC7-crosscut-metadata-v0.3/bag-info.txt
x KC7-crosscut-metadata-v0.3/tagmanifest-sha256.txt
x KC7-crosscut-metadata-v0.3/manifest-md5.txt
x KC7-crosscut-metadata-v0.3/data/
x KC7-crosscut-metadata-v0.3/data/datasets/
x KC7-crosscut-metadata-v0.3/data/datasets/TOPMed_phs000946_wgs_public.json
x KC7-crosscut-metadata-v0.3/data/datasets/GTEx_v7_rnaseq_public.json
x KC7-crosscut-metadata-v0.3/data/datasets/MGD_GRCm38-C57BL6J_public.json
x KC7-crosscut-metadata-v0.3/data/docs/
x KC7-crosscut-metadata-v0.3/data/docs/RELEASE_NOTES
x KC7-crosscut-metadata-v0.3/data/docs/ChangeLog
x KC7-crosscut-metadata-v0.3/manifest-sha256.txt
````

After uncompressing the DATS JSON-LD files can be found in `KC7-crosscut-metadata-v0.3/data/datasets`:

```
$ ls -al KC7-crosscut-metadata-v0.3/data/datasets/
total 461888
drwxr-xr-x  5 jcrabtree  staff        160 Jun 27 15:35 .
drwxr-xr-x  4 jcrabtree  staff        128 Jun 27 15:35 ..
-rw-r--r--  1 jcrabtree  staff   48188564 Jun 27 15:35 GTEx_v7_rnaseq_public.json
-rw-r--r--  1 jcrabtree  staff  188240933 Jun 27 15:35 MGD_GRCm38-C57BL6J_public.json
-rw-r--r--  1 jcrabtree  staff      52537 Jun 27 15:35 TOPMed_phs000946_wgs_public.json
```

If this sounds like too much work (it isn't), the most recent raw JSON files can also be found in the 
[dats-json/](https://github.com/dcppc/crosscut-metadata/tree/master/dats-json) subdirectory.


## Building the Crosscut Metadata Model Instance (on strictly public metadata)

The script to build the public crosscut metadata model instance is called `make-crosscut-instance-bdbag.sh`
and can be found in the top level of this repo:

https://github.com/dcppc/crosscut-metadata/blob/master/make-crosscut-instance-bdbag.sh

The script contains the commands to perform the DATS metadata conversion for each of the currently supported
data (sub)sets, but as the comments in the file indicate, you will first have to download a couple of 
plain text and/or tab-delimited metadata files for each of them:

### AGR/MGI

The script includes `curl` commands to download the requisite MGI flat files, but those commands are 
commented out by default:

```
mkdir -p mgd-data
cd mgd-data
curl -O http://www.informatics.jax.org/downloads/mgigff/MGI.gff3.gz
curl -O http://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt
cd ..
```

### GTEx

For GTEx the following two files are needed from https://www.gtexportal.org/home/datasets:

* GTEx_v7_Annotations_SubjectPhenotypesDS.txt
* GTEx_v7_Annotations_SampleAttributesDS.txt

### TOPMed

For the example TOPMed study, phs000946, the public TOPMed metadata/variable summaries should be
downloaded from the following URL into a local directory named phs000946.v3:

ftp://ftp.ncbi.nlm.nih.gov/dbgap/studies/phs000946/phs000946.v3.p1/pheno_variable_summaries/

### Other prerequisites

In order to run the command to create the BDBag, which is also in the script, you will need to 
install the bdbag command-line utility if you do not already have it:

```
pip install bdbag
```


## Building the Crosscut Metadata Model Instance on access-restricted metadata

The script mentioned above, `make-crosscut-instance-bdbag.sh`, also contains an example command showing
how to generate DATS JSON for the access-restricted metadata associated with the example TOPMed study,
phs000946. Simply add the access-restricted dbGaP files to the same local directory as the public 
files (or, even better, place them in a separate directory) and then tell the conversion script where
to find them, as in the example command:

./bin/topmed_to_dats.py --dbgap_public_xml_path=./phs000946.v3 --dbgap_protected_metadata_path=./phs000946.v3 \
 --output_file=$EXTERNAL_ID/metadata/annotations/datasets/TOPMed_phs000946_wgs_RESTRICTED.json


## DATS-JSON validation

All of the DATS JSON-LD files produced by the scripts have been validated using the validator provided
in the main DATS repository, https://github.com/datatagsuite/WG3-MetadataSpecifications. Any changes to 
the DATS JSON should be checked against the validator before making a new release.


## Model Description

This section describes how the three datasets are currently encoded in DATS and discusses some of the tradeoffs
and shortcomings inherent in the encoding. 

### GTEx encoding

TODO

### TOPMed encoding

TODO

### MGI encoding

TODO