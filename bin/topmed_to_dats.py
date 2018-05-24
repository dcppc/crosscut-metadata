#!/usr/bin/env python3

# Create DATS JSON description of TOPMed public data.

import argparse
from ccmm.dats.datsobj import DATSEncoder
import ccmm.topmed.wgs_datasets
import ccmm.topmed.public_metadata
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET

# expected attribute values for the <stat> element
STAT_ATTRIBS = {
    "n": True,
    "nulls": True,
    "mean_count": True,
    "median_count": True,
    "min_count": True,
    "max_count": True
}

# expected tag values for <variable>
VARIABLE_TAGS = {
    "name": True,
    "description": True,
    "type": True
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
def parse_var_report_stats(et):
    stats = { "values": None }
    cv_values = []
    for child in et:
        print("stats child=" + str(child))
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
            value = { "code": child.attrib['code'], "count": child.attrib['count'] }
            cv_values.append(value)
        else:
            logging.fatal("unexpected child.tag = " + child.tag + " under <stats> element")
            sys.exit(1)

    if len(cv_values) > 0:
        stats['values'] = cv_values

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

# read dbGaP XML data dict file
def read_xml_data_dict(xml_file):
    logging.info("reading " + xml_file)
    subj_dd_tree = ET.parse(xml_file)
    subj_root = subj_dd_tree.getroot()
    if subj_root.tag != 'data_table':
        logging.fatal("unexpected root element (" + subj_root.tag + ") in " + xml_file)
        sys.exit(1)

    study_id = subj_root.attrib['study_id']
    date_created = subj_root.attrib['date_created']
    data_dict_descr = None
    vars = []

    # iterate over variables
    for child in subj_root:
        if child.tag == "description":
            data_dict_descr = child.text
        # each variable has name, description, type
        elif child.tag == "variable":
            var = { "id": child.attrib['id'], "type": None }
            vars.append(var)
            # for type = "encoded value"
            cv_values = []

            for gchild in child:
                if gchild.tag == "value":
                    code = gchild.attrib['code']
                    value = gchild.text
                    cv_values.append({ 'code': code, 'value': value })
                elif gchild.tag == "total":
                    print("parsing var report <total> for " + child.attrib['id'])
                    var['total'] = parse_var_report_total(gchild)
                elif gchild.tag in VARIABLE_TAGS:
                    var[gchild.tag] = gchild.text
                else:
                    logging.fatal("unexpected child tag = " + gchild.tag)
                    sys.exit(1)

            if var['type'] == "encoded value":
                var['values'] = cv_values

        else:
            logging.fatal("unexpected child tag = " + child.tag)
            sys.exit(1)

    print("study_id=" + study_id)
    print("data_dict_descr=" + data_dict_descr)
    print("date_created=" + date_created)
    print("variables=")
    for var in vars:
        print("  " + str(var))

def read_xml_var_report():
    pass

# ------------------------------------------------------
# main()
# ------------------------------------------------------

def main():

    # input
    parser = argparse.ArgumentParser(description='Create DATS JSON for TOPMed public metadata.')
    parser.add_argument('--output_file', default='.', help ='Output file path for the DATS JSON file containing the top-level DATS Dataset.')
    parser.add_argument('--dbgap_public_xml_path', required=True, help ='Path to directory that contains public dbGaP metadata files e.g., *.data_dict.xml and *.var_report.xml')
    parser.add_argument('--dbgap_protected_metadata_path', required=False, help ='Path to directory that contains access-controlled dbGaP tab-delimited metadata files.')
    args = parser.parse_args()

    # logging
    logging.basicConfig(level=logging.INFO)

    # create top-level dataset
    topmed_dataset = ccmm.topmed.wgs_datasets.get_dataset_json()

    # if not processing protected metadata then generate representative DATS JSON using only the public metadata
    pub_xp = args.dbgap_public_xml_path
    priv_mp = args.dbgap_protected_metadata_path

    if priv_mp is None:
        study_files = ccmm.topmed.public_metadata.find_metadata_files(pub_xp)
        n_studies = len(study_files)
        logging.info("found metadata file(s) for " + str(n_studies) + " study/studies in " + pub_xp)

        # process one study at a time
        for study in study_files:
            sd = study_files[study]
            logging.info("processing metadata for study " + study)
            
            # ----------------------------
            # Subject
            # ----------------------------

            # ----------------------------
            # subject data_dict 
            # ----------------------------
            subject_dd = sd['Subject']['data_dict']
            read_xml_data_dict(subject_dd['path'])

            # ----------------------------
            # subject var_report
            # ----------------------------
            # format of var_report is similar in structure to the data_dict
            subject_vr = sd['Subject']['var_report']
            read_xml_data_dict(subject_vr['path'])
            sys.exit(1)

            # Subject_Attributes

            # Sample 

            # Sample_Attributes
            

    else:
        logging.fatal("processing access-controlled dbGaP metadata is not yet supported")
        sys.exit(1)

    # write Dataset to DATS JSON file
    with open(args.output_file, mode="w") as jf:
        jf.write(json.dumps(topmed_dataset, indent=2, cls=DATSEncoder))

if __name__ == '__main__':
    main()
