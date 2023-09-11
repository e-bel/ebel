"""Root init for eBEL."""
from . import cache, constants, errors, parser, transformers
from .manager.orientdb.biodbs.bel import Bel

__version__ = "1.0.33"

__title__ = "e(BE:L)"
__description__ = "Validation and extension of biomedical knowledge graphs"
__url__ = "https://github.com/e-bel/ebel"

__author__ = "Christian Ebeling"
__email__ = "christian.ebeling@scai.fraunhofer.de"

__license__ = "?"
__copyright__ = """Copyright (c) 2021 Christian Ebeling, Fraunhofer Institute for Algorithms and Scientific
Computing SCAI, Schloss Birlinghoven, 53754 Sankt Augustin, Germany"""

project_name = __title__
