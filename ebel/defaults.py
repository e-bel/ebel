# -*- coding: utf-8 -*-

"""This file contains default values for configurations and parameters."""

import os
import logging
import logging.handlers as handlers

from .constants import PROJECT_DIR, DATA_DIR, LOG_DIR

###############################################################################
# UNIPROT taxonomy IDs to import

default_tax_ids = [
    9606,  # Humans
    10116,  # Rats
    10090,  # Mice
    7227,  # Drosophila melanogaster
    694009, 2697049,  # COVID
    7955,  # Zebrafish
]
###############################################################################

SQLITE_DATABASE_NAME = 'ebel.db'
SQLITE_TEST_DATABASE_NAME = 'ebel_test.db'
DATABASE_LOCATION = os.path.join(
    DATA_DIR,
    SQLITE_DATABASE_NAME
)
DEFAULT_TEST_DATABASE_LOCATION = os.path.join(
    DATA_DIR,
    SQLITE_TEST_DATABASE_NAME
)

###############################################################################
# SQLAlchemy connection strings
# =============================
# SQLite
# ------
CONN_STR_DEFAULT = 'sqlite:///' + DATABASE_LOCATION
CONN_STR_TESTS = 'sqlite:///' + SQLITE_TEST_DATABASE_NAME
# MySQL
# -----
CONN_STR_MYSQL_PREFIX = 'mysql+pymysql://ebel:ebel@localhost/'
CONN_STR_MYSQL = CONN_STR_MYSQL_PREFIX + 'ebel?charset=utf8_bin'
CONN_STR_MYSQL_TESTS = CONN_STR_MYSQL_PREFIX + 'ebel_test?charset=utf8_bin'

###############################################################################
# Config
config_file_path = os.path.join(PROJECT_DIR, 'config.ini')

###############################################################################
# Log Handling
logHandler = handlers.RotatingFileHandler(filename=os.path.join(LOG_DIR, 'ebel.log'),
                                          mode='a',
                                          maxBytes=4098 * 10,  # 4MB file max
                                          backupCount=0)
logh_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logHandler.setFormatter(logh_format)
logHandler.setLevel(logging.DEBUG)

# Console Handler
ch = logging.StreamHandler()
ch_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(ch_format)
ch.setLevel(logging.WARNING)
