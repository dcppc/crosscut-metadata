#!/usr/bin/env python3

import logging
import os 
import re
import sys
import xml.etree.ElementTree as ET

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

# expected attribute values for the <stat> element
STAT_ATTRIBS = {
    "n": True,
    "nulls": True,

    "mean_count": True,
    "median_count": True,
    "min_count": True,
    "max_count": True,

    "mean": True,
    "median": True,
    "min": True,
    "max": True,
    "sd": True
}

# expected attribute values for <variable>
VARIABLE_ATTRIBS = {
    "var_name": True,
    "calculated_type": True,
    "reported_type": True
}

# expected tag values for <variable>
VARIABLE_TAGS = {
    "name": True,
    "description": True,
    "type": True,
    "comment": True,
    "coll_interval": True,
    "unit": True,
    "logical_min": True,
    "logical_max": True
}

# parse <stats> section of variable report e.g.,
#
# <stats>
#   <stat n="80" nulls="0"/>
# </stats>
#
# or
#
# <stats>
#   <stat n="80" nulls="0" mean_count="80" median_count="80" min_count="80" max_count="80"/>
#   <enum code="1" count="80">Disease-Specific (COPD and Smoking, RD) (DS-CS-RD)</enum>
#  </stats>
#
# <stats> elements can also include <example>s
#
def parse_var_report_stats(et):
    stats = { "values": None }
    cv_values = []
    examples = []
    for child in et:
        if child.tag == "stat":
            for att in child.attrib:
                av = child.attrib[att]
                if att in STAT_ATTRIBS:
                    stats[att] = av
                else:
                    logging.fatal("unexpected attribute in <stat> element: " + att)
                    sys.exit(1)
            pass
        elif child.tag == "enum":
            value = { "count": child.attrib['count'], "name": child.text }
            # not all enum elements have a code
            if 'code' in child.attrib:
                value['code'] = child.attrib['code']
            cv_values.append(value)
        # example value with count
        elif child.tag == "example":
            ex = { "count": child.attrib['count'], "name": child.text }
            examples.append(ex)
        else:
            logging.fatal("unexpected child.tag = " + child.tag + " under <stats> element")
            sys.exit(1)

    if len(cv_values) > 0:
        stats['values'] = cv_values
    if len(examples) > 0:
        stats['examples'] = examples

    return stats

# parse <total> section of variable report e.g., 
#
# <total>
#   <subject_profile>
#    <case_control>
#     <case>80</case>
#    </case_control>
#    <sex>
#     <male>23</male>
#     <female>57</female>
#    </sex>
#   </subject_profile>
#  <stats>
#    <stat n="80" nulls="0"/>
#  </stats>
# </total>
#
def parse_var_report_total(et):
    res = {}
    for child in et:
        if child.tag == "subject_profile":
            # TODO
            pass
        elif child.tag == "stats":
            res['stats'] = parse_var_report_stats(child)
        else:
            logging.fatal("unexpected child.tag = " + child.tag + " under var_report <total>")
    return res

# read dbGaP XML data_dict or var_report XML file
def read_dbgap_data_dict_or_var_report_xml(xml_file):
    logging.info("reading " + xml_file)
    subj_dd_tree = ET.parse(xml_file)
    subj_root = subj_dd_tree.getroot()
    if subj_root.tag != 'data_table':
        logging.fatal("unexpected root element (" + subj_root.tag + ") in " + xml_file)
        sys.exit(1)

    study_id = subj_root.attrib['study_id']
    date_created = subj_root.attrib['date_created']
    data_dict_descr = None
    has_coll = None
    vars = []

    # iterate over variables
    for child in subj_root:
        if child.tag == "description":
            data_dict_descr = child.text
        # each variable has name, description, type
        elif child.tag == "variable":
            var = { "id": child.attrib['id'], "type": None }
            for vt in VARIABLE_ATTRIBS:
                if vt in child.attrib:
                    var[vt] = child.attrib[vt]

            vars.append(var)
            # for type = "encoded value"
            cv_values = []

            for gchild in child:
                if gchild.tag == "value":
                    code = gchild.attrib['code']
                    value = gchild.text
                    cv_values.append({ 'code': code, 'value': value })
                elif gchild.tag == "total":
                    var['total'] = parse_var_report_total(gchild)
                elif gchild.tag in VARIABLE_TAGS:
                    var[gchild.tag] = gchild.text
                else:
                    logging.fatal("unexpected child tag = " + gchild.tag)
                    sys.exit(1)

            if var['type'] == "encoded value":
                var['values'] = cv_values

        # TODO - check documentation for meaning of this dataset-level value
        elif child.tag == "has_coll":
            has_coll = child.text
        else:
            logging.fatal("unexpected child tag = " + child.tag)
            sys.exit(1)

    xml_info = {
        "study_id": study_id,
        "data_dict_descr": data_dict_descr,
        "date_created": date_created,
        "has_coll": has_coll,
        "vars": vars
        }

    return xml_info

# nested dicts not natively supported in Python3?
def make_multilevel_dict(items, keys):
    md = {}
    for item in items:
        d = md
        for k in keys[:-1]:
            kv = item[k]
            if kv not in d:
                d[kv] = {}
            d = d[kv]
        d[item[keys[-1]]] = item

    return md

# Find all dbGaP XML metadata files in a given directory.
def get_study_metadata_files(dir):
    filenames = os.listdir(dir)
    files = []

    for f in filenames:
        # ignore anything that doesn't start with a study id
        if re.match(r'^phs\d+\.', f):
            # list of possible file types (Subject, Sample, etc.) may vary from study to study
            m = re.match(r'^(phs\d+\.v\d+)\.((\S+)_(Subject|Sample|Sample_Attributes|Subject_Phenotypes)).(data_dict|var_report)\.xml$', f)
            if m is None:
                logging.fatal("unable to parse file type and study name from dbGaP file " + f)
                sys.exit(1)

            file = {
                "name": f, 
                "path": os.path.join(dir, f), 
                "study_id": m.group(1), 
                "study_name": m.group(3), 
                "metadata_type": m.group(4), 
                "file_type": m.group(5) 
                }
            files.append(file)

    return make_multilevel_dict(files, ["study_id", "metadata_type", "file_type"])

# Read all dbGaP XML metadata files in a given directory and read and parse their contents.
def read_study_metadata(dir):
    study_md = {}
    study_files = get_study_metadata_files(dir)
    n_studies = len(study_files)
    logging.info("found metadata file(s) for " + str(n_studies) + " study/studies in " + dir)

    # process one study at a time
    for study in study_files:
        logging.info("processing metadata for study " + study)
        sd = study_files[study]
        md = { 'files': sd }
        study_md[study] = md
        
        # each study should have a data_dict and var_report for each of the following:
        for datatype in ('Subject', 'Sample', 'Sample_Attributes', 'Subject_Phenotypes'):
            md[datatype] = {}

            for filetype in ('data_dict', 'var_report'):
                file_path = sd[datatype][filetype]['path']
                xml_data = read_dbgap_data_dict_or_var_report_xml(file_path)
                md[datatype][filetype] = { 'file': file_path, 'data': xml_data }

    return study_md
