#!/usr/bin/env python3

import csv
import logging
import re
import sys

# ------------------------------------------------------
# Error handling
# ------------------------------------------------------

def fatal_error(err_msg):
    logging.fatal(err_msg)
    sys.exit(1)

def fatal_parse_error(err_msg, file, lnum):
    msg = err_msg + " at line " + str(lnum) + " of " + file
    fatal_error(msg)

# Generic parser for subject/phenotype and sample/attribute metadata files
#
# file_path - path to the file to be read
# column_metadata - list of dicts structured like so:
#   COL_MD = [
#      {'id': 'SAMPID', 'empty_ok': False },
#      {'id': 'SMATSSCR', 'integer_cv': { 0: 'None', 1: 'Mild', 2: 'Moderate', 3: 'Severe' } , 'empty_ok': True },
#      {'id': 'SMCENTER',  'cv': [ 'B1', 'C1', 'D1', 'B1, A1', 'C1, A1', 'D1, A1' ] , 'empty_ok': True }
#   ]
# id_column - name of the primary key columns
#
def read_csv_metadata_file(file_path, column_metadata, id_column):
    # rows indexed by the value in id_column
    rows = {}

    with open(file_path) as fh:
        reader = csv.reader(fh, delimiter='\t')
        lnum = 0
        for line in reader:
            lnum += 1

            # check column headings match expected values
            if lnum == 1:
                cnum = 0
                for col in column_metadata:
                    if line[cnum] != col['id']:
                        fatal_parse_error("Unexpected column header '" + line[cnum] + "' in column " + str(cnum+1) + " ", file_path, lnum)
                    cnum += 1

            # parse column values
            else:
                cnum = 0
                parsed_row = {}

                for col in column_metadata:
                    colname = col['id']
                    colval = line[cnum]
                    parsed_col = { "raw_value": colval }

                    # check for empty value
                    if colval == '':
                        if col['empty_ok']:
                            parsed_col['mapped_value'] = None
                        else:
                            fatal_parse_error("Missing value in column " + str(cnum+1) + "/" + colname + " but empty_ok = False.", file_path, lnum)

                    # check regex if present
                    elif 'regex' in col:
                        regex = col['regex']
                        m = re.match(regex, colval)
                        if m is None:
                            fatal_parse_error("Value in column '" + str(cnum+1) + "' ('" + colval+ "') does not match regex " + str(regex), file_path, lnum)

                    # integer_cv
                    elif 'integer_cv' in col:
                        m = re.match(r'^(\d+)', colval)
                        if m is None:
                            fatal_parse_error("Value in column '" + str(cnum+1) + "' ('" + colval+ "') is not an integer.", file_path, lnum)
                            
                        iv = int(m.group(1))
                        icv = col['integer_cv']
                        if iv not in icv:
                            fatal_parse_error("No mapping defined for integer value " + str(iv) + " in column " + str(cnum+1) + "/" + colname + " ", file_path, lnum)
                        val = icv[iv]
                        parsed_col["mapped_value"] = val

                    # cv
                    elif 'cv' in col:
                        # check that value is one of the allowed values
                        cv = col['cv']

                    if 'mapped_value' not in parsed_col:
                        parsed_col['mapped_value'] = parsed_col['raw_value']

                    cnum += 1
                    parsed_row[colname] = parsed_col

                # set row id
                row_id = parsed_row[id_column]['mapped_value']
                parsed_row['id'] = row_id
#                logging.debug("read row " + str(parsed_row) + " from line " + str(lnum) + " of " + file_path)
                if row_id in rows:
                    fatal_parse_error("Duplicate " + id_column + " '" + rowid + "'", subj_phen_file, lnum)
                rows[row_id] = parsed_row

    return rows
