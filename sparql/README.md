
# SPARQL Queries

This directory contains a small collection of SPARQL queries that demonstrate how to extract information from the 
DATS JSON-LD file that make up the crosscut metadata instance. The queries are currently embedded in a Python 
script (topmed_gtex_sparql_examples.py) that uses RDFLib (https://github.com/RDFLib/rdflib) and the RDFLib JSON-LD 
parser plugin (https://github.com/RDFLib/rdflib-jsonld) to parse and query the JSON-LD.

## Running the queries

NOTE: By default the `topmed_gtex_sparql_examples.py` script discussed below prints all of the RDF triples 
that were generated from the JSON-LD input file before running any queries. This can result in
verbose output to the terminal, which can be useful when developing queries, but may be excessive 
when the script is run on the larger JSON-LD files. To disable the triple printing simply comment out
the following 2 lines in the script:

```
    print("Parsed JSON-LD:")
    print(g.serialize(format='n3', indent=4).decode('ascii'))
```

A sample script (run-sparql-queries.sh) has been included to demonstrate how to run the queries. It first 
unpacks the BDBag for the v0.4 release into the current working directory (assuming that the v0.4 release
file is in `../releases`):

```
tar xzvf ../releases/KC7-crosscut-metadata-v0.4.tgz
```

Next it runs the Python script containing the sample queries, passing to it the path of one of the DATS JSON-LD
files in the unpacked BDBag. This particular DATS file contains public GTEx metadata, but only for the first
20 samples (and subjects). This was done to reduce the file size to provide users with a smaller file suitable
for testing:

```
export JSON_DIR=KC7-crosscut-metadata-v0.4/data/datasets/

time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public.jsonld
```

For reasons that will be discussed in the next section, parsing and running queries on even this very small
(~300KB) file is quite slow, about 1.5 minutes. Therefore in any further testing or processing of these
files using RDFLib it is highly recommended that the remote context URIs in the JSON-LD files be replaced
with local context file references. A second script, `run-sparql-queries-faster.sh`, illustrates how this
may be accomplished. Step 1 is to download the relevant schema.org and OBO Foundry context files:

```
# download context files locally
git clone git@github.com:datatagsuite/context.git
```

Step 2 is to rewrite the context file URIs in the JSON-LD files, which can be accomplished with the 
following set of Perl 1-liners:

```
# rewrite JSON-LD files to use local contexts
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public.jsonld >$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_rnaseq_public.jsonld >$JSON_DIR/GTEx_v7_rnaseq_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public.jsonld >$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_dbGaP_public.jsonld >$JSON_DIR/GTEx_v7_dbGaP_public_local_contexts.jsonld
```

Each of the JSON-LD files in the BDBag should now have an "_local_contexts" counterpart that refers 
to the newly-downloaded context files. Using the local contexts the performance should be acceptable
for all of the JSON-LD files based on public dbGaP metadata. Note also that the SPARQL queries
have been written in such a way that they work on both the GTEx and TOPMed metadata files:

```
# takes about 2-3 seconds using local context files (vs ~95 seconds using GitHub context URIs)
time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public_local_contexts.jsonld
# takes about 9-10 seconds using local context files
time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public_local_contexts.jsonld
# takes about 6-7 seconds using local context files
time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/GTEx_v7_dbGaP_public_local_contexts.jsonld
```

The final JSON-LD file, `GTEx_v7_rnaseq_public_local_contexts.jsonld`, is significantly larger than
the others, at about 135MB after context URI replacement. Parsing and querying this file can take
5-10 minutes, so for larger files like this one it may make sense to parse the JSON-LD and load the
resulting triples into an RDF triple store before attempting to run any queries and/or finding a 
faster parser than the RDFLib JSON-LD plugin.


## RDFLib parser and query performance

The v0.4 crosscut metadata model instance releases makes use of multiple JSON-LD context files, which means that 
each DATS entity in the instance points to two distinct JSON-LD context files, one defined using schema.org 
vocabularies and one defined using the (typically more specific) OBO Foundry terms. For example, the following 
JSON-LD excerpt shows some of the properties of a DATS Dataset entity, including the JSON-LD @context property
that contains a list of the context file URIs:

```
{
  "@type": "Dataset",
  "@context": [
    "https://w3id.org/dats/context/sdo/dataset_sdo_context.jsonld",
    "https://w3id.org/dats/context/obo/dataset_obo_context.jsonld"
  ],
  "version": "v7",
  "title": "Genotype-Tissue Expression Project (GTEx)",
  ...
```

If both context files define a mapping for a given property it is the last context file in the list (i.e, the
OBO Foundry file) whose mapping will take precedence.
