#!/usr/bin/env python3

from ccmm.dats.datsobj import DatsObj
import ccmm.mgd.human_homologs
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
    # TODO - add other types e.g., genes, human homologs, other feature types
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
    'pseudogenic_gene_segment': DatsObj("Annotation", [("value", "pseudogenic_gene_segment"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0001741")]),
    'homologous_region': DatsObj("Annotation", [("value", "homologous_region"), ("valueIRI", "http://purl.obolibrary.org/obo/SO_0000853")])
}

STRAND_CHADO2SO = {
    '+': 'forward',
    '-': 'reverse'
}

MGD_SEQ_DOWNLOAD_URL = "http://www.informatics.jax.org/downloads/reports/index.html#seq"

# Alternate and related identifiers
# TODO - move this into dats/datsobj and standardize list of possible databases with a CV
ID_URL_PREFIXES = {
    "NCBI_Gene": "https://www.ncbi.nlm.nih.gov/gene/?term=",
    "NCBI_HomoloGene": "https://www.ncbi.nlm.nih.gov/homologene/?term=",
    "ENSEMBL": "http://www.ensembl.org/Mus_musculus/Gene/Summary?db=core;g=",
    "VEGA": "http://vega.archive.ensembl.org/Mus_musculus/Gene/Summary?db=core;g=",
    "miRBase": "http://www.mirbase.org/cgi-bin/mirna_entry.pl?acc=",
    "GenBank": "https://www.ncbi.nlm.nih.gov/nuccore/",
    "RefSeq": "https://www.ncbi.nlm.nih.gov/refseq/?term=",
    # assumes that appended id already includes "MGI:"
    "MGI": "http://www.informatics.jax.org/marker/"
}

def get_dats_id_aux(id_type, source, id, rel_type):
    url_prefix = ID_URL_PREFIXES[source]
    atts = [("identifier", url_prefix + id)]
    atts.append(("identifierSource", source))
    if rel_type is not None:
        atts.append(("relationType", rel_type))
    return DatsObj(id_type, atts)

def get_dats_id(source, id):
    return get_dats_id_aux("Identifier", source, id, None)

def get_dats_related_id(source, id, rel_type):
    return get_dats_id_aux("RelatedIdentifier", source, id, rel_type)

def get_dats_alternate_id(source, id):
    # AlternateIdentifiers have no relationType
    return get_dats_id_aux("AlternateIdentifier", source, id, None)

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
    
def get_dataset_json(gff3_path, human_homologs_path):
    # read human homologs from MGI human/mouse sequence file
    mgi2hgene_h = ccmm.mgd.human_homologs.read_mgd_mouse_human_seq_file(human_homologs_path)

    # read mouse features/genes from GFF3
    data = read_mgd_gff3(gff3_path)

    # molecular entities that represent genes and other top-level features of interest
    entities = []

    # number of mouse genes/features with no human homolog
    n_homolog = 0
    n_no_homolog = 0
    n_genes = 0

    # relationType is a string/uri
    h_region = SO_TERMS['homologous_region'].get('valueIRI')

    # TODO - add taxonomy, either in 'isAbout' or in each individual gene (or both)

    for f in data['features']:
        if f['source'] == 'MGI':
            if re.match(r'^gene|pseudogene|sequence_feature$', f['type']) and (f['bioType'] != 'DNA segment'):
                id = f['ID']
                id = re.sub(r'MGI:MGI:', 'MGI:', id)
                roles = None
                # is this a gene or a gene segment
                is_gene = re.match(r'gene', f['type']) or re.match(r'gene', f['bioType'])
                if is_gene:
                    n_genes += 1

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
                        alt_ids.append(get_dats_alternate_id(src, src_id)) 

                # unharmonized data/anything that doesn't map anywhere else
                extra_props = [
                    DatsObj("CategoryValuesPair", [("category", "reference sequence"), ("values", [ f['seqid'] ])]),
                    DatsObj("CategoryValuesPair", [("category", "start coordinate"), ("values", [ f['start'] ])]),
                    DatsObj("CategoryValuesPair", [("category", "end coordinate"), ("values", [ f['end'] ])]),
                    DatsObj("CategoryValuesPair", [("category", "strand"), ("values", [ f['strand'] ])])
                    ]

                # human homologs
                related_ids = []
                has_homolog = False

                if id in mgi2hgene_h:
                    hgene = mgi2hgene_h[id]
                    homologene_id = hgene['id']
                    human_genes = []

                    # add HomoloGene reference
                    related_ids.append(get_dats_related_id("NCBI_HomoloGene", homologene_id, h_region))

                    if 'human' in hgene:
                        human_genes = hgene['human']
                        has_homolog = True
                    for human_gene in human_genes:
                        entrez_gene_id = human_gene['EntrezGene ID']
                        related_ids.append(get_dats_related_id("NCBI_Gene", entrez_gene_id, h_region))

                if is_gene:
                    if has_homolog:
                        n_homolog += 1
                    else:
                        n_no_homolog += 1

                me = DatsObj('MolecularEntity', [
                        ("name", f['Name']),
                        ("identifier", get_dats_id("MGI", id)),
                        ("alternateIdentifiers", alt_ids),
                        ("relatedIdentifiers", related_ids),
                        ("characteristics", characteristics),
                        ("roles", roles),
                        ("extraProperties", extra_props),
                        ])

                entities.append(me)

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

    logging.debug("human homolog found for " + str(n_homolog) + "/" + str(n_genes) + " mouse (pseudo)genes")
    logging.debug("no human homolog found for " + str(n_no_homolog) + "/" + str(n_genes) + " mouse (pseudo)genes")
    return parent_mgd_dataset
