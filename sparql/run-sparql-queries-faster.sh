#!/bin/bash

# Example showing parse speed improvement using locally cached context files.

# download context files locally
git clone git@github.com:datatagsuite/context.git

# rewrite JSON-LD file to use local contexts
perl -ne 's/https:\/\/(datatagsuite.github.io|w3id.org)\//.\//; print;' <TOPMed_phs000946_wgs_public_v0.4preview2.jsonld >TOPMed_phs000946_wgs_public_v0.4preview2_local_contexts.jsonld

# takes about 2 seconds using local contexts (vs 35-40 seconds using GitHub context URIs)
time ./topmed_sparql_examples.py --topmed_file=./TOPMed_phs000946_wgs_public_v0.4preview2_local_contexts.jsonld
