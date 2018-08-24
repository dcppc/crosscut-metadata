
# SPARQL Queries

This directory contains a small collection of SPARQL queries that demonstrate how to extract information 
from the DATS JSON-LD files that make up the crosscut metadata instance. The queries are currently embedded 
in a Python script (`topmed_gtex_sparql_examples.py`) that uses RDFLib (https://github.com/RDFLib/rdflib) 
and the RDFLib JSON-LD parser plugin (https://github.com/RDFLib/rdflib-jsonld) to parse and query the JSON-LD.


## Running the queries

NOTE: By default the `topmed_gtex_sparql_examples.py` script discussed below prints all of the RDF triples 
that were generated from the JSON-LD input file before running any queries. This can result in
verbose output to the terminal, which can be useful when developing queries, but may be excessive 
when the script is run on the larger JSON-LD files in the current release. To disable the triple printing 
simply comment out the following 2 lines in the script:

```
    print("Parsed JSON-LD:")
    print(g.serialize(format='n3', indent=4).decode('ascii'))
```

A sample script (`run-sparql-queries.sh`) has been included to demonstrate how to run the queries. It first 
unpacks the BDBag for the v0.4 release into the current working directory (assuming that the v0.4 release
file is in `../releases`):

```
tar xzvf ../releases/KC7-crosscut-metadata-v0.4.tgz
```

Next it runs the Python script containing the sample queries, passing to it the path of one of the DATS JSON-LD
files in the unpacked BDBag. This particular DATS file contains public GTEx metadata, but only for the first
20 samples (and subjects). This was done to reduce the file size to provide users with a smaller file suitable
for this type of testing:

```
export JSON_DIR=KC7-crosscut-metadata-v0.4/data/datasets/

time ./topmed_gtex_sparql_examples.py --dats_file=$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public.jsonld
```

For reasons that will be discussed in the next section, parsing and running queries on even this very small
(~300KB) file is quite slow, about 1.5 minutes on a MacBook Pro. Therefore in any further testing or processing 
of these files using RDFLib it is highly recommended that the remote context URIs in the JSON-LD files be 
replaced with local context file references. A second script, `run-sparql-queries-faster.sh`, illustrates 
one way in which this may be accomplished. Step 1 is to download the relevant schema.org and OBO Foundry 
context files:

```
# download context files locally
git clone git@github.com:datatagsuite/context.git
```

Step 2 is to rewrite the context file URIs in the JSON-LD files, for example with the following set of Perl 1-liners:

```
# rewrite JSON-LD files to use local contexts
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public.jsonld >$JSON_DIR/GTEx_v7_rnaseq_20_SAMPLES_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_rnaseq_public.jsonld >$JSON_DIR/GTEx_v7_rnaseq_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public.jsonld >$JSON_DIR/TOPMed_phs000951_phs000946_phs001024_wgs_public_local_contexts.jsonld
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <$JSON_DIR/GTEx_v7_dbGaP_public.jsonld >$JSON_DIR/GTEx_v7_dbGaP_public_local_contexts.jsonld
```

Each of the JSON-LD files in the BDBag should now have a "_local_contexts" counterpart that uses
the newly-downloaded context files. Running the queries on these files should yield reasonable
performance for all of the v0.4 files except one. Here are the commands (from the script) used 
to run the queries on each of the files. Note the expected parse/query times indicated in the 
comments, and also the fact that the same queries work on both the TOPMed and GTEx files, providing
some assurance that the overall structure of the DATS encoding is consistent across data source:

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
5-10 minutes in RDFLib, so for larger files like this one it may make sense to parse the JSON-LD 
and load the resulting triples into an RDF triplestore before attempting to run queries. Using a 
more efficient parser (e.g., one of the available Java-based tools) may also improve the time it
takes to generate triples from the JSON-LD input.


## RDFLib parser / SPARQL query performance

The v0.4 crosscut metadata model instance release makes use of multiple JSON-LD context files, which means that 
each DATS entity in the instance points to two distinct JSON-LD context files, one defined using schema.org 
("sdo") vocabularies and one defined using the (typically more specific) OBO Foundry terms ("obo"). For example, 
the following JSON-LD excerpt shows some of the properties of a DATS Dataset entity, including the JSON-LD 
@context property that points to the JSON-LD context file URIs:

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

### Multiple context files: 2X slowdown

If both context files define a mapping for a given property it is the last context file in the list (i.e, the
OBO Foundry file) whose mapping will take precedence. In our limited testing, switching from the single SDO 
context file to two context files (SDO + OBO) increased the time it takes the RDFLib JSON-LD parser to parse 
a simple JSON-LD file by about a factor of 2.

### Avoiding redirects: 3X speedup

It appears to be the case that--at least in its default configuration--the RDFLib JSON-LD parser plugin 
attempts to individually resolve each and every context file URI reference, without doing any caching, 
either of the context files themselves or of any redirects encountered while resolving the URI found in
the JSON-LD file. As a result our limiting testing also determined that a 2-3X speedup could be obtained
by replacing the w3id.org context file URIs like those shown below:

```
  "@context": [
    "https://w3id.org/dats/context/sdo/dataset_sdo_context.jsonld",
    "https://w3id.org/dats/context/obo/dataset_obo_context.jsonld"
  ],
```

with the corrsponding GitHub URIs (to which the above w3id.org URIs redirect):

```
  "@context": [
    "https://datatagsuite.github.io/context/sdo/dataset_sdo_context.jsonld",
    "https://datatagsuite.github.io/context/obo/dataset_obo_context.jsonld"
  ],
```

### Using local context files: 10X-100X speedup

However, even with the github.io URIs the RDFLib JSON-LD parser plugin still appears to be making at least
one HTTPS request for each and every context file reference. Switching to context files stored on the local
file system therefore results in a further speedup of at least 10X and in any many cases much more, depending 
on the complexity of the input DATS JSON and the number of embedded context file URIs. This is the technique 
used by the `run-sparql-queries-faster.sh` script mentioned above. There is some room for improving the 
DATS JSON encoding in such way that parsing should take less time regardless of the parser used. For example,
the following changes could be implemented:

 * Merge the two separate sets of context files into one set.
 * Make more extensive use of JSON-LD id references to avoid excessive duplication of JSON entities.

However, the best long-term solution would be to switch to a JSON-LD parser that caches the parsed 
representation of each context file in-memory. Even with the local context file technique used above 
it is still likely that the RDFLib plugin is having to read each context file from the file system
every time a reference to one is encountered (i.e., twice for each and every DATS entity.)


