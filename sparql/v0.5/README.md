
# SPARQL Queries

This directory contains work in progress for the upcoming v0.5 release. The default RDFLib SPARQL query
evaluation engine appears to perform little or no query optimization, meaning that even relatively simple
queries can run extremely slowly. In one test with the current pre-release public GTEx JSON-LD file 
RDFLib took 3 hours to run a single SPARQL query. That same query implemented manually using RDFLib API
calls runs in about 90 seconds, including the time taken to parse the JSON-LD file.
