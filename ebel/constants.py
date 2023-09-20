"""Defined variables used throughout the package."""
# -*- coding: utf-8 -*-

import os
from pathlib import Path

THIS_DIR = Path(__file__)
PROJECT_NAME = "ebel"

HOME = Path.home()
LIBRARY_NAME = PROJECT_NAME

# Path to folder
PROJECT_DIR = Path(HOME, f".{PROJECT_NAME}")
PROJECT_DIR.mkdir(parents=True, exist_ok=True)

# Path to data folder
DATA_DIR = Path(PROJECT_DIR, "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Path to logs folder
LOG_DIR = Path(PROJECT_DIR, "logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default database name and location
DB_NAME = f"{PROJECT_NAME}.db"
DB_PATH = Path(DATA_DIR, DB_NAME)

GRAMMAR_BEL_PATH = {
    "2": THIS_DIR.joinpath("grammar", "grammar_bel_2.bnf"),
    "2_1": THIS_DIR.joinpath("grammar", "grammar_bel_2_1.bnf"),
}

GRAMMAR_NS_ANNO_PATH = THIS_DIR.joinpath("grammar", "grammar_belns_belanno_1__2.bnf")
GRAMMAR_START_NS = "belns"
GRAMMAR_START_ANNO = "belanno"
GRAMMAR_START_LINE = "script_line_by_line"

# Variables
RID = "rid"

URL = "URL"
PATTERN = "PATTERN"
LIST = "LIST"
FILE = "FILE"
ALLOWED_TYPES = [URL, LIST, PATTERN, FILE]

DEFAULT_ODB = "DEFAULT_ODB"

# Protein Modifications
PMOD = {
    "pmod_ace": "Ac",
    "pmod_adr": "ADPRib",
    "pmod_add": "ADP-rybosylation",
    "pmod_far": "Farn",
    "pmod_ger": "Gerger",
    "pmod_gly": "Glyco",
    "pmod_hyd": "Hy",
    "pmod_isg": "ISG",
    "pmod_me0": "Me",
    "pmod_me1": "Me1",
    "pmod_mon": "monomethylation",
    "pmod_me2": "Me2",
    "pmod_me3": "Me3",
    "pmod_tri": "trimethylation",
    "pmod_myr": "Myr",
    "pmod_ned": "Nedd",
    "pmod_ngl": "NGlyco",
    "pmod_nit": "NO",
    "pmod_ogl": "OGlyco",
    "pmod_pal": "Palm",
    "pmod_pho": "Ph",
    "pmod_sul": "Sulf",
    "pmod_sup": "sulphation",
    "pmod_suh": "sulfonation",
    "pmod_sum": "Sumo",
    "pmod_suy": "Ub",
    "pmod_ubi": "ubiquitinylation",
    "pmod_u48": "UbK48",
    "pmod_u63": "UbK63",
    "pmod_ubm": "UbMono",
    "pmod_ubp": "UbPoly",
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
INCREASES = "increases"
DIRECTLY_INCREASES = "directly_increases"
CAUSAL_INCREASE = {INCREASES, DIRECTLY_INCREASES}

DECREASES = "decreases"
DIRECTLY_DECREASES = "directly_decreases"
CAUSAL_DECREASE = {DECREASES, DIRECTLY_DECREASES}

# Correlative
POSITIVE_CORRELATION = "positive_correlation"
NEGATIVE_CORRELATION = "negative_correlation"


# Terminal Colors
class TerminalFormatting:
    """Terminal style definitions."""

    RESET = "\033[0m"

    class Format:
        """Format style definitions."""

        BOLD = "\033[1m"
        ITALIC = "\033[3m"
        UNDERLINED = "\033[4m"
        STRIKETHROUGH = "\033[9m"

    class Fore:
        """Foreground style definitions."""

        __temp = "\033[{}m"
        __temp_b = "\033[1;{}m"
        RED = __temp.format(31)
        RED_BRIGHT = __temp_b.format(31)
        GREEN = __temp.format(32)
        GREEN_BRIGHT = __temp_b.format(32)
        YELLOW = __temp.format(33)
        YELLOW_BRIGHT = __temp_b.format(33)
        BLUE = __temp.format(34)
        BLUE_BRIGHT = __temp_b.format(34)
        PINK = __temp.format(35)
        PINK_BRIGHT = __temp_b.format(35)
        CYAN = __temp.format(36)
        CYAN_BRIGHT = __temp_b.format(36)
        WHITE = __temp_b.format(37)
        BLACK = __temp.format(30)
        GREY = __temp_b.format(30)
        GREY_BRIGHT = __temp_b.format(37)

    class Back:
        """Back style definitions."""

        __temp = "\033[{}m"
        NOTHING = __temp.format(40)
        RED = __temp.format(41)
        GREEN = __temp.format(42)
        YELLOW = __temp.format(43)
        BLUE = __temp.format(44)
        PINK = __temp.format(45)
        BLUE_LIGHT = __temp.format(46)
        GREY = __temp.format(47)

    TITLE = f"{Back.GREY}{Fore.BLUE}{Format.BOLD}{Format.UNDERLINED}"
    HEADER = f"{Fore.YELLOW}{Format.BOLD}{Format.UNDERLINED}"
    QUESTION = f"{Fore.GREEN}{Format.ITALIC}"
    DEFAULT_VALUE = f"{Fore.GREEN_BRIGHT}"
