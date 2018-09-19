#!/usr/bin/env python3

import logging
import os 
import re
import sys
import xml.etree.ElementTree as ET
from ccmm.dats.datsobj import DatsObj
import ccmm.util as util

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
    'GRU',
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

        else:
            logging.debug("ignoring metadata file " + f)

    return util.make_multilevel_dict(files, ["study_id", "study_name", "metadata_type", "file_type"])

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
    # heuristic: studies with no data_dict files will be treated as sub-studies
    n_not_substudy = 0
    substudy_names = {}
    for study_id in study_files:
        sd = study_files[study_id]
        if util.multilevel_dict_key_exists(sd, 'data_dict'):
            n_not_substudy += 1
        else:
            sd['_is_substudy'] = 1
            # substudies should have only a single study name
            ss_names = [x for x in sd.keys() if not x.startswith('_')]
            n_ss_names = len(ss_names)
            if n_ss_names != 1:
                logging.fatal("Sub-study " + study_id + " maps to " + str(n_ss_names) + " substudy names: " + ",".join(ss_names))
                sys.exit(1)
            substudy_names[ss_names[0]] = True
            logging.info(study_id + " | " + ss_names[0] + " is a sub-study")

    if n_not_substudy != 1:
        logging.fatal("Failed to identify main study - found " + str(n_not_substudy) + " main studies")
        sys.exit(1)

    # process one study at a time
    for study_id in study_files:

        # find file data for parent study
        sd = None

        study = study_files[study_id]
        if '_is_substudy' in study:
            continue

        for study_name in study:
            if study_name.startswith('_'):
                continue
            if study_name in substudy_names:
                logging.info("skipping sub-study " + study_name)
                continue
            if sd is not None:
                logging.fatal("found multiple top-level studies under " + study_id)
                sys.exit(1)
            sd = study[study_name]

        if sd is None:
            logging.fatal("failed to find any top-level study under " + study_id)
            sys.exit(1)

        logging.info("processing metadata for study " + study_id + " | " + study_name)

        md = { 'files': sd }
        study_md[study_id] = md
        
        # each study may have a data_dict and var_report for each of the following:
        for datatype in ('Subject', 'Sample', 'Sample_Attributes', 'Subject_Phenotypes'):
            for filetype in ('data_dict', 'var_report'):

                # Subject_Phenotypes is not always present
                if datatype not in sd:
                    logging.info("no XML found for " + datatype + "." + filetype)
                    continue

                if datatype not in md:
                    md[datatype] = {}

                file_path = sd[datatype][filetype]['path']
                logging.debug("parsing metadata file " + file_path)

                xml_data = read_dbgap_data_dict_or_var_report_xml(file_path)
                md[datatype][filetype] = { 'file': file_path, 'data': xml_data }

    return study_md

# Record study variables as dimensions of the study/Dataset.
def add_study_vars(study, study_md):
    
    # maps dbGaP variable id to DATS dimension and variable report
    id_to_var = {}
    # maps variable type (e.g., Subject, Sample_Attributes), name and consent group to DATS dimension and variable report
    type_name_cg_to_var = {}

    for var_type in ('Subject', 'Subject_Phenotypes', 'Sample', 'Sample_Attributes'):
        if var_type in study_md:
            var_data = study_md[var_type]['data_dict']['data']
            vars = var_data['vars']
            vdict = {}
            type_name_cg_to_var[var_type] = vdict

            for var in vars:
                var_name = var['name']
                id = DatsObj("Identifier", [
                    ("identifier",  var['id']),
                    ("identifierSource", "dbGaP")])
        
                dim = DatsObj("Dimension", [
                    ("identifier", id),
                    ("name", DatsObj("Annotation", [("value", var_name)])),
                    ("description", var['description'])
                    # TODO: include stats
                ])  

                study.getProperty("dimensions").append(dim)
            
                # track dbGaP variable Dimension and variable report by dbGaP id
                if var['id'] in id_to_var:
                    logging.fatal("duplicate definition found for dbGaP variable " + var_name + " with accession=" + var['id'])
                    sys.exit(1)

                t ={"dim": dim, "var": var}
                id_to_var[var['id']] = t
                
                # track by name and consent group
                m = re.match(r'^(.*)(\.(c\d+))$', var['id'])
        
                if m is None:
                    suffix = ""
                else:
                    suffix = "." + m.group(3)

                key = "".join([var_name, suffix])
                if key in vdict:
                    logging.fatal("duplicate definition found for dbGaP variable " + key + " in " + var_type + " file")
                vdict[key] = t

    return { "id_to_var": id_to_var, "type_name_cg_to_var": type_name_cg_to_var }
