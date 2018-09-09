#!/usr/bin/env python3

from collections import OrderedDict
import json
import logging
import re
import sys
import uuid

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

# Location of JSON-LD contexts
# TODO - these links are stable but not versioned. Replace with stable versioned link prefix when available.
#JSON_LD_SDO_CONTEXT_URI_PREFIX = 'https://w3id.org/dats/context/sdo/'
#JSON_LD_OBO_FOUNDRY_CONTEXT_URI_PREFIX = 'https://w3id.org/dats/context/obo/'

# use direct links to avoid redirects (results in 3X improvement in rdflib parse speed)
JSON_LD_SDO_CONTEXT_URI_PREFIX = 'https://datatagsuite.github.io/context/sdo/'
JSON_LD_OBO_FOUNDRY_CONTEXT_URI_PREFIX = 'https://datatagsuite.github.io/context/obo/'

# use local context files (further 10X improvement in rdflib parse speed)
#JSON_LD_SDO_CONTEXT_URI_PREFIX = './context/sdo/'
#JSON_LD_OBO_FOUNDRY_CONTEXT_URI_PREFIX = './context/obo/'

# debug flag - should remove all id references from the resulting instance when True
DEBUG_NO_ID_REFS = False

# All known DATS object types
# from schema dir of https://github.com/datatagsuite/schema.git:
# egrep '@type' *.json | perl -ne 'if (/^(\S+):.*\"enum\":\s*\[\s*\"([^\"]+)\"/) { print "\"$2\": { \"name\": \"$2\", \"schema\": \"$1\", \"has_context\": False },\n"; }' | sort | uniq
DATS_TYPES = {
    "Access": { "name": "Access", "schema": "access_schema.json", "has_context": True },
    "Activity": { "name": "Activity", "schema": "activity_schema.json", "has_context": True },
    "AlternateIdentifier": { "name": "AlternateIdentifier", "schema": "alternate_identifier_info_schema.json", "has_context": True },
    "AnatomicalPart": { "name": "AnatomicalPart", "schema": "anatomical_part_schema.json", "has_context": True },
    "Annotation": { "name": "Annotation", "schema": "annotation_schema.json", "has_context": True },
    "BiologicalEntity": { "name": "BiologicalEntity", "schema": "biological_entity_schema.json", "has_context": True },
    "CategoryValuesPair": { "name": "CategoryValuesPair", "schema": "category_values_pair_schema.json", "has_context": True },
    "ConsentInfo": { "name": "ConsentInfo", "schema": "consent_info_schema.json", "has_context": True },
    "DataAcquisition": { "name": "DataAcquisition", "schema": "data_acquisition_schema.json", "has_context": True },
    "DataAnalysis": { "name": "DataAnalysis", "schema": "data_analysis_schema.json", "has_context": True },
    "DataRepository": { "name": "DataRepository", "schema": "data_repository_schema.json", "has_context": True },
    "DataStandard": { "name": "DataStandard", "schema": "data_standard_schema.json", "has_context": True },
    "DataType": { "name": "DataType", "schema": "data_type_schema.json", "has_context": True },
    "Dataset": { "name": "Dataset", "schema": "dataset_schema.json", "has_context": True },
    "DatasetDistribution": { "name": "DatasetDistribution", "schema": "dataset_distribution_schema.json", "has_context": True },
    "Date": { "name": "Date", "schema": "date_info_schema.json", "has_context": True },
    "Dimension": { "name": "Dimension", "schema": "dimension_schema.json", "has_context": True },
    "Disease": { "name": "Disease", "schema": "disease_schema.json", "has_context": True },
    "Grant": { "name": "Grant", "schema": "grant_schema.json", "has_context": True },
    "Identifier": { "name": "Identifier", "schema": "identifier_info_schema.json", "has_context": True },
    "Instrument": { "name": "Instrument", "schema": "instrument_schema.json", "has_context": True },
    "License": { "name": "License", "schema": "license_schema.json", "has_context": False },
    "Material": { "name": "Material", "schema": "material_schema.json", "has_context": True },
    "MolecularEntity": { "name": "MolecularEntity", "schema": "molecular_entity_schema.json", "has_context": True },
    "Organization": { "name": "Organization", "schema": "organization_schema.json", "has_context": True },
    "Person": { "name": "Person", "schema": "person_schema.json", "has_context": True },
    "Place": { "name": "Place", "schema": "place_schema.json", "has_context": True },
    "Provenance": { "name": "Provenance", "schema": "provenance_schema.json", "has_context": True },
    "Publication": { "name": "Publication", "schema": "publication_schema.json", "has_context": True },
    "RelatedIdentifier": { "name": "RelatedIdentifier", "schema": "related_identifier_info_schema.json", "has_context": True },
    "Software": { "name": "Software", "schema": "software_schema.json", "has_context": True },
    "Study": { "name": "Study", "schema": "study_schema.json", "has_context": True },
    "StudyGroup": { "name": "StudyGroup", "schema": "study_group_schema.json", "has_context": True },
    "TaxonomicInformation": { "name": "TaxonomicInformation", "schema": "taxonomic_info_schema.json", "has_context": True },
    "Treatment": { "name": "Treatment", "schema": "treatment_schema.json", "has_context": True }
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
            sdo_context_file = re.sub(r'_schema.json$', '_sdo_context.jsonld', json_ld_file)
            sdo_json_ld_context =  JSON_LD_SDO_CONTEXT_URI_PREFIX + sdo_context_file
            obo_foundry_context_file = re.sub(r'_schema.json$', '_obo_context.jsonld', json_ld_file)
            obo_foundry_ld_context =  JSON_LD_OBO_FOUNDRY_CONTEXT_URI_PREFIX + obo_foundry_context_file 
            dats_atts.append(("@context", [ sdo_json_ld_context, obo_foundry_ld_context ] ))

        # @id
        # use identifier URI if one is specified
        id_uri = None
        for att in atts:
            (key, val) = att
            if key == "identifier" and isinstance(val, DatsObj):
                if val.get("@type") == "Identifier":
                    idval = val.get("identifier")
                    # TODO - this only catches the handful of URI schemes used in the current encodings
                    if re.match(r'^(https?|s3|gs|ftp):', idval):
                        id_uri = idval

        # assign random uuid if no id specified
        if id == "":
            if id_uri is not None:
                id = id_uri
            else:
                id = "http://127.0.0.1/TMPID/" + str(uuid.uuid4())

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

    # return object id in form suitable for use as JSON-LD id reference
    def getIdRef(self):
        return { "@id": self.data["@id"] }

# JSONEncoder for data structures that use DatsObj

class DATSEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, DatsObj):
            return o.data
        else:
            return json.JSONEncoder.default(self, o)
        

# ------------------------------------------------------
# DatsObjCache
# ------------------------------------------------------

class DatsObjCache:
    cache = {}

    def __init__(self):
        pass

    # return the object if it's new, the id reference if it's not
    def get_obj_or_ref(self, obj_key, obj_fn):
        if obj_key in self.cache:
            if DEBUG_NO_ID_REFS:
                return self.cache[obj_key]
            else:
                return self.cache[obj_key].getIdRef()
        new_obj = obj_fn()
        self.cache[obj_key] = new_obj
        return new_obj

    
