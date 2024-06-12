"""Root init for eBEL."""
from ebel import cache, constants, errors, parser, transformers
from ebel.manager.orientdb.biodbs.bel import Bel

__version__ = "1.1.0"

__title__ = "e(BE:L)"
__description__ = "Validation and extension of biomedical knowledge graphs"
__url__ = "https://github.com/e-bel/ebel"

__author__ = "Christian Ebeling"
__email__ = "christian.ebeling@scai.fraunhofer.de"

__license__ = "?"
__copyright__ = """Copyright (c) 2023 Christian Ebeling, Fraunhofer Institute for Algorithms and Scientific
Computing SCAI, Schloss Birlinghoven, 53754 Sankt Augustin, Germany"""

project_name = __title__
