"""General methods used by e(BE:L) modules."""
import re
import gzip
import shutil
import hashlib
import configparser

import os.path

from types import GeneratorType

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.base import Engine
from typing import Iterable, Union, List

from ebel import defaults
from ebel.config import write_to_config, get_config_value
from ebel.defaults import CONN_STR_DEFAULT
from ebel.constants import DATA_DIR


class BelRdb(object):
    """Singleton for Relational Database Connection."""

    __instance = None

    def __new__(cls):
        """Define new object."""
        if BelRdb.__instance is None:
            BelRdb.__instance = object.__new__(cls)
            connection_string = _get_connection_string()
            dialect = re.search(r"^(\w+)(\+\w+)?:", connection_string).group(1)
            if dialect == 'mysql':
                utf8mb4 = "charset=utf8mb4"
                if utf8mb4 not in connection_string:
                    connection_string = connection_string + f"?{utf8mb4}"
                BelRdb.__instance.engine = create_engine(connection_string, pool_size=30, max_overflow=10)
            else:
                BelRdb.__instance.engine = create_engine(connection_string)
            BelRdb.__instance.session = sessionmaker(bind=BelRdb.__instance.engine)()
        return BelRdb.__instance


def _get_connection_string():
    """Get the sqlalchemy connection string from config file, sets the default string if not there."""
    return get_config_value('DATABASE', 'sqlalchemy_connection_string', CONN_STR_DEFAULT)


def _get_engine() -> Engine:
    """Get SQLAlchmey engine."""
    connection_string = _get_connection_string()
    engine = create_engine(connection_string, pool_size=30, max_overflow=10)
    return engine


def _get_session_object():
    return sessionmaker(bind=_get_engine())


def get_session():
    """Return session object."""
    return _get_session_object()()


def chunks(parsable: Iterable, size: int = 100) -> GeneratorType:
    """Generate a list of chunks with specific size [default=100]."""
    chunk = []
    counter = 0
    for e in parsable:
        counter += 1
        chunk.append(e)
        if counter == size:
            yield chunk
            chunk = []
            counter = 0
    yield chunk


def get_standard_name(name: str) -> str:
    """Return standard name."""
    part_of_name = [x for x in re.findall("[A-Z]*[a-z0-9]*", name) if x]
    new_name = "_".join(part_of_name).lower()
    if re.search(r'^\d+', new_name):
        new_name = '_' + new_name
    return new_name


def md5(file_path):
    """Calculate md5 for file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_path(url: str, biodb: str):
    """Get standard file path by file_name and DATADIR."""
    file_name = os.path.basename(url)
    bio_db_dir = os.path.join(DATA_DIR, biodb)
    os.makedirs(bio_db_dir, exist_ok=True)
    return os.path.join(bio_db_dir, file_name)


def get_file_name(url_or_path):
    """Get standard file path by file_name and DATADIR."""
    return os.path.basename(url_or_path)


def gunzip(file_path: str, file_path_gunzipped: str):
    """Gunzip a file."""
    with gzip.open(file_path, 'rb') as f_in:
        with open(file_path_gunzipped, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def get_disease_trait_keywords_from_config(traits: Union[str, list] = None, overwrite: bool = False) -> List[str]:
    """Interface with the e(BE:L) config file.

    This reads and returns keywords found in the 'SNP_RELATED_TRAITS' section or it will create the section using
    the passed traits.

    Parameters
    ----------
    traits: Union[str, List[str]]
        The list of pathologies/pathogens.
    overwrite: [bool, optional]
        Can choose to overwrite the default disease_trait_keyword value in the config file.

    Returns
    -------
    If the config file has the 'SNP_RELATED_TRAITS' section, the method returns the value(s) stored in the
    "keyword" section. If no section or config file exists, returns the default value: ['Alzheimer'].
    """
    section_name = "SNP_RELATED_TRAITS"
    option = "keyword"

    if traits and isinstance(traits, list):
        traits = ",".join([trait.strip() for trait in traits])

    if traits and isinstance(traits, str):
        traits = ",".join([trait.strip() for trait in traits.split(",")])  # Split, strip, recombine

    if os.path.isfile(defaults.config_file_path):  # If config file exists
        cfg = configparser.ConfigParser()
        cfg.read(defaults.config_file_path)

        if cfg.has_section(section_name) and not overwrite:  # If there is a section for the default value
            traits = cfg.get(section_name, option)  # Get keyword from config

        elif traits and overwrite:  # Traits passed and overwrite enabled
            write_to_config(section_name, option, traits)

        elif not cfg.has_section(section_name) and traits:  # No section but traits passed
            write_to_config(section_name, option, traits)

    else:  # If no config file then write a new one with the section/option/value
        write_to_config(section_name, option, traits)

    if not isinstance(traits, list):
        traits = traits.split(",")

    return traits if traits is not None else []
