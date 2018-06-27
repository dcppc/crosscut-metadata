#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
from collections import OrderedDict
import csv
import gzip
import logging
import re
import sys

# Read MGI/MGD HOM_MouseHumanSequence.rpt file.
# 
def read_mgd_mouse_human_seq_file(file_path):
    # index by HomoloGene id then species
    hgene_h = {}
    # mapping from MGI mouse gene id to HomoloGene
    mgi2hgene_h = {}

    fields = None
    n_fields = 0
    
    fh = None
    if re.match(r'.*\.gz$', file_path):
        fh = gzip.open(file_path, 'rt')
    else:
        fh = open(file_path)
    
    if fh is None:
        logging.fatal("failed to open file " + file_path)
        sys.exit(1)
    
    reader = csv.reader(fh, delimiter='\t')
    lnum = 0
    last_line = None

    for line in reader:
        lnum += 1

        # ignore exact duplicate lines (there is one at line 34758)
        if line == last_line:
            continue
        last_line = line

        # header line
        if re.match(r'^HomoloGene ID', line[0]):
            fields = line
            n_fields = len(fields)

        # data line
        else:
            nf = len(line)
            if nf != n_fields:
                logging.fatal("unexpected number of fields (" + str(nv) + ", not " + str(n_fields) + ") at line " + str(lnum) + " of " + file_path)

            d = {}
            for f in range(0, nf):
                if line[f] != "":
                    d[fields[f]] = line[f]

            # index by HomoloGene ID and species
            homologene_id = d['HomoloGene ID']
            species = d['Common Organism Name']
            species = re.sub(r', laboratory', '', species)

            # this particular file should contain only human and mouse genes
            if not re.match(r'^human|mouse$', species):
                logging.fatal("unexpected species at line " + str(lnum) + " of " + file_path)
                sys.exit(1)

            hgene = None
            if homologene_id in hgene_h:
                hgene = hgene_h[homologene_id]
            else:
                hgene = { 'id': homologene_id }
                hgene_h[homologene_id] = hgene

            if species in hgene:
                hgene[species].append(d)
            else:
                hgene[species] = [d]

            # index by MGI id
            if 'Mouse MGI ID' in d:
                id = d['Mouse MGI ID']
                if id in mgi2hgene_h:
                    logging.fatal("duplicate MGI id (" + id + ") at line " + str(lnum) + " of " + file_path)
                    sys.exit(1)
                mgi2hgene_h[id] = hgene

    n_homologenes = len(hgene_h)

    # number of mouse genes with at least one human homolog
    n_homologs = 0
    for mgi_id in mgi2hgene_h:
        hgene = mgi2hgene_h[mgi_id]
        n_human = 0
        n_mouse = 0
        if 'human' in hgene:
            n_human = len(hgene['human'])
        if 'mouse' in hgene:
            n_mouse = len(hgene['mouse'])
        # the HomoloGene mapping isn't necessarily 1-1
        if n_mouse >= 1 and n_human >= 1:
            n_homologs += 1

    logging.info("read " + str(n_homologenes) + " HomoloGene ids")
    logging.info(str(n_homologs) + " mouse genes map to at least one human gene via HomoloGene")
  
    return mgi2hgene_h

