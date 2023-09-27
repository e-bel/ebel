# -*- coding: utf-8 -*-

"""This file contains default values for configurations and parameters."""

import logging.config

from ebel.constants import DATA_DIR, PROJECT_DIR, THIS_DIR, LOG_DIR

###############################################################################
# UNIPROT taxonomy IDs to import

default_tax_ids = [
    9606,  # Humans
    10116,  # Rats
    10090,  # Mice
    7227,  # Drosophila melanogaster
    694009,
    2697049,  # COVID
    7955,  # Zebrafish
]
###############################################################################

SQLITE_DATABASE_NAME = "ebel.db"
SQLITE_TEST_DATABASE_NAME = "ebel_test.db"
DATABASE_LOCATION = DATA_DIR.joinpath(SQLITE_DATABASE_NAME)
DEFAULT_TEST_DATABASE_LOCATION = DATA_DIR.joinpath(SQLITE_TEST_DATABASE_NAME)

###############################################################################
# SQLAlchemy connection strings
# =============================
# SQLite
# ------
CONN_STR_DEFAULT = "sqlite:///" + DATABASE_LOCATION.name
CONN_STR_TESTS = "sqlite:///" + DEFAULT_TEST_DATABASE_LOCATION.name
# MySQL
# -----
CONN_STR_MYSQL_PREFIX = "mysql+pymysql://ebel:ebel@localhost/"
CONN_STR_MYSQL = CONN_STR_MYSQL_PREFIX + "ebel?charset=utf8"
CONN_STR_MYSQL_TESTS = CONN_STR_MYSQL_PREFIX + "ebel_test?charset=utf8"

###############################################################################
# Config
config_file_path = PROJECT_DIR.joinpath("config.ini")

###############################################################################
# Log Handling
logging.config.fileConfig(THIS_DIR.joinpath("logging.conf"), defaults={"logfilename": LOG_DIR.joinpath("ebel.log")})
