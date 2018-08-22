#!/usr/bin/env python3

import logging
import os 
import re
import sys
import xml.etree.ElementTree as ET

# ------------------------------------------------------
# Global variables
# ------------------------------------------------------

# list of permitted file types
FILE_TYPES = [
    'Subject',
    'Sample',
    'Sample_Attributes',
    'Subject_Phenotypes',
    'Subject_Images'
]

FILE_TYPES_RE = '|'.join(FILE_TYPES)

# list of permitted metadata types
METADATA_TYPES = [
    'data_dict',
    'var_report',
    'MULTI',
    # TODO - handle use codes separately and ensure all combinations are handled:
    'DS-CS-RD',
    'DS-LD',
    'HMB',
    'DS-LD-RD',
    ''
]

METADATA_TYPES_RE = '|'.join(METADATA_TYPES)
 
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
    "sd": True,
    "distinct_vals": True
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

# parse <total>, <cases>, or <controls> subsection of variable report e.g., 
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
def parse_var_report_subsection(et, subsection):
    res = {}
    for child in et:
        if child.tag == "subject_profile":
            # TODO
            pass
        elif child.tag == "stats":
            res['stats'] = parse_var_report_stats(child)
        else:
            logging.fatal("unexpected child.tag = " + child.tag + " under var_report <" + subsection + ">")
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
            # for "values" where type is not "encoded value"
            cv_list = []

            for gchild in child:
                if gchild.tag == "value":
                    if var['type'] == "encoded value":
                        code = gchild.attrib['code']
                        value = gchild.text
                        cv_values.append({ 'code': code, 'value': value })
                    else:
                        value = gchild.text
                        cv_list.append(value)
                elif gchild.tag == "total":
                    var['total'] = parse_var_report_subsection(gchild, "total")
                elif gchild.tag == "cases":
                    var['cases'] = parse_var_report_subsection(gchild, "cases")
                elif gchild.tag == "controls":
                    var['controls'] = parse_var_report_subsection(gchild, "controls")
                elif gchild.tag in VARIABLE_TAGS:
                    var[gchild.tag] = gchild.text
                else:
                    logging.fatal("unexpected child tag under variable " + child.attrib['id']  + " = " + gchild.tag)
                    sys.exit(1)

            if var['type'] == "encoded value":
                var['values'] = cv_values
            if len(cv_list) > 0:
                var['values'] = cv_list

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

# Find all dbGaP XML or .txt metadata files in a given directory.
def get_study_metadata_files(dir, suffix):
    filenames = os.listdir(dir)
    files = []

    for f in filenames:
        # ignore anything that doesn't start with a study id and end with suffix
        if re.match(r'^phs\d+\..*\.' + suffix + '$', f):
            # list of possible file types (Subject, Sample, etc.) may vary from study to study
            # phsXXXXXX - study accession
            # phtXXXXXX - phenotype trait table accession
            # v = data version, p = participant set version, c = consent group version
            m = re.match(r'^(phs\d+\.v\d+)\.(pht\d+\.v\d+)(\.p\d+)?\.(\S+)_(' + FILE_TYPES_RE + ').(' + METADATA_TYPES_RE + ')\.' + suffix + '$', f)
            if m is None:
                logging.fatal("unable to parse file type and study name from dbGaP file " + f)
                sys.exit(1)

            file = {
                "name": f, 
                "path": os.path.join(dir, f), 
                "study_id": m.group(1), 
                "phenotype_id": m.group(2), 
                "participant_set_version": m.group(3),
                "study_name": m.group(4), 
                "metadata_type": m.group(5), 
                "file_type": m.group(6) 
                }
            files.append(file)

    return make_multilevel_dict(files, ["study_id", "metadata_type", "file_type"])

# Read all dbGaP XML metadata files in a given directory and read and parse their contents.
def read_study_metadata(dir):
    study_md = {}
    study_files = get_study_metadata_files(dir, "xml")
    n_studies = len(study_files)
    study_str = 'study'
    if n_studies > 1:
        study_str = 'studies'
    logging.info("found metadata file(s) for " + str(n_studies) + " " + study_str + " in " + dir)

    # identify sub-studies
    # and index their var_report files by phenotypic trait table accession
    ss_var_reports = {}
    n_not_substudy = 0
    for study in study_files:
        file_types_d = {}
        sd = study_files[study]
        for datatype in sd:
            dt_files = sd[datatype]
            for filetype in dt_files:
                file = sd[datatype][filetype]
                file_types_d[filetype] = True
                if filetype == 'var_report':
                    ss_var_reports[file['phenotype_id']] = file            

        # if only var_report files are present it will be treated as a sub-study
        file_types = [x for x in file_types_d.keys()]
        n_file_types = len(file_types)
        if (n_file_types == 1) and (file_types[0] == 'var_report'):
            sd['is_substudy'] = True
        else:
            sd['is_substudy'] = False
            n_not_substudy += 1

    if n_not_substudy != 1:
        logging.fatal("Failed to identify main study - found " + str(n_not_substudy) + " main studies")
        sys.exit(1)

    # process one study at a time
    for study in study_files:
        if study_files[study]['is_substudy']:
            logging.info("skipping sub-study " + study)
            continue
        logging.info("processing metadata for study " + study)
        sd = study_files[study]
        md = { 'files': sd }
        study_md[study] = md
        
        # each study should have a data_dict and var_report for each of the following:
        for datatype in ('Subject', 'Sample', 'Sample_Attributes', 'Subject_Phenotypes'):
            for filetype in ('data_dict', 'var_report'):

                # Subject_Phenotypes is not always present
                if datatype not in sd:
                    logging.info("no XML found for " + datatype + "." + filetype)
                    continue

                # skip any data_dict files whose corresponding var_report is from a sub-study
                if filetype == 'data_dict':
                    var_report_study = ss_var_reports[sd[datatype][filetype]['phenotype_id']]['study_id']
                    if var_report_study != study:
                        logging.info("skipping data_dict for sub-study " + var_report_study)
                        break

                if datatype not in md:
                    md[datatype] = {}

                file_path = sd[datatype][filetype]['path']

                xml_data = read_dbgap_data_dict_or_var_report_xml(file_path)
                md[datatype][filetype] = { 'file': file_path, 'data': xml_data }

    return study_md
