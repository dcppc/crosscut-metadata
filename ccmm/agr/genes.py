#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
import ccmm.dats.util as util
from collections import OrderedDict
import pandas as pd
import csv
import json
import logging
import os
import re
import sys


# List of SOIds
SOID = {
    "SO:0000336": "Pseudogene",
    "SO:0000374": "Ribozyme",
    "SO:0000704": "Gene",
    "SO:0001217": "Protein Coding Gene",
    "SO:0001263": "Non-coding RNA Gene",
    "SO:0001265": "miRNA Gene",    
    "SO:0001266": "scRNA Gene", 
    "SO:0001267": "snoRNA Gene", 
    "SO:0001268": "snRNA Gene", 
    "SO:0001269": "SRP RNA Gene", 
    "SO:0001272": "tRNA Gene",
    "SO:0001500": "Phenotypic Marker",
    "SO:0001637": "rRNAGene",
    "SO:0001639": "RNase P RNA Gene",    
    "SO:0001640": "RNase MRP RNA Gene",
    "SO:0001641": "lincRNA Gene",
    "SO:0001643": "Telomerase RNA Gene",
    "SO:0001841": "Polymorphic Pseudogene",  
    "SO:0001877": "Long Non-coding RNA",
    "SO:0001904": "Antisense Transcript",  
    "SO:0002132": "Sense Overlap lncRNA",
    "SO:0002184": "Sense Intronic lncRNA gene",
    "SO:0002185": "Bidirectional Promoter lncRNA",
    "SO:3000000": "Gene Segment"
    }

# List of evidence code IDs
EVID = {
    "TAS": "ECO_0000304",
    "DOA": "ECO",
    "IAGP": "ECO_0005613",
    "IDA": "ECO_0000314",
    "IEP": "ECO_0000270",
    "IGI": "ECO_0000316",
    "IMP": "ECO_0000315"
}

# List of relation IDs
RELID = {
    "is_implicated_in": "ECO_0000304",
    "is_model_of": "ECO",
    "is_marker_for": "ECO_0005613"
}

def search_dict(key, value, list_of_dictionaries):
    return [element for element in list_of_dictionaries if element[key] == value]

def read_bgi(cache, mod, bgi_gff3_disease_path):
    
    features = []
    feature = {}
    
    file = bgi_gff3_disease_path + "/" + mod + "_BGI.json"
    f = open(file)
    x = json.load(f)
    f.close()
    records = x["data"]
    
    for entry in records:
        # required gene attributes per BGI
        primaryId, soTermId, symbol, taxonId = entry["primaryId"], entry["soTermId"], entry["symbol"], entry["taxonId"]
       
        # other gene attributes
        crossRefIds, geneSynopsis, assembly, chr, start, end, strand = "NA", "NA", "NA", "NA", "NA", "NA", "NA"
         
               
        if 'crossReferenceIds' in entry.keys():
            crossRefIds = entry["crossReferenceIds"]
        
        if 'geneSynopsis' in entry.keys():
            geneSynopsis = entry["geneSynopsis"]
            
        #logging.info("genomeLoc: " + genomeLoc[0]['assembly'])    
            
        if 'genomeLocations' in entry.keys():
            genomeLoc = entry["genomeLocations"]
            assembly = genomeLoc[0]['assembly']
            chr = genomeLoc[0]['chromosome']
            if 'startPosition' in genomeLoc[0].keys():
                start = genomeLoc[0]['startPosition']
            if 'endPosition' in genomeLoc[0].keys():
                end = genomeLoc[0]['endPosition']
            if 'strand' in genomeLoc[0].keys():
                strand = genomeLoc[0]['strand']
        
        if '10090' in taxonId:
            taxon = util.get_taxon_mouse(cache)
        elif '10116' in taxonId:
            taxon = util.get_taxon_rat(cache)
        else:
            logging.fatal("encountered taxonomy other than Mouse (10090) or Rat (10116) - " + taxonId)
            sys.exit(1)
        
        feature = {
            'descr': geneSynopsis,
            'primaryId': primaryId,
            'alt_ids': crossRefIds,
            'assembly': assembly,
            'chr': chr,
            'start': start,
            'end': end,
            'strand': strand,
            'soid': soTermId,
            'taxon': taxonId
        }
        features.append(feature)
        
    return features

def read_disease(cache, mod, bgi_gff3_disease_path):
    
    diseases = []
    disease = {}
    
    file = bgi_gff3_disease_path + "/" + mod + "_disease.json"
    f = open(file)
    x = json.load(f)
    f.close()
    records = x["data"]
    
    for entry in records:
        # required disease attributes
        object_id, do_id, data_provider, date_ass, obj_relation, evidence = \
        entry["objectId"], entry["DOid"], entry["dataProvider"], entry["dateAssigned"], entry["objectRelation"], entry["evidence"]
        
        pubmed_id =""
        # other disease attributes
        if 'pubMedId' in entry["evidence"]["publication"].keys():
            pubmed_id = entry["evidence"]["publication"]["pubMedId"] 
            #logging.info("pub: " + pubmed_id)
        
        disease = {
            'object_id': object_id,
            'do_id': do_id,
            'data_provider': data_provider,
            'date_ass': date_ass,
            'association_type': obj_relation["associationType"],
            'evidence_codes': evidence["evidenceCodes"],
            'pubmed_id':  pubmed_id 
        }
        diseases.append(disease)

    return diseases


