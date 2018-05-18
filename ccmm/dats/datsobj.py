#!/usr/bin/env python3

from collections import OrderedDict
import json
import logging
import re

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

# Location of JSON-LD contexts
# TODO - replace with stable versioned link prefix (TBD)
JSON_LD_CONTEXT_URI_PREFIX = 'https://raw.githubusercontent.com/datatagsuite/context/master/sdo/'

# All known DATS object types
# from schema dir of https://github.com/datatagsuite/schema.git:
# egrep '@type' *.json | perl -ne 'if (/^(\S+):.*\"enum\":\s*\[\s*\"([^\"]+)\"/) { print "\"$2\": { \"name\": \"$2\", \"schema\": \"$1\", \"has_context\": False },\n"; }' | sort | uniq
DATS_TYPES = {
    "Access": { "name": "Access", "schema": "access_schema.json", "has_context": False },
    "Activity": { "name": "Activity", "schema": "activity_schema.json", "has_context": False },
    "AlternateIdentifier": { "name": "AlternateIdentifier", "schema": "alternate_identifier_info_schema.json", "has_context": False },
    "AnatomicalPart": { "name": "AnatomicalPart", "schema": "anatomical_part_schema.json", "has_context": False },
    "Annotation": { "name": "Annotation", "schema": "annotation_schema.json", "has_context": False },
    "BiologicalEntity": { "name": "BiologicalEntity", "schema": "biological_entity_schema.json", "has_context": False },
    "CategoryValuesPair": { "name": "CategoryValuesPair", "schema": "category_values_pair_schema.json", "has_context": False },
    "DataAcquisition": { "name": "DataAcquisition", "schema": "data_acquisition_schema.json", "has_context": False },
    "DataAnalysis": { "name": "DataAnalysis", "schema": "data_analysis_schema.json", "has_context": False },
    "DataRepository": { "name": "DataRepository", "schema": "data_repository_schema.json", "has_context": True },
    "DataStandard": { "name": "DataStandard", "schema": "data_standard_schema.json", "has_context": True },
    "DataType": { "name": "DataType", "schema": "data_type_schema.json", "has_context": False },
    "Dataset": { "name": "Dataset", "schema": "dataset_schema.json", "has_context": True },
    "DatasetDistribution": { "name": "DatasetDistribution", "schema": "dataset_distribution_schema.json", "has_context": True },
    "Date": { "name": "Date", "schema": "date_info_schema.json", "has_context": False },
    "Dimension": { "name": "Dimension", "schema": "dimension_schema.json", "has_context": False },
    "Disease": { "name": "Disease", "schema": "disease_schema.json", "has_context": False },
    "Grant": { "name": "Grant", "schema": "grant_schema.json", "has_context": True },
    "Identifier": { "name": "Identifier", "schema": "identifier_info_schema.json", "has_context": False },
    "Instrument": { "name": "Instrument", "schema": "instrument_schema.json", "has_context": False },
    "License": { "name": "License", "schema": "license_schema.json", "has_context": False },
    "Material": { "name": "Material", "schema": "material_schema.json", "has_context": True },
    "MolecularEntity": { "name": "MolecularEntity", "schema": "molecular_entity_schema.json", "has_context": False },
    "Organization": { "name": "Organization", "schema": "organization_schema.json", "has_context": True },
    "Person": { "name": "Person", "schema": "person_schema.json", "has_context": True },
    "Place": { "name": "Place", "schema": "place_schema.json", "has_context": False },
    "Provenance": { "name": "Provenance", "schema": "provenance_schema.json", "has_context": False },
    "Publication": { "name": "Publication", "schema": "publication_schema.json", "has_context": True },
    "RelatedIdentifier": { "name": "RelatedIdentifier", "schema": "related_identifier_info_schema.json", "has_context": False },
    "Software": { "name": "Software", "schema": "software_schema.json", "has_context": True },
    "Study": { "name": "Study", "schema": "study_schema.json", "has_context": False },
    "StudyGroup": { "name": "StudyGroup", "schema": "study_group_schema.json", "has_context": False },
    "TaxonomicInformation": { "name": "TaxonomicInformation", "schema": "taxonomic_info_schema.json", "has_context": False },
    "Treatment": { "name": "Treatment", "schema": "treatment_schema.json", "has_context": False }
    }

# ------------------------------------------------------
# DatsObj
# ------------------------------------------------------

class DatsObj:
    data = None

    def __init__(self, dats_type, atts = [], id = ""):
        # check that dats_type is valid
        if dats_type not in DATS_TYPES:
            logging.fatal("Unknown DATS object type '" + dats_type + "'")
            sys.exit(1)
            
        dt = DATS_TYPES[dats_type]

        dats_atts = [("@type", dats_type)]

        # @context
        if dt['has_context']:
            json_ld_file = dt['schema']
            context_file = re.sub(r'_schema.json$', '_context.jsonld', json_ld_file)
            json_ld_context = JSON_LD_CONTEXT_URI_PREFIX + context_file
            dats_atts.append(("@context", json_ld_context))

        # @id
        # TODO - id should be a URI according to dataset_schema.json
        # HACK - workaround for the fact that the Access JSON schema doesn't declare @id
        if dats_type != "Access":
            dats_atts.append(("@id", id))
        dats_atts.extend(atts)
        self.data = OrderedDict(dats_atts)

    def getProperty(self, name):
        return self.data[name]

    def setProperty(self, name, value):
        self.data[name] = value

    def get(self, name):
        return self.getProperty(name)
    
    def set(self, name, value):
        self.setProperty(name, value)

# JSONEncoder for data structures that use DatsObj

class DATSEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, DatsObj):
            return o.data
        else:
            return json.JSONEncoder.default(self, o)
        
