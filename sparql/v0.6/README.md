
# v0.6 SPARQL Queries

This directory contains a set of SPARQL queries and associated RDFLib scripts that are compatible
with the v0.6 crosscut metadata release. To understand the organization of the files in this directory
it may be helpful to review the notes in the preceding two releases (v0.4 and v0.5). In each of these
releases, workarounds and/or optimizations were adopted in order to improve the speed of RDFLib's 
parsing (v0.4) and querying (v0.5) of the DATS JSON-LD files that comprise the crosscut metadata model 
instance:

* https://github.com/dcppc/crosscut-metadata/tree/master/sparql/v0.4 describes the use of locally-cached
JSON-LD context files to improve the performance of the RDFLib JSON-LD parser.
* https://github.com/dcppc/crosscut-metadata/tree/master/sparql/v0.5 describes the use of direct 
RDFLib API calls (the rdflib_* scripts) in lieu of SPARQL queries (the corresponding sparql_* 
scripts) to achieve acceptable query performance in RDFLib.

In keeping with this theme, the main change made in v0.6 was to refactor the RDFLib queries into 
standalone Python functions, which allows a single RDFLib script to parse the JSON-LD document
once and then run all of the available queries on the RDF graph without having to re-parse the
JSON files each time. In v0.5 the queries were only available as standalone scripts, meaning that 
running 3 test queries entailed reading and parsing each JSON-LD document three times. For the 
controlled access metadata files it can take RDFLib (even with local context files and some additional
optimizations) 3-4 minutes just to parse the input file. The rdflib_test_* scripts in this directory
illustrate the use of this technique: they parse the JSON-LD input once, call several of the 
test functions, and then exit. This is closer to the expected production use of the crosscut
metadata model instance: we would expect that in production use the instance would first be loaded 
into a persistent triple store and then interrogated through whatever SPARQL or other query API 
the triple store supports. Alternatively, the `make-tabular-dump.sh` script in this directory could
be adapted to dump the requisite metadata into a set of tab-delimited files that could then be
ingested into some other data management system.
