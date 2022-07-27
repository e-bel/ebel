"""Variables used by all tests in the test_manager directory."""
import os
import pathlib

from ebel import Bel
from ebel.constants import DEFAULT_ODB
from ebel.config import get_config_value
from ebel.manager.orientdb.odb_meta import Graph

# Paths
VALIDATION_TEST_DIR = pathlib.Path(__file__).parent.absolute()
TEST_DATA_DIR = os.path.join(VALIDATION_TEST_DIR, "..", "data")

IMPORT_DIR = os.path.join(TEST_DATA_DIR, "import_tests")
TEST_BEL = os.path.join(IMPORT_DIR, "basic_import_test.bel")
TEST_JSON = TEST_BEL + ".json"

# Parameters for TEST database
USER = get_config_value(DEFAULT_ODB, 'user')
PASSWORD = get_config_value(DEFAULT_ODB, 'password')
DB_NAME = 'ebel_test'
SERVER = 'localhost'
PORT = "2424"
ROOT_PWD = get_config_value(DEFAULT_ODB, 'root_password')

if ROOT_PWD is None:
    raise ValueError("Need root password to perform tests. Please add 'root_password' to configuration file")

# Configure client
config_params = {
    "db": DB_NAME,
    "user": USER,
    "password": PASSWORD,
    "server": SERVER,
    "port": PORT,
    "root_password": ROOT_PWD
}

test_client = Bel(graph_config=config_params)