def read_orthology(ortholog_file):
    
    orthologs = []
    ortholog = {}
    
    orth_list = pd.read_csv(ortholog_file, sep='\t', header=14, dtype='str')
    # Process the entries in the file
    
    for row in orth_list.itertuples():
        #logging.info("orth: " + str(row)) 
        ortho_gene_id, ortho_gene_symbol, ortho_taxon, mod_gene_id, mod_taxon = row[1], row[2], row[3], row[5], row[7]
        ortholog = {
            'ortho_gene_id': ortho_gene_id,
            'ortho_gene_symbol': ortho_gene_symbol,
            'ortho_taxon': ortho_taxon,
            'mod_gene_id': mod_gene_id,
            'mod_taxon': mod_taxon
            }
        orthologs.append(ortholog)
    
    return orthologs
        



# Generate DATS JSON for a single gene
def get_gene_json(cache, mod, bgi_gff3_disease_path, orthologs):
    
    # read gene features form BGI file
    features = read_bgi(cache, mod, bgi_gff3_disease_path)
    
    # read disease from disease JSON file
    diseases = read_disease(cache, mod, bgi_gff3_disease_path)
    
    # TODO - read gene features from GFF3 file
    
    
    genes = []
    
    for f in features:
        genomeLocation = DatsObj("GenomeLocation", [
            ("assembly", f['assembly']),
            ("chromosome", f['chr']),
            ("startPosition", f['start']),
            ("endPosition", f['end']),
            ("strand", f['strand'])
            ])

        types = [OrderedDict([
            ("value", SOID[f['soid']]),("valueIRI", "http://purl.obolibrary.org/obo/SO_" + f['soid'][3:])
            ])]
        
        alternate_ids = []
        if f['alt_ids'] != "NA":
            alt_ids_list = []
            for i in f['alt_ids']:
                source, id = i.split(':')
                alt_id = [ util.get_alt_id(id, source) ]   
                alternate_ids.append(alt_id)   
        
        
        #encode disease
        disease_list = []
        
        gene_diseases = search_dict('object_id', f['primaryId'], diseases)  
        
        if len(gene_diseases) > 0:
            
            do_ids = [d['do_id'] for d in gene_diseases] 
            uniq_do_ids = list(set(do_ids))
            
            #for g in gene_diseases:  
            for d in uniq_do_ids:
                disease_id = OrderedDict([
                    ("identifier",  d),
                    ("identifierSource", "Disease Ontology")])
                
                select_diseases = search_dict('do_id', d, gene_diseases)
                
                relation = OrderedDict([("value", select_diseases[0]['association_type'])])
                
                # account for multiple evidence codes per disease id
                evd_ids = []
                evd_ids_list = [d['evidence_codes'] for d in select_diseases]
                for i in evd_ids_list[0]:
                    evd_id = OrderedDict([("value", i), ("valueIRI", "http://purl.obolibrary.org/obo/" + EVID[i])])                
                    evd_ids.append(evd_id)
                     
               # account for multiple publications per disease id
                pub_ids = []
                pub_ids_list = [d['pubmed_id'] for d in select_diseases]
                for i in pub_ids_list:
                    pub_id = OrderedDict([("identifier",  i)])                
                    pub_ids.append(pub_id)
                
                related_entity_id = OrderedDict([
                    ("object", disease_id),
                    ("relation", relation),
                    ("relationEvidence", evd_ids),
                    ("publications", pub_ids)
                    ]) 
                disease_list.append(related_entity_id)
            
          
        #encode ortholog
        ortholog_list = []
        
        gene_orthologs = search_dict('mod_gene_id', f['primaryId'], orthologs)  

        if len(gene_orthologs) > 0:
            for o in gene_orthologs:  
                mol_entity_ortholog = DatsObj("MolecularEntity", [
                    ("identifier", DatsObj("Identifier", [("identifier", o['ortho_gene_id'])])),
                    ("name", o['ortho_gene_id']),
                    ("description", "Ortholog"),
                    ("taxonomy", [ o['ortho_taxon'] ]),
                    ("alternateIdentifiers", util.get_alt_id(o['ortho_gene_symbol'], "Gene Symbol")),
                ]) 
                
                related_entity_id = OrderedDict([
                    ("object", mol_entity_ortholog)
                    ]) 
                ortholog_list.append(related_entity_id)
        
        related_entities = disease_list + ortholog_list
        
        gene = DatsObj("MolecularEntity", [
                ("identifier", DatsObj("Identifier", [("identifier", f['primaryId'])])),
                ("name", f['primaryId']),
                ("description", f['descr']),
                ("types", types),
                ("taxonomy", [ f['taxon'] ]),
                ("genomeLocation", genomeLocation),
                ("alternateIdentifiers", alternate_ids),
                ("relatedEntities", related_entities )
                ])
        genes.append(gene)

    return genes
