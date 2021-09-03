"""Defined variables used throughout the package."""
# -*- coding: utf-8 -*-

import os

THIS_DIR = os.path.dirname(__file__)
PROJECT_NAME = 'ebel'

HOME = os.path.expanduser('~')
LIBRARY_NAME = PROJECT_NAME

# Path to folder
PROJECT_DIR = os.path.join(HOME, f".{PROJECT_NAME}")
if not os.path.exists(PROJECT_DIR):
    os.mkdir(PROJECT_DIR)

# Path to data folder
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

# Path to logs folder
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

# Default database name and location
DB_NAME = '{}.db'.format(PROJECT_NAME)
DB_PATH = os.path.join(DATA_DIR, DB_NAME)

GRAMMAR_BEL_PATH = {'2': os.path.join(THIS_DIR, 'grammar', 'grammar_bel_2.bnf'),
                    '2_1': os.path.join(THIS_DIR, 'grammar', 'grammar_bel_2_1.bnf'),
                    }

GRAMMAR_NS_ANNO_PATH = os.path.join(THIS_DIR, 'grammar', 'grammar_belns_belanno_1__2.bnf')
GRAMMAR_START_NS = 'belns'
GRAMMAR_START_ANNO = 'belanno'
GRAMMAR_START_LINE = 'script_line_by_line'

# Variables
RID = 'rid'

URL = "URL"
PATTERN = "PATTERN"
LIST = "LIST"
FILE = "FILE"
ALLOWED_TYPES = [URL, LIST, PATTERN, FILE]

DEFAULT_ODB = "DEFAULT_ODB"

# Protein Modifications
PMOD = {
    'pmod_ace': "Ac",
    'pmod_adr': "ADPRib",
    'pmod_add': "ADP-rybosylation",
    'pmod_far': "Farn",
    'pmod_ger': "Gerger",
    'pmod_gly': "Glyco",
    'pmod_hyd': "Hy",
    'pmod_isg': "ISG",
    'pmod_me0': "Me",
    'pmod_me1': "Me1",
    'pmod_mon': "monomethylation",
    'pmod_me2': "Me2",
    'pmod_me3': "Me3",
    'pmod_tri': "trimethylation",
    'pmod_myr': "Myr",
    'pmod_ned': "Nedd",
    'pmod_ngl': "NGlyco",
    'pmod_nit': "NO",
    'pmod_ogl': "OGlyco",
    'pmod_pal': "Palm",
    'pmod_pho': "Ph",
    'pmod_sul': "Sulf",
    'pmod_sup': "sulphation",
    'pmod_suh': "sulfonation",
    'pmod_sum': "Sumo",
    'pmod_suy': "Ub",
    'pmod_ubi': "ubiquitinylation",
    'pmod_u48': "UbK48",
    'pmod_u63': "UbK63",
    'pmod_ubm': "UbMono",
    'pmod_ubp': "UbPoly"
}

CYTOSCAPE_TEMPLATE = """{
  "format_version" : "1.0",
  "generated_by" : "cytoscape-3.6.0",
  "target_cytoscapejs_version" : "~2.1",
  "data" : {
    "shared_name" : "BEL_in_Cytoscape",
    "name" : "BEL_in_Cytoscape",
    "SUID" : 100000000,
    "__Annotations" : [ "" ],
    "networkMetadata" : "",
    "selected" : false
  },
  "elements" : {
    "nodes" : %s,
    "edges" : %s
  }
}"""

MD_FILE_HEADER = """Error report"""

SPECIES_NAMESPACE = {
    "HGNC": 9606,
    "MGI": 10090,
    "RGD": 10116,
    "FLYBASE": 7227,
}

# Edge types
# Causal
INCREASES = 'increases'
DIRECTLY_INCREASES = 'directly_increases'
CAUSAL_INCREASE = {INCREASES, DIRECTLY_INCREASES}

DECREASES = 'decreases'
DIRECTLY_DECREASES = 'directly_decreases'
CAUSAL_DECREASE = {DECREASES, DIRECTLY_DECREASES}

# Correlative
POSITIVE_CORRELATION = 'positive_correlation'
NEGATIVE_CORRELATION = 'negative_correlation'
