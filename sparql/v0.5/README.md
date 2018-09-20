
# SPARQL Queries

This directory contains a small set of SPARQL queries and associated RDFLib scripts that are compatible
with the v0.5 crosscut metadata release. In the previous v0.4 release the SPARQL queries were embedded
in a single sample Python script and two shell scripts were provided to unpack the crosscut metadata
BDBag and run the Python script. One of these scripts ran the script directly on the JSON-LD files 
from the crosscut metadata BDBag. The other one (the "faster" version) first replaced all of the 
JSON-LD context file URIs in the JSON-LD with references to locally-downloaded copies of the context
files. The reason for this is that the RDFLib JSON-LD parser does not appear to do any caching
of context files, and because the crosscut metadata DATS JSON-LD files contain _many_ context file 
references, making it very very slow to parse the original JSON-LD files, particularly for the much 
larger controlled-access metadata files. For additional details on the incremental steps taken to 
improve the performance of the RDFLib JSON-LD parsing, see the v0.4 README.md:

https://github.com/dcppc/crosscut-metadata/tree/master/sparql/v0.4

In _this_ directory we still have two versions of the shell script: a "regular" one, run-sparql-queries.sh
and the faster one, run-sparql-queries-faster.sh  In addition, the handful of SPARQL queries have been 
split into separate files:

* sparql_list_2nd_level_datasets.py
* sparql_list_dataset_variables.py
* sparql_list_study_group_members.py

However, while replacing the remote context file references with local ones solved the RDFLib JSON-LD 
parser performance problem, we found that the SPARQL queries themselves were extremely slow to run, 
even on what should be reasonably-sized inputs. For example, running `sparql_list_2nd_level_datasets.py`
on the then 160MB public GTEx JSON-LD file took about 3 hours, even with local context files. The
time taken by this particular query increased drastically as more DATS `Dataset` objects were added 
to the JSON-LD file. In order to be able to run the queries in a reasonable time via RDFLib we 
re-implemented each of them directly using the RDFLib API (by making repeated calls to the `triples()`
function) rather than the SPARQL query evaluator. In the case of `sparql_list_2nd_level_datasets.py`
this reduced the runtime from 3 hours to about 90 seconds, most of that being the time it took the
JSON-LD parser to create ~663,000 RDF triples from the input JSON-LD file. This was done for each of
the example SPARQL queries, creating an 'rdflib' equivalent for each one:

* rdflib_list_2nd_level_datasets.py
* rdflib_list_dataset_variables.py
* rdflib_list_study_group_members.py

Each of these scripts has been annotated to show the RDFLib `triples()` calls that correspond to
each part of the (more or less) equivalent SPARQL query. In this release it is these `rdflib_*`
scripts, not the `sparql_*` ones that are invoked from the `run-sparql-queries-faster.sh` script.

