"""OrientDB defaults."""
from enum import Enum
from typing import Dict


class OIndexType(Enum):
    """Allowed OrientDB Index types."""

    NOTUNIQUE = 'notunique'
    UNIQUE = 'unique'
    FULLTEXT = 'fulltext'
    DICTIONARY = 'dictionary'
    UNIQUE_HASH_INDEX = 'unique_hash_index'
    NOTUNIQUE_HASH_INDEX = 'notunique_hash_index'
    FULLTEXT_HASH_INDEX = 'fulltext_hash_index'
    DICTIONARY_HASH_INDEX = 'dictionary_hash_index'


class ODataType(Enum):
    """Allowed OrientDB Data types."""

    BOOLEAN = 'BOOLEAN'
    BINARY = 'BINARY'
    BYTE = 'BYTE'
    DATE = 'DATE'
    DATETIME = 'DATETIME'
    DECIMAL = 'DECIMAL'
    DOUBLE = 'DOUBLE'
    EMBEDDED = 'EMBEDDED'
    EMBEDDEDLIST = 'EMBEDDEDLIST'
    EMBEDDEDSET = 'EMBEDDEDSET'
    EMBEDDEDMAP = 'EMBEDDEDMAP'
    FLOAT = 'FLOAT'
    INTEGER = 'INTEGER'
    LONG = 'LONG'
    LINK = 'LINK'
    LINKLIST = 'LINKLIST'
    LINKSET = 'LINKSET'
    LINKMAP = 'LINKMAP'
    LINKBAG = 'LINKBAG'
    STRING = 'STRING'
    SHORT = 'SHORT'


bel_func_short: Dict[str, str] = {
    "gmod": 'gmod',
    "protein": 'p',
    "abundance": 'a',
    "micro_rna": 'm',
    "rna": 'r',
    "gene": 'g',
    "activity": 'act',
    "fragment": 'frag',
    "pmod": 'pmod',
    "location": 'loc',
    "variant": 'var',
    "complex": 'complex',
    "reaction": 'rxn',
    "reactants": 'reactants',
    "products": 'products',
    "pathology": 'path',
    "degradation": 'deg',
    "biological_process": 'bp',
    "list": 'list',
    "cell_secretion": 'sec',
    "composite": 'composite',
    "translocation": 'tloc',
    "fusion_protein": 'fus',
    "fusion_rna": 'fus',
    "fusion_gene": 'fus',
    "from_location": 'fromLoc',
    "to_location": 'toLoc',
    "cell_surface_expression": 'surf',
    "population": 'pop'
}

normalized_pmod: Dict[str, str] = {
    'ace': "Ac",
    'adr': "ADPRib",
    'add': "\"ADP-rybosylation\"",
    'far': "Farn",
    'ger': "Gerger",
    'gly': "Glyco",
    'hyd': "Hy",
    'isg': "ISG",
    'me0': "Me",
    'me1': "Me1",
    'mon': "monomethylation",
    'me2': "Me2",
    'me3': "Me3",
    'tri': "trimethylation",
    'myr': "Myr",
    'ned': "Nedd",
    'ngl': "NGlyco",
    'nit': "NO",
    'ogl': "OGlyco",
    'pal': "Palm",
    'pho': "Ph",
    'sul': "Sulf",
    'sup': "sulphation",
    'suh': "sulfonation",
    'sum': "sulphonation",
    'suy': "Sumo",
    'ubi': "Ub",
    'u48': "UbK48",
    'u63': "UbK63",
    'ubm': "UbMono",
    'ubp': "UbPoly",
    'pre': 'Prenylation',  # added for BioGrid
    'dei': 'de-ISGylation',  # added for BioGrid
    'fat': 'FAT10ylation'
}

normalized_pmod_reverse = {v: k for k, v in normalized_pmod.items()}


class BelPmod:
    """Protein modification definitions."""

    ACE = normalized_pmod['ace']
    ADR = normalized_pmod['adr']
    ADD = normalized_pmod['add']
    FAR = normalized_pmod['far']
    GER = normalized_pmod['ger']
    GLY = normalized_pmod['gly']
    HYD = normalized_pmod['hyd']
    ISG = normalized_pmod['isg']
    ME0 = normalized_pmod['me0']
    ME1 = normalized_pmod['me1']
    MON = normalized_pmod['mon']
    ME2 = normalized_pmod['me2']
    ME3 = normalized_pmod['me3']
    TRI = normalized_pmod['tri']
    MYR = normalized_pmod['myr']
    NED = normalized_pmod['ned']
    NGL = normalized_pmod['ngl']
    NIT = normalized_pmod['nit']
    OGL = normalized_pmod['ogl']
    PAL = normalized_pmod['pal']
    PHO = normalized_pmod['pho']
    SUL = normalized_pmod['sul']
    SUP = normalized_pmod['sup']
    SUH = normalized_pmod['suh']
    SUM = normalized_pmod['sum']
    SUY = normalized_pmod['suy']
    UBI = normalized_pmod['ubi']
    U48 = normalized_pmod['u48']
    U63 = normalized_pmod['u63']
    UBM = normalized_pmod['ubm']
    UBP = normalized_pmod['ubp']
    PRE = normalized_pmod['pre']  # added for BioGrid
    DEI = normalized_pmod['dei']  # added for BioGrid
    FAT = normalized_pmod['fat']
