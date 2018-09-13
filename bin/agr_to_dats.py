#!/usr/bin/env python3

# Create DATS JSON description of MODs data
# At minimum it will include genes, gene names, human orthologs, and associated diseases

import argparse
from ccmm.dats.datsobj import DatsObj, DatsObjCache
from collections import OrderedDict
from ccmm.dats.datsobj import DATSEncoder
import ccmm.agr.ref_genome_dataset
import ccmm.agr.genes
import json
import logging
import os
import re
import sys

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for Mouse Genome Database reference genome and annotation.')
    parser.add_argument('--agr_genomes_list', required=True, help ='Comma-delimited list of MOD releases to convert to DATS. Eg. MGI_1.0.4_2,RGD_1.0.4_3')
    parser.add_argument('--output_file', required=True, help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    parser.add_argument('--bgi_gff3_disease_path', required=True, help ='Path to directory that contains Basic Gene Information (BGI), GFF3 and disease_json files.')
    parser.add_argument('--ortholog_file', required=True, help ='Path to filtered ortholog file from AGR (.tsv)')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)
    
    # cache used to minimize duplication of JSON objects in JSON-LD output
    cache = DatsObjCache()

    # convert accession list to dict
    acc_d = {}
    for acc in args.agr_genomes_list.split(","):
        acc_d[acc] = True

    # create top-level dataset
    agr_dataset = ccmm.agr.ref_genome_dataset.get_dataset_json(acc_d)

    # index reference genomes by id
    ref_genomes_by_id = {}
    for rgds in agr_dataset.get("hasPart"):
        ref_genome_id = rgds.get("identifier").get("identifier")
        if ref_genome_id in ref_genomes_by_id:
            logging.fatal("encountered duplicate ref_genome_id " + ref_genome_id)
            sys.exit(1)
        m = re.match(r'^(\w+_\d+\.\d+\.\d+)$', ref_genome_id)
        if m is None:
            logging.fatal("unable to parse ref_genome_id " + ref_genome_id)
            sys.exit(1)
        ref_genomes_by_id[m.group(1)] = rgds
    
    # Ref genome Variables
    REF_GENOME_VARS = OrderedDict([("value", "Property or Attribute"), ("valueIRI", "http://purl.obolibrary.org/obo/NCIT_C20189")])

    for acc in acc_d:
        gene_entity = ccmm.agr.genes.get_gene_json(cache, acc, args.bgi_gff3_disease_path, args.ortholog_file)
        ref_genome = ref_genomes_by_id[acc]
        ref_genome.set("isAbout", [gene_entity])
    

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(agr_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()



