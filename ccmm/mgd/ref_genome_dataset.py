#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
from collections import OrderedDict
import csv
import gzip
import logging
import re
import sys

EXPECTED_GENOME_BUILD = "GRCm38-C57BL/6J"
N_GFF_FIELDS = 9

MGI = DatsObj("Organization", [("abbreviation", "MGI"),("name", "Mouse Genome Informatics")])

MGD = DatsObj("DataRepository", [
        ("name", "MGD"),
        ("description", "Mouse Genome Database"),
        ("publishers", [MGI])
        ])

## Ontology for Biomedical Investigations
# "DNA sequencing"
DNA_SEQUENCING_TYPE = OrderedDict([("value", "DNA sequencing"), ("valueIRI", "http://purl.obolibrary.org/obo/OBI_0000626")])

MGD_TYPES = [
    DatsObj("DataType", [("information", DNA_SEQUENCING_TYPE)])
    # TODO - add other types e.g., genes, orthologs, other feature types
    ]

# SO term lookup 
SO_TERMS = {
    'direction_attribute': DatsObj("Annotation", [("value", "direction_attribute"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0001029")]),
    'forward': DatsObj("Annotation", [("value", "forward"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0001030")]),
    'reverse': DatsObj("Annotation", [("value", "reverse"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0001031")]),
    'chromosome': DatsObj("Annotation", [("value", "chromosome"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0000340")]),
    'gene': DatsObj("Annotation", [("value", "gene"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0000704")]),
    'gene_segment': DatsObj("Annotation", [("value", "gene_segment"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_3000000")]),
    'pseudogene': DatsObj("Annotation", [("value", "pseudogene"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0000336")]),
    'pseudogenic_gene_segment': DatsObj("Annotation", [("value", "pseudogenic_gene_segment"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0001741")])
}

STRAND_CHADO2SO = {
    '+': 'forward',
    '-': 'reverse'
}

MGD_SEQ_DOWNLOAD_URL = "http://www.informatics.jax.org/downloads/reports/index.html#seq"

# TODO - replace this with a proper validating GFF3 parser (from Biocode?)
#  but note that MGI GFF3 may not validate due to:
#    1. CDS features lacking IDs required of multi-line features
#    2. some features (maybe?) violating unique ID constraint due to genome sequence patches
# TODO - this is unnecessarily memory-intensive - each gene is a separate block in the MGI GFF
#  and could be parsed separately
def read_mgd_gff3(gff3_path):
    md = {}
    providers = []
    provider = None
    feats = []
    i2f = {}
    p2c = {}
    c2p = {}

    data = { 'metadata': md, 'providers': providers, 'features': feats, 'id2feat': i2f, 'parent2child': p2c, 'child2parent': c2p }

    fh = None
    if re.match(r'.*\.gz$', gff3_path):
        fh = gzip.open(gff3_path, 'rt')
    else:
        fh = open(gff3_path)

    if fh is None:
        logging.fatal("failed to open GFF3 file " + gff3_path)
        sys.exit(1)

    reader = csv.reader(fh, delimiter='\t')
    lnum = 0
    for line in reader:
        lnum += 1
         # comment lines
        if re.match(r'^#.*', line[0]):
            # extract metadata
            m = re.match(r'^# \s*(Last updated|Description|URL|Latest-version|Generated|Genome build|Contact): (\S.*)$', line[0])
            if m is not None:
                md[m.group(1)] = m.group(2)
                logging.debug("GFF metadata: " + m.group(1) + " = " + m.group(2))

            # info on Providers/source data files for MGI Unified Gene Catalog e.g., 
            # Provider: miRBase
            #   File: miRBase21_mmu.gff3
            #   Modified: Wed Mar 16 15:40:58 2016
            m = re.match(r'^# Provider: (\S+)', line[0])
            # new Provider
            if m is not None:
                provider = { 'name': m.group(1) }
                providers.append(provider)
            elif provider is not None:
                m = re.match(r'^#\s+(File|Modified): (\S.*)\s*$', line[0])
                if m is not None:
                    provider[m.group(1)] = m.group(2)
                # end of Provider block
                elif re.match(r'^#\s*$', line[0]):
                    provider = None

        # not comment lines
        else:
            ll = len(line)
            if ll != N_GFF_FIELDS:
                logging.fatal("unexpected (" + str(ll) + ") number of GFF fields at line " + str(lnum) + " of " + gff_file)
                sys.exit(1)

            (seqid, source, type, start, end, score, strand, phase, attributes) = line

            # only parse MGI features for now
            # feature IDs are not unique if non-MGI features are included, due to the inclusion of genomic patch sequences:
            #  see egrep 'ID=NCBI_Gene:NM_001034869.2' MGI.gff3 
            if source != 'MGI':
                continue

            feat = { 'seqid': seqid, 'source': source, 'type': type, 'start': start, 'end': end, 'strand': strand, 'lnum': lnum }
            feats.append(feat)

            # parse attributes
            atts = attributes.rsplit(';')
            for att in atts:
                (key, delim, value) = att.partition('=')
                if delim == "":
                    logger.fatal("failed to split attribute value '" + att + "' at line " + str(lnum))
                    sys.exit(1)
                if key in feat:
                    logger.fatal("GFF3 attribute shadows fixed column '" + key + "' at line " + str(lnum))
                    sys.exit(1)
                feat[key] = value

            # record id mapping and parent/child relationships
            id = None
            parent = None

            if 'ID' in feat:
                id = feat['ID']
                i2f[id] = feat
            if 'Parent' in feat:
                parent = feat['Parent']

            if (id is not None) and (parent is not None):
                if id in c2p:
                    if i2f[parent] != c2p[id]:
                        logging.fatal("id " + id + " maps to different parent feature at line " + str(lnum) + " of " + gff3_path)
                        sys.exit(1)
                else:
                    # assume that parent always precedes child in the GFF
                    c2p[id] = i2f[parent]

                if parent in p2c:
                    p2c[parent].append(feat)
                else:
                    p2c[parent] = [ feat ]

    # check genome release matches expected
    if md['Genome build'] != EXPECTED_GENOME_BUILD:
        logging.fatal("read unexpected mouse genome build (" + md['Genome build'] + ") from " + gff3_path)
        sys.exit(1)

    return data
    
def get_dataset_json(gff3_path):
    data = read_mgd_gff3(gff3_path)

    # molecular entities that represent genes and other top-level features of interest
    entities = []

    # TODO - add taxonomy, either in 'isAbout' or in each individual gene (or both)

    for f in data['features']:
        if f['source'] == 'MGI':
            if re.match(r'^gene|pseudogene|sequence_feature$', f['type']) and (f['bioType'] != 'DNA segment'):
                id = f['ID']
                id = re.sub(r'MGI:MGI:', 'MGI:', id)
                roles = None

                # specify/map GFF3 feature type to role
                if f['type'] == 'sequence_feature':
                    bioType = re.sub(r' ', '_', f['bioType'])
                    roles = [ SO_TERMS[bioType] ]
                else:
                    roles = [ SO_TERMS[f['type']] ]

                # array of dimension or material
                characteristics = [
                    # chromosome
                    DatsObj("Dimension", [("name", {'value': 'chromosome'}), ("types", [SO_TERMS['chromosome']]), ("values", [f['seqid']])]),
                    # start coordinate
                    # end coordinate
                    ]

                # strand
                # direction_attribute only allows 'forward' or 'reverse' so if the strand is unknown the characteristic is omitted
                if f['strand'] in STRAND_CHADO2SO:
                    # map chado strand to name of corresponding SO term
                    SO_strand = STRAND_CHADO2SO[f['strand']]
                    DATS_strand = DatsObj("Dimension", [
                            ("name", {'value': 'direction_attribute'}), 
                            ("types", [SO_TERMS['direction_attribute']]), 
                            # in dimension_schema.json 'values' is an array with no other constraints, hence 
                            # our use of a string rather than an explicit reference to the SO ID
                            ("values", [SO_strand])
                            ])
                    characteristics.append(DATS_strand)

                # dbxrefs
                alt_ids = []
                if 'Dbxref' in f:
                    dbxref = f['Dbxref']
                    dbxrefs = dbxref.rsplit(',')
                    for dbx in dbxrefs:
                        (src, delim, src_id) = dbx.partition(':')
                        alt_ids.append(DatsObj("AlternateIdentifier", [("identifier", src_id), ("identifierSource", src)]))

                # unharmonized data/anything that doesn't map anywhere else
                extra_props = [
                    DatsObj("CategoryValuesPair", [("category", "reference sequence"), ("values", [ f['seqid'] ])]),
                    DatsObj("CategoryValuesPair", [("category", "start coordinate"), ("values", [ f['start'] ])]),
                    DatsObj("CategoryValuesPair", [("category", "end coordinate"), ("values", [ f['end'] ])]),
                    DatsObj("CategoryValuesPair", [("category", "strand"), ("values", [ f['strand'] ])])
                    ]


                me = DatsObj('MolecularEntity', [
                        ("name", f['Name']),
                        ("identifier", DatsObj("Identifier", [("identifier", id), ("identifierSource", "MGI")])),
                        ("alternateIdentifiers", alt_ids),
                        # TODO - add human orthologs to relatedIdentifiers
                        ("relatedIdentifiers", []),
                        ("characteristics", characteristics),
                        ("roles", roles),
                        ("extraProperties", extra_props),
                        ])

                entities.append(me)

                # DEBUG
                break

            else:
                logging.debug("skipped feature of type " + f['type'] + " at line " + str(f['lnum']) + ": mgiName=" + f['mgiName'] + ", bioType=" + f['bioType'])

    # parent MGD reference genome dataset
    parent_mgd_dataset = DatsObj("Dataset", [
            ("identifier", DatsObj("Identifier", [
                        ("identifier", "GRCm38-C57BL/6J"),
                        ("identifierSource", "MGI")
                        ])),
            ("title",  "GRCm38-C57BL/6J reference genome, genes, and human orthologs"),
            ("description", "GRCm38-C57BL/6J reference genome, genes, and human orthologs based on MGI/MGD Unified Mouse Gene Catalog."),
            ("storedIn", MGD),
            ("types", MGD_TYPES),
            ("creators", [ MGI, DatsObj("Person", [("email", data['metadata']['Contact'])]) ]),
            ("distributions", [DatsObj("DatasetDistribution", [
                                    ("access", DatsObj("Access", [
                                                ("landingPage", MGD_SEQ_DOWNLOAD_URL)
                                                ]))
                                    ])]),
            ("version", data['metadata']['Last updated']),
            ("isAbout", entities)
            ])

    # TODO - add 'licenses', 'availability', 'dimensions', 'primaryPublications'?
    # TODO - add sub-Datasets for the individual MGI files that contributed to the DATS encoding?
    #   metadata['URL'] gives the FTP URI of the source data file

    return parent_mgd_dataset
