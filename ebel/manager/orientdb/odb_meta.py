"""Meta classes for OrientDb."""
import abc
import copy
import json
import logging
import os
import random
import socket
import time

from abc import abstractmethod
from collections import defaultdict, OrderedDict
from http.client import RemoteDisconnected
from shutil import copyfileobj
from types import GeneratorType
from typing import List, Iterable, Dict, Union, Tuple, Set, Optional
from urllib.request import urlopen, Request

import numpy as np
import pandas as pd
import requests
import xmltodict
import sqlalchemy as sqla
from sqlalchemy.sql.schema import Table
from sqlalchemy_utils import database_exists, create_database

from pyorientdb import OrientDB, orient
from pyorientdb.exceptions import PyOrientIndexException, PyOrientCommandException, PyOrientSecurityAccessException
from pyorientdb.otypes import OrientRecord

from tqdm import tqdm

import ebel.database
from ebel.constants import RID, DEFAULT_ODB
from ebel.cache import set_mysql_interactive
from ebel.manager.orientdb import urls as default_urls
from ebel.manager.orientdb.odb_structure import OClass, OIndex, OProperty, Edge, Generic, Node
from ebel.tools import BelRdb, get_file_path, chunks, get_standard_name
from ebel.config import write_to_config, get_config_as_dict

type_map_inverse = {v: k for k, v in orient.type_map.items()}

logger = logging.getLogger(__name__)


class ExceptionClassNotExists(Exception):
    """Package specific exception class definition."""

    def __init__(self, message):
        """Init method."""
        self.message = message


class Graph(abc.ABC):
    """Generic parent class for BioDBs."""

    def __init__(
            self,
            generics: Tuple[Generic] = (),
            nodes: Tuple[Node] = (),
            edges: Tuple[Edge] = (),
            indices: Tuple[OIndex] = (),
            urls: dict = None,
            biodb_name: str = '',
            tables_base=None,
            config_params: Optional[dict] = None,
            overwrite_config: bool = False,
    ):
        """Init method."""
        self.generic_classes: Tuple[OClass] = generics
        self.node_classes: Tuple[OClass] = nodes
        self.edge_classes: Tuple[OClass] = edges
        self.class_indices: Tuple[OIndex] = indices
        self.tables_base = tables_base  # sqlalchemy base

        self.urls = urls if urls else {}
        self.biodb_name = biodb_name

        self.odb_db_name = config_params['db'] if config_params and 'db' in config_params else None
        self.odb_user = config_params['user'] if config_params and 'user' in config_params else None
        self.odb_password = config_params['password'] if config_params and 'password' in config_params else None
        self.odb_server = config_params['server'] if config_params and 'server' in config_params else 'localhost'
        self.odb_port = config_params['port'] if config_params and 'port' in config_params else '2424'
        self.odb_user_reader = None
        self.odb_user_reader_password = None
        # Root password should not be set, but can be
        self._odb_root_password = None

        self.__config_params_check(overwrite_config)
        self.client: OrientDB = self.get_client()

        self.create_all_classes()
        self.cluster_ids = {}

        rdb = BelRdb()
        self.engine = rdb.engine
        self.session = rdb.session

        if not database_exists(self.engine.url):
            if str(self.engine.url).startswith("mysql"):
                set_mysql_interactive()

            else:
                create_database(self.engine.url)

    def __config_params_check(self, overwrite_config: bool = False):
        """Go through passed/available configuration params."""
        # Set the client
        config_dict = get_config_as_dict()

        credentials = {
            "name": self.odb_db_name,
            "user": self.odb_user,
            "password": self.odb_password,
            "server": self.odb_server,
            "port": int(self.odb_port),
            "root_password": self._odb_root_password
        }

        # If values are passed
        if all(credentials.values()):
            #  If there is no "DEFAULT_ODB" section in the configuration file, then write these values to it
            if DEFAULT_ODB not in config_dict:
                for option, value in credentials.items():
                    if "root" not in option and overwrite_config:  # Don't want to write root to config file
                        write_to_config(section=DEFAULT_ODB, option=option, value=value)

            self.set_configuration_parameters()

        # If there is a "DEFAULT_ODB" section in the configuration file, then read these values
        elif DEFAULT_ODB in config_dict:
            self.set_configuration_parameters()

        # No parameters passed and no saved parameters in config means user needs to provide some info
        else:
            missing_params = ", ".join({key for key, val in credentials.items() if val is None})
            raise ValueError(f"Please provide initial configuration parameters. Missing parameters: {missing_params}")
            # logger.error(f"Please provide initial configuration parameters. Missing parameters: {missing_params}")

    def execute(self, command_str: str) -> List[OrientRecord]:
        """Execute a command directly in the OrientDB server.

        Parameters
        ----------
        command_str: str
            The SQL to be executed

        Raises
        ------
        PyOrientCommandException
            Caused by a disconnect to the ODB server. eBEL will try to reconnect if possible.

        Returns
        -------
        ODB response.
        """
        try:
            return self.client.command(command_str)

        # TODO: following exceptions seems not to cover connection error
        # except (PyOrientCommandException, PyOrientSecurityAccessException):
        except:
            # Try to reconnect
            self.client.close()
            self.client = self.get_client()
            # self.client.db_open(self.odb_name, self.odb_user, self.odb_password)
            # print(command_str)
            return self.client.command(command_str)

    def set_configuration_parameters(self):
        """Set configuration for OrientDB database client instance using configuration file or passed params."""
        odb_config = get_config_as_dict().get(DEFAULT_ODB)

        self.odb_db_name = self.odb_db_name or odb_config.get('name')
        self.odb_user = self.odb_user or odb_config.get('user')
        self.odb_password = self.odb_password or odb_config.get('password')
        self.odb_server = self.odb_server or odb_config.get('server')
        self.odb_port = int(self.odb_port or odb_config.get('port') or '2424')
        self.odb_user_reader = self.odb_user_reader or odb_config.get('user_reader') or None
        self.odb_user_reader_password = self.odb_user_reader_password or odb_config.get('user_reader_password') or None

        # Root password should not be written in the config file, but it's possible
        self._odb_root_password = self._odb_root_password or odb_config.get('root_password')

    def get_client(self) -> OrientDB:
        """Attempts to connect to the OrientDB client. This is currently done by using session tokens."""
        client = ebel.database.get_orientdb_client(self.odb_server, self.odb_port, self.odb_db_name, self.odb_user,
                                                   self.odb_password, self._odb_root_password, self.odb_user_reader,
                                                   self.odb_user_reader_password)

        return client

    def __repr__(self):
        """Represent the class."""
        template = "{{BioDatabase:{class_name}}}[url:{url}, edges:{edges}, generics:{generics}]"
        representation = template.format(
            class_name=self.__class__.__name__,
            url=self.urls,
            edges={k: v for k, v in self.number_of_edges.items() if v},
            nodes={k: v for k, v in self.number_of_nodes.items() if v},
            generics={k: v for k, v in self.number_of_generics.items() if v}
        )
        return representation

    @abstractmethod
    def insert_data(self) -> Dict[str, int]:
        """Insert all generic data."""

    @abstractmethod
    def update_interactions(self) -> int:
        """Insert all generic data."""

    def clear_and_import_data(self) -> Dict[str, int]:
        """Clears the associated table and inserts the data from raw downloaded data."""
        inserted = {}
        logger.info(f"Clear generics for {self.biodb_name}")
        if self.generic_classes:
            self.clear_generics()

        if self.tables_base:
            self.recreate_tables()

        try:
            inserted = self.insert_data()
            logger.info(f"Successfully inserted data for {self.biodb_name}")

        except FileNotFoundError:
            logging.error(f"Data file for {self.biodb_name.upper()} was not found. Skipping...")

        except Exception as e:
            logger.error(f"Failed to insert data for {self.biodb_name}!", exc_info=e)

        return inserted

    def create_index_rdbms(self, table_name: str, columns):
        """Creates index on column(s) in RDBMS."""
        if isinstance(columns, str):
            columns = [columns]
        sql_columns = ','.join(columns)
        index_name = f"idx_{table_name}_" + "_".join(columns)
        self.engine.execute(f"CREATE INDEX {index_name} ON {table_name} ({sql_columns})")

    def clear_edges_by_bel_doc_rid(self, bel_document_rid: str, even_if_other_doc_rids_exists=True):
        """Delete all edges linked to a specified BEL document rID."""
        changes = 0
        if even_if_other_doc_rids_exists:
            sql = f'DELETE FROM `bel_relation` WHERE {bel_document_rid} IN document'
            changes = self.execute(sql)[0]

        else:
            sql = f'SELECT @rid.asString() AS rid, document.asString() FROM `bel_relation` ' \
                  f'WHERE {bel_document_rid} IN document'
            for r in self.query_get_dict(sql):
                new_rids = [x.strip() for x in r['document'][1:-1].split(',')]
                new_rids.remove(bel_document_rid)
                if new_rids:
                    new_rids_str = ','.join(new_rids)
                    self.execute(f"UPDATE {r['rid']} SET document = [{new_rids_str}]")
                    changes += 1
                else:
                    self.execute(f"DELETE EDGE {r['rid']}")
                    changes += 1

        self.execute(f"DELETE from bel_document where @rid = {bel_document_rid}")

        return changes

    def clear_documents(self) -> int:
        """Clear all document info. Returns number of deleted documents."""
        return self.execute('Delete from `bel_document`')[0]

    def get_number_of_bel_statements_by_document_rid(self, bel_document_rid: str) -> int:
        """Return BEL statement count with a given document ID."""
        sql = f"Select count(*) as num from bel_relation where  document = {bel_document_rid}"
        return self.execute(sql)[0].oRecordData['num']

    def get_documents(self):
        """Return all document info as pandas DataFrame."""
        return self.query('Select * from bel_document')

    def get_documents_as_dict(self):
        """Return all document info as pandas DataFrame."""
        return [x.oRecordData for x in self.execute('Select * from bel_document')]

    def add_keyword(self, keyword: str, description: str) -> pd.DataFrame:
        """Add a keyword and description used to tagging BEL documents.

        Parameters
        ----------
        keyword : str
            The name of a project the work is based on or type of work
        description : str
            Detailed explanation of the keyword
        """
        sql = f"INSERT INTO keyword CONTENT {'label': {keyword}, 'description': {description}}"
        return self.query(sql)

    def get_info_class(self, class_name):
        """Return info about class."""
        sql = "Select * from (SELECT expand( classes ) FROM metadata:schema) where name='{}' limit 1"
        return self.execute(sql.format(class_name))[0].oRecordData

    def get_info_properties(self, class_name: str, short: bool = True):
        """Get the property information for a specified table."""
        sql_temp = "select expand(properties) from (select expand(classes) from metadata:schema) where name = '{}'"
        sql = sql_temp.format(class_name)
        o_record_datas = [x.oRecordData for x in self.execute(sql)]

        if short:
            props = [{'name': x['name'], 'type': type_map_inverse[x['type']]} for x in o_record_datas]

        else:
            props = o_record_datas

        return props

    def entry_exists(self, class_name, **params) -> bool:
        """Check if class_name whith parameters exists."""
        where_list = []
        for column, value in params.items():
            if isinstance(value, (str, list, dict)):
                where_list.append("`{}` = {}".format(column, json.dumps(value)))
            elif isinstance(value, (int, float)):
                where_list.append("`{}` = {}".format(column, value))

        where = " and ".join(where_list)
        sql = "Select 1 from `{}` where {} limit 1".format(class_name, where)
        results = self.execute(sql)

        return bool(len(results))

    def query(self, sql: str) -> pd.DataFrame:
        """Return a pandas DataFrame results table."""
        results = self.execute(sql)
        return pd.DataFrame([x.oRecordData for x in results])

    def query_get_dict(self, sql: str) -> List[dict]:
        """Return list of dictionaries using a given SQL query."""
        results = self.execute(sql)
        return [x.oRecordData for x in results]

    def query_class(self, class_name: str, limit: int = 0, skip: int = 0, columns: Iterable[str] = None,
                    with_rid=True, with_class=False, print_sql: bool = False, group_by: List[str] = None,
                    distinct=False, as_dataframe: bool = False, where_list: Tuple[str] = (),
                    **params) -> Union[List[dict], pd.DataFrame]:
        """Query class by params and returns list of pyorient.OrientRecord."""
        if not self.class_exists(class_name):
            raise ExceptionClassNotExists("Class {} not exists in database.".format(class_name))

        where = self.__get_sql_where_part(params, where_list)

        sql_limit = ""
        if limit:
            sql_limit = "LIMIT {}".format(limit)

        sql_skip = ""
        if skip:
            sql_skip = "SKIP {}".format(skip)

        if isinstance(columns, Iterable):
            cols = columns

        else:
            cols = ["*"]

        if with_rid:
            cols.append("@rid.asString()")

        if with_class:
            cols.append("@class.asString()")

        sql_cols = ", ".join(cols)

        if isinstance(group_by, Iterable):
            group_by = "GROUP BY " + ", ".join(group_by)

        else:
            group_by = ''

        if distinct and len(cols) == 1:
            sql_cols = "distinct({})".format(sql_cols)

        sql_temp = "SELECT {sql_cols} FROM `{class_name}` {where} {group_by} {sql_limit} {sql_skip}"

        sql = sql_temp.format(sql_cols=sql_cols,
                              class_name=class_name,
                              where=where,
                              sql_limit=sql_limit,
                              sql_skip=sql_skip,
                              group_by=group_by)

        if print_sql:
            print(sql)

        results = self.execute(sql)

        if as_dataframe:
            return_value = pd.DataFrame([x.oRecordData for x in results])

        else:
            return_value = [x.oRecordData for x in results]

        return return_value

    def query_class_chunks(self, class_name: str, chunk_size: int = 10000, columns: Iterable[str] = None,
                           with_rid=True, with_class=False, print_sql: bool = False, group_by: List[str] = None,
                           distinct: bool = False):
        """Query class by params and only return a set of results in batches. Creates a generator."""
        number_entries = self.get_number_of_class(class_name)
        total_num_chunks = (number_entries // chunk_size) + 1

        chunk_index = 0
        while chunk_index < total_num_chunks:
            generic_table_chunk = self.query_class(class_name=class_name,
                                                   limit=chunk_size,
                                                   skip=chunk_size * chunk_index,
                                                   with_rid=with_rid,
                                                   with_class=with_class,
                                                   print_sql=print_sql,
                                                   group_by=group_by,
                                                   distinct=distinct,
                                                   columns=columns)
            yield generic_table_chunk
            chunk_index += 1

    def query_rid(self, rid, columns: list = None):
        """Query specified columns of a given rID entry."""
        table_columns = columns if columns else []
        columns_in_sql = ', '.join(table_columns)
        results = self.execute(f"Select {columns_in_sql} from {rid}")
        if results:
            return [x.oRecordData for x in results][0]

    def download(self,
                 url_dict: Dict[str, str] = None,
                 biodb: str = None,
                 expiration_days: int = 100) -> Dict[str, bool]:
        """Download url to file_path if not older than expiration_days."""
        if not url_dict and hasattr(self, 'urls'):
            url_dict = self.urls

        downloaded = {}

        for key, url in url_dict.items():
            downloaded[key] = self.download_file(url, self.biodb_name, expiration_days)

        return downloaded

    @staticmethod
    def download_file(url: str, biodb: str, expiration_days: int = 100, addtional_header: dict = None) -> bool:
        """Download file. Returns True if it was needed to download the file."""
        header = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/"
                          "537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"}
        if addtional_header:
            header.update(addtional_header)

        expiration_secs = expiration_days * 60 * 60 * 24
        now = time.time()
        downloaded = False
        file_path = get_file_path(url, biodb)
        file_exists = os.path.exists(file_path)

        if file_exists:
            expired = now - os.path.getmtime(file_path) > expiration_secs
        else:
            expired = True

        if not file_exists or expired:
            logger.info(f"Download {url}")
            try:
                with urlopen(Request(url, headers=header)) as response, open(file_path, 'wb') as out_file:
                    copyfileobj(response, out_file)

                downloaded = True

            except RemoteDisconnected:
                logger.error(f"{url} could not be downloaded! Website appears to be down.", exc_info=False)

            except Exception:
                logger.error(f"{url} could not be downloaded!", exc_info=True)

        return downloaded

    def index_exists(self, index_name: str):
        """Check if index_name exists."""
        sql = """Select 1 as exists from (select expand(indexes)
                  from metadata:indexmanager) where name = '{}'""".format(index_name)
        return len(self.execute(sql)) > 0

    def create_index(self, index: OIndex):
        """Create index."""
        sql = "CREATE INDEX {index_name} ON `{class_name}` ({columns}) {index_type}"

        index_name = self.get_index_name(index)
        if not self.index_exists(index_name):
            sql = sql.format(class_name=index.class_name,
                             columns=",".join(index.columns),
                             index_name=self.get_index_name(index),
                             index_type=index.index_type.value)
            try:
                self.execute(sql)

            except PyOrientIndexException:
                errmsg = f"Index failure: {self.get_index_name(index)} on {index.class_name}. Check ODB version."
                logger.error(errmsg)

        return self

    def get_index_name(self, index: OIndex):
        """Return index name."""
        return index.class_name + "." + "__".join(index.columns)

    def create_all_classes(self):
        """Create all classes."""
        class_names = self.create_classes(self.classes)

        self.create_indices(self.class_indices)
        return class_names

    def create_all_indices(self):
        """Create indices."""
        for index in self.class_indices:
            self.create_index(index)

    def create_indices(self, indices: Tuple[OIndex]):
        """Create indices."""
        for index in indices:
            self.create_index(index)

    def drop_all_indices(self):
        """Drop indices."""
        for index in self.class_indices:
            self.drop_index(index)

    def drop_indices(self, indices: List[OIndex]):
        """Drop indices."""
        for index in indices:
            self.drop_index(index)

    def drop_index(self, index: OIndex):
        """Drop index."""
        self.execute("DROP INDEX {}".format(self.get_index_name(index)))

    def create_node_classes(self):
        """Create node classes."""
        class_names = self.create_classes(self.node_classes)
        self.create_indices(self.class_indices)
        return class_names

    def create_edge_classes(self):
        """Create edge classes."""
        class_names = self.create_classes(self.edge_classes)
        self.create_indices(self.class_indices)
        return class_names

    def create_generic_classes(self):
        """Create generic classes."""
        class_names = self.create_classes(self.generic_classes)
        self.create_indices(self.class_indices)
        return class_names

    @property
    def classes(self) -> Tuple[OClass, ...]:
        """Return generic, node and edge classes as List[OClass]."""
        return self.generic_classes + self.node_classes + self.edge_classes

    def create_classes(self, oclasses: Tuple[OClass] = None):
        """Create classes.

        list of classes (odb_structure.OClass)
        OrientDB class v, e or g
        for vertex, edge or generic
        """
        created = []

        for oclass in oclasses:
            self.create_class(oclass)
            created.append(oclass.name)
        return created

    def create_class(self, oclass: OClass, print_sql=False):
        """Create class.

        OrientDB class v, e or g
        for vertex, edge or generic
        """
        sql_class = "CREATE CLASS {name} IF NOT EXISTS {extends} {abstract}"

        sql_dict = {"name": "`" + oclass.name + "`", "extends": '', "abstract": ''}

        if oclass.extends:
            sql_dict['extends'] = "EXTENDS " + ", ".join(["`" + x + "`" for x in oclass.extends])
        if oclass.abstract:
            sql_dict['abstract'] = "ABSTRACT"

        sql = sql_class.format(**sql_dict)
        if print_sql:
            print(sql)
        self.execute(sql)

        if oclass.props:
            for prop in oclass.props:
                self.create_class_property(class_name=oclass.name, prop=prop)

        if isinstance(oclass, Edge):
            sql_in_out = f"CREATE PROPERTY {oclass.name}.{{}}  IF NOT EXISTS LINK {{}}"
            if oclass.in_out[0]:
                self.execute(sql_in_out.format('in', oclass.in_out[0]))
            if oclass.in_out[1]:
                self.execute(sql_in_out.format('out', oclass.in_out[1]))

    def create_class_property(self, class_name: str, prop: OProperty, print_sql: bool = False):
        """Create OrientDB class property."""
        sql_prop = "CREATE PROPERTY `{name}`.`{prop_name}`\
        IF NOT EXISTS {dtype} {linked_class} {linked_type} {mandatory}"

        linked_class = prop.linked_class or ''
        linked_type = prop.linked_type.value if prop.linked_type else ''
        mandatory = "(MANDATORY TRUE)" if prop.mandatory else ''
        sql = sql_prop.format(name=class_name,
                              prop_name=prop.prop_name,
                              dtype=prop.data_type.value,
                              linked_class=linked_class,
                              linked_type=linked_type,
                              mandatory=mandatory)
        if print_sql:
            print(sql)
        self.execute(sql)

    def class_exists(self, class_name: str) -> bool:
        """Check if OrientDB class exists."""
        sql = "Select 1 as exists from (select expand(classes) from metadata:schema) where name = '{}'"
        r = self.execute(sql.format(class_name))
        return len(r) > 0

    def classes_exists(self, list_of_class_names):
        """Check if list of OrientDB classes exists."""
        for c in list_of_class_names:
            if not self.class_exists(c):
                return False
        return True

    def drop_class(self, class_name: str):
        """Drop the specified table."""
        self.execute("DROP CLASS `{}`".format(class_name))

    def __drop_classes(self, classes: Iterable[OClass]):
        """Delete the classes in opposite order."""
        dropped = []
        for oclass in classes[::-1]:
            if self.class_exists(oclass.name) and oclass.own_class:
                self.drop_class(oclass.name)
                dropped.append(oclass.name)
        return dropped

    def drop_all_classes(self):
        """Drop all classes."""
        return self.__drop_classes(self.classes)

    def drop_generic_classes(self):
        """Drop all generic classes."""
        return self.__drop_classes(self.generic_classes)

    def drop_node_classes(self):
        """Drop all node classes."""
        return self.__drop_classes(self.node_classes)

    def drop_edge_classes(self):
        """Drop all edge classes."""
        return self.__drop_classes(self.edge_classes)

    def clear(self):
        """Clear (delete entries) from all classes."""
        return {'nodes': self.clear_nodes(),
                'edges': self.clear_edges(),
                'generics': self.clear_generics()}

    def is_abstract_class(self, class_name: str) -> bool:
        """Returns true if class is abstract."""
        sql = """select 1 from (
                    select expand(classes) from metadata:schema
                    ) where name = '{}' and abstract = true"""
        return bool(self.execute(sql.format(class_name)))

    def clear_edges(self) -> Dict[str, int]:
        """Delete all edges."""
        deleted = {}
        sql_temp = "DELETE EDGE `{}`"
        if hasattr(self, 'edge_classes'):
            for oclass in self.edge_classes:
                if oclass.own_class and not oclass.abstract and self.class_exists(oclass.name):
                    sql = sql_temp.format(oclass.name)
                    deleted[oclass.name] = self.execute(sql)[0]
        return deleted

    def clear_class(self, class_name):
        """Delete all entries from class if exists."""
        sql = "DELETE FROM `{}`".format(class_name)
        deleted = self.execute(sql)[0]
        return deleted

    def clear_nodes(self):
        """Delete all nodes."""
        deleted = {}
        sql_temp = "DELETE VERTEX {}"
        for oclass in self.node_classes:
            if self.class_exists(oclass.name) and oclass.own_class:
                sql = sql_temp.format(oclass.name)
                deleted[oclass.name] = self.execute(sql)[0]
        return deleted

    def clear_nodes_with_no_edges(self):
        """Delete all nodes from a class with no edges."""
        sql_temp = "Delete vertex {} where bothE().size()=0"
        deleted = {}
        for oclass in self.node_classes:
            if self.class_exists(oclass.name) and oclass.own_class:
                sql = sql_temp.format(oclass.name)
                deleted[oclass.name] = self.execute(sql)[0]
        return deleted

    def clear_generics(self):
        """Delete all entries in generic tables."""
        deleted = {}
        for oclass in self.generic_classes:
            if self.class_exists(oclass.name):
                deleted[oclass.name] = self.clear_class(oclass.name)
        return deleted

    def recreate_tables(self):
        """Recreate SQLAlchemy tables in relational database."""
        self.tables_base.metadata.drop_all(self.engine)
        self.tables_base.metadata.create_all(self.engine)
        self.session.commit()

    def clear_nodes_and_edges(self):
        """Delete all nodes and edges of a specific biodb."""
        number_of_deleted_edges = self.clear_edges()
        number_of_deleted_nodes = self.clear_nodes()
        return {'nodes': number_of_deleted_nodes, 'edges': number_of_deleted_edges}

    def clear_all_nodes_and_edges(self):
        """Delete all nodes and edges in the whole database."""
        edges_deleted = self.execute("Delete edge E")[0]
        nodes_deleted = self.execute("Delete vertex V")[0]
        return {'edges': edges_deleted, 'nodes': nodes_deleted}

    def clear_exp_edges(self):
        """Delete all DEA experiment associated edges."""
        deleted = self.clear_class(class_name='ko_relation')
        return deleted

    def recreate(self):
        """Recreate OrientDB collection."""
        self.clear_edges()
        self.clear_nodes()
        self.drop_edge_classes()
        self.drop_node_classes()
        self.create_all_classes()

    def table_exists(self, table: Table):
        """Checks if the table exists in RDBMS."""
        return sqla.inspect(self.engine).has_table(table)

    @property
    def number_of_generics(self) -> Dict[str, int]:
        """Returns for number of entries in OrientDB classes and RDB tables. Tables have priority."""
        numbers = {}

        if self.tables_base:
            for table_name, table in self.tables_base.metadata.tables.items():
                if self.table_exists(table_name):
                    sql = f"Select count(*) from `{table_name}`"
                    numbers[table_name] = self.engine.execute(sql).fetchone()[0]
                else:
                    numbers[table_name] = 0
        elif self.generic_classes:
            for oclass in self.generic_classes:
                numbers[oclass.name] = self.get_number_of_class(oclass.name)

        return numbers

    @staticmethod
    def __get_sql_where_part(params, where_list: Tuple[str] = ()):
        """Return a ODB SQL where part by params."""
        where_list = list(where_list)
        for column, value in params.items():
            if isinstance(value, (str, list, dict)):
                if value == 'notnull':
                    where_list.append("`{}` IS NOT NULL".format(column))
                else:
                    where_list.append("`{}` = {}".format(column, json.dumps(value)))
            elif isinstance(value, (int, float)):
                where_list.append("`{}` = {}".format(column, value))
            elif value is None:
                where_list.append("`{}` IS NULL".format(column))
        where = ""
        if where_list:
            where = " WHERE " + " AND ".join(where_list)
        return where

    def get_number_of_class(self, class_name, distinct_column_name: str = None, **params):
        """Return count of unique values for a given class_name and column name."""
        column = '*'
        if distinct_column_name:
            column = f'distinct({distinct_column_name})'
        where = self.__get_sql_where_part(params)
        sql = f"Select count(`{column}`) from `{class_name}`{where}"
        return self.execute(sql)[0].oRecordData['count']

    @property
    def number_of_nodes(self):
        """Return node count."""
        numbers = {}
        for oclass in self.node_classes:
            if oclass.own_class:
                self.get_number_of_class(oclass.name)
                numbers[oclass.name] = self.get_number_of_class(oclass.name)
        return numbers

    @property
    def number_of_edges(self):
        """Return edge count."""
        numbers = {}
        for oclass in self.edge_classes:
            if oclass.own_class:
                numbers[oclass.name] = self.get_number_of_class(oclass.name)
        return numbers

    def get_cluster_ids(self, class_name: str) -> list:
        """Get all cluster ids by class name."""
        sql_cids = "Select clusterIds from (select expand(classes) from metadata:schema) where name = '{}'"
        if class_name not in self.cluster_ids:
            cids = self.execute(sql_cids.format(class_name))[0].oRecordData['clusterIds']
            self.cluster_ids[class_name] = cids
        return self.cluster_ids[class_name]

    def insert_record(self, class_name: str, value_dict: dict, print_sql=False) -> Optional[str]:
        """Insert new entry in class with values from dictionary. Returns rid."""
        sql = "insert into `{}` content {}".format(class_name, json.dumps(value_dict))

        if print_sql:
            print(sql)

        try:
            r = self.execute(sql)[0]
            return r._OrientRecord__rid

        except (PyOrientCommandException, socket.timeout):
            logger.error(f"Unable to execute\n{sql}", exc_info=True)

    def create_record(self, class_name: str, value_dict: dict) -> Optional[str]:
        """Create record/ insert into class_name with content of value_dict."""
        cid = random.choice(self.get_cluster_ids(class_name))

        try:
            r = self.client.record_create(cid, {'@' + class_name: value_dict})._OrientRecord__rid

        except (PyOrientCommandException, socket.timeout):
            logger.warning("Standard insert in odb_meta.create_record did not work!")
            r = self.insert_record(class_name, value_dict)

        except Exception:
            logger.error("Failed to create record", exc_info=True)
            return None

        return r

    def update_record(self, class_name: str, value_dict: dict) -> str:
        """Update record with content of value_dict."""
        cid = random.choice(self.get_cluster_ids(class_name))
        r = self.client.record_update(cid, {'@' + class_name: value_dict})
        return r._OrientRecord__rid

    def edge_exists(self, class_name: str, from_rid: str, to_rid: str, value_dict: dict = {}) -> str:
        """Check if edge exists. Return rid if exists else None."""
        data = copy.deepcopy(value_dict)  # deep copy and DO NOT change the dictionary!!!
        data.update({'out.@rid': from_rid, 'in.@rid': to_rid})
        result = self.query_class(class_name, limit=1, **data)
        if result:
            return result[0][RID]

    def node_exists(self, class_name: str, value_dict: dict = {}, check_for: Union[Iterable[str], str] = None,
                    print_sql: bool = False) -> str:
        """Check if node exists. Return rid if exists else None."""
        check_for_dict = value_dict.copy()
        if check_for:
            check_for = [check_for] if isinstance(check_for, str) else check_for
            check_for_dict = {k: v for k, v in check_for_dict.items() if k in check_for}
        result = self.query_class(class_name=class_name, limit=1, print_sql=print_sql, **check_for_dict)
        if result:
            return result[0][RID]

    def create_edge(self, class_name: str, from_rid: str, to_rid: str, value_dict: dict = {}, print_sql=False,
                    if_not_exists=False, ignore_empty_values=False) -> str:
        """Create edge from from_rid(@rid) to to_rid(@rid) with content of value_dict."""
        content = ''
        if if_not_exists:
            edge_rid = self.edge_exists(class_name, from_rid, to_rid, value_dict)
            if edge_rid:
                return edge_rid

        if value_dict:
            if ignore_empty_values:
                value_dict = {k: v for k, v in value_dict.items()}
            content = "CONTENT {}".format(json.dumps(value_dict))
        sql_temp = "CREATE EDGE `{class_name}` FROM {from_rid} TO {to_rid} {content}"
        sql = sql_temp.format(class_name=class_name, from_rid=from_rid, to_rid=to_rid, content=content)
        if print_sql:
            print(sql)
        r = self.execute(sql)[0]
        return r._OrientRecord__rid

    def get_create_rid(self, class_name: str, value_dict: dict, check_for=None, print_sql=False) -> str:
        """Return class_name.@rid by value_dict. Create record/insert if not exists."""
        rid = self.node_exists(class_name=class_name, value_dict=value_dict, check_for=check_for, print_sql=print_sql)
        if not rid:
            rid = self.insert_record(class_name=class_name, value_dict=value_dict, print_sql=print_sql)
        return rid

    def update_correlative_edges(self) -> List[str]:
        """Create a reverse edge for every correlative edge."""
        updated_edges = []

        correlative_edges = self.query_class(class_name="correlative", with_rid=False, with_class=True)
        for c_edge in tqdm(correlative_edges, desc="Creating reverse correlative edges"):
            from_rid = c_edge.pop('in').get_hash()
            to_rid = c_edge.pop('out').get_hash()
            edge_class = c_edge.pop("class")
            c_edge['document'] = [doc.get_hash() for doc in c_edge['document']]

            new_rid = self.create_edge(class_name=edge_class, from_rid=from_rid, to_rid=to_rid,
                                       value_dict=c_edge, if_not_exists=True)
            updated_edges.append(new_rid)
        return updated_edges

    def update_document_info(self):
        """Update document metadata."""
        self.update_pmids()
        self.update_pmcids()

    def update_pmcids(self) -> int:
        """Add PMC ID to bel_relation if one exists."""
        update_sql_tmp = "UPDATE bel_relation SET pmc = '{}' WHERE pmid = {}"
        missing_pmc_sql = "SELECT distinct(pmid) as pmid from bel_relation WHERE pmc IS NULL"

        results = self.query(missing_pmc_sql)

        updated = 0
        if results is not None and 'pmid' in results:
            pmids_with_missing_pmc = list(results['pmid'])

            id_dict = dict()
            for pmid_sublist in chunks(pmids_with_missing_pmc, size=200):
                pmid_string = ','.join([str(x) for x in pmid_sublist])
                url_filled = default_urls.NCBI_PMID.format(pmid_string)

                api_query_response = requests.get(url_filled)
                pmcids_json = json.loads(api_query_response.text)

                if 'records' in pmcids_json.keys():
                    for record in pmcids_json['records']:
                        if 'pmid' in record.keys():
                            if 'pmcid' in record.keys():
                                id_dict[record['pmid']] = record['pmcid']

                            else:
                                id_dict[record['pmid']] = None

            for pmid, pmc in tqdm(id_dict.items(), desc="Updating PMC IDs"):
                if pmc:
                    update_sql_filled = update_sql_tmp.format(pmc, pmid)
                    r = self.execute(update_sql_filled)
                    updated += len(r)

        return updated

    def update_pmids(self, edge_name='bel_relation'):
        """Update PMID metadata for all edges of the specified edge_name."""
        sql_missing_citations = """Select distinct(pmid)
                                    as pmid from {}
                                    where
                                        pmid IS NOT NULL and
                                        pmid > 0 and
                                        citation.pubdate IS NULL"""
        r = self.execute(sql_missing_citations.format(edge_name))
        pmids = [x.oRecordData['pmid'] for x in r]

        updated = 0

        # length of PMID around 8-9 digits: 150*10=1500 + url with 103 => ~1600
        # max length of url = 2,083
        if pmids:
            chunk_size = 150
            total = len(pmids) // chunk_size + 1

            for pmid_chunk in tqdm(
                    chunks(pmids, size=chunk_size),
                    total=total,
                    desc=f"Update PMID citations in {edge_name}"
            ):
                try:
                    updated += self._query_ncbi(pmid_chunk, edge_name)

                except KeyError as e:
                    logger.error("KeyError occurred during parsing. See logs for full description.")
                    logger.info(e)

        return updated

    def _query_ncbi(self, pmid_chunk: GeneratorType, edge_name: str):
        """Query NCBI for publication metadata."""
        sql_template = "Update {} set citation = {} where pmid = {}"

        sql_update_mesh_terms = "Update {} set annotation.mesh = {} where pmid = {}"
        sql_update_mesh_substances = "Update {} set annotation.substances = {} where pmid = {}"

        nameset = {'LastName', 'Initials'}

        start_time = time.time()
        url = default_urls.NCBI_MESH + ",".join([str(x) for x in pmid_chunk])
        xml_pubmed = requests.get(url)
        parsed_data = xmltodict.parse(xml_pubmed.text)

        updated = 0
        if 'PubmedArticleSet' in parsed_data:
            medline_citations = parsed_data['PubmedArticleSet']['PubmedArticle']

            if isinstance(medline_citations, OrderedDict):
                medline_citations = [medline_citations, ]

            for medlineCitation in medline_citations:
                mc = medlineCitation['MedlineCitation']
                data = {'type': "PubMed", 'ref': mc['PMID']['#text']}
                article = mc['Article']

                # Authors
                author_list = []
                if 'AuthorList' in article:  # Authors not always listed
                    authors = article['AuthorList']['Author']

                    if isinstance(authors, OrderedDict):
                        authors = [authors]

                    for author in authors:
                        if isinstance(author, OrderedDict) and nameset.issubset(author.keys()):
                            author_list.append(author['LastName'] + " " + author['Initials'])

                data['author_list'] = author_list

                if author_list:
                    data['last_author'] = author_list[-1]

                # Journal
                data['full_journal_name'] = mc['Article']['Journal']['Title']

                # Article Date
                article_date = mc.get('DateCompleted', mc.get('DateRevised'))
                if article_date:
                    ad = article_date.values()
                    data['pub_date'] = '-'.join(ad)
                    data['pub_year'] = int(list(ad)[0])

                # Title
                data['title'] = mc['Article']['ArticleTitle']

                # DOI
                if 'ELocationID' in mc['Article']:
                    eids = mc['Article']['ELocationID']

                    if isinstance(eids, OrderedDict):
                        eids = [mc['Article']['ELocationID']]

                    for eid in eids:
                        if eid.get('@EIdType') == 'doi':
                            data['doi'] = eid['#text']

                # MeSH Headings
                meshs = []
                if 'MeshHeadingList' in mc:
                    for mesh in mc['MeshHeadingList']['MeshHeading']:
                        m = mesh['DescriptorName']
                        meshs.append(m['#text'])

                # Associated chemicals
                substances = []
                if 'ChemicalList' in mc:
                    chemicals = mc['ChemicalList']['Chemical']
                    if isinstance(chemicals, OrderedDict):
                        chemicals = [chemicals]
                    for chemical in chemicals:
                        substances.append(chemical['NameOfSubstance']['#text'])

                data_json = json.dumps(data)
                sql = sql_template.format(edge_name, data_json, data['ref'])
                self.execute(sql)

                if meshs:
                    content_mesh = json.dumps(meshs)
                    sql_m = sql_update_mesh_terms.format(edge_name, content_mesh, data['ref'])
                    self.execute(sql_m)

                if substances:
                    content_substances = json.dumps(substances)
                    sql_s = sql_update_mesh_substances.format(edge_name, content_substances, data['ref'])
                    self.execute(sql_s)

                updated += 1
        # don't make NCBI angry
        if (time.time() - start_time) < 1:
            time.sleep(1)

        return updated

    @staticmethod
    def _standardize_column_names(columns: Iterable[str]) -> List[str]:
        """Standardize column names.

        Parameters
        ----------
        columns: Iterable[str]
            Iterable of columns names.
        """
        return [get_standard_name(x) for x in columns]

    def _standardize_dataframe(self, dataframe: pd.DataFrame,
                               replace_nulls_with_nones: bool = True,
                               standardize_column_names: bool = True,
                               replace_minus_with_nones: bool = True) -> pd.DataFrame:
        if standardize_column_names:
            dataframe.columns = self._standardize_column_names(dataframe.columns)

        if replace_nulls_with_nones:
            dataframe.replace({np.nan: None}, inplace=True)

        if replace_minus_with_nones and any(dataframe.dtypes == 'object'):
            dataframe.replace({'-': None}, inplace=True)

        return dataframe

    def import_dataframe(self, dataframe: pd.DataFrame, class_name: str, replace_nulls_with_nones: bool = True,
                         standardize_column_names: bool = True, replace: bool = True, ) -> int:
        """Import dataframe into OrientDb class with name."""
        sql_temp = f"insert into `{class_name}` content {{}}"
        inserted = 0

        if replace:
            self.clear_class(class_name)

        dataframe = self._standardize_dataframe(dataframe, replace_nulls_with_nones, standardize_column_names)

        for row in tqdm(dataframe.to_dict(orient='records'), desc=f"Insert {class_name.upper()} data"):
            sql = sql_temp.format(json.dumps(row))

            try:
                self.execute(sql)

            except PyOrientCommandException as pyorientdb_command_exception:
                logging.error('OrientDB SQL error:', sql, pyorientdb_command_exception)

            inserted += 1

        return inserted

    def batch_insert(self, dataframe: pd.DataFrame, database: str, chunk_size: int = 100, desc: str = None,
                     standardize_column_names: bool = False, replace: bool = True,
                     replace_nulls_with_nones: bool = False) -> int:
        """Adds rows of a dataframe into specified generic table in batches.

        Parameters
        ----------
        dataframe: pandas DataFrame
            A dataframe of information to be inserted into the generic table.
        database: str
            Name of the generic table to be inserted into.
        chunk_size: int (optional)
            Number of chunks to break the dataframe into for batching.
        desc: str
            A description for tqdm about what is being iterated through.
        standardize_column_names: bool
            If True (default=False), standardize column names.
        replace: bool
            If True (default), content of dataframe replaces old data.
        replace_nulls_with_nones: bool
            If True (default=False), replace numpy.nan with None (==null in OrientDB).
        Returns
        -------
        int
            Number of rows inserted into the table.
        """
        sql_temp = "INSERT INTO {} CONTENT {}"

        inserted = 0
        total = len(dataframe.index) // chunk_size + 1

        if standardize_column_names:
            dataframe.columns = self._standardize_column_names(dataframe.columns)

        if replace:
            self.clear_class(database)

        if replace_nulls_with_nones:
            dataframe.replace({pd.np.nan: None}, inplace=True)

        for chunk in tqdm(chunks(dataframe.index, chunk_size), total=total, desc=desc):

            batch_cmds = ['begin']
            for i in chunk:
                sql = sql_temp.format(database, dataframe.loc[i].to_json())
                batch_cmds.append(sql)
            batch_cmds.append("commit retry 100")
            cmd = ';'.join(batch_cmds)
            self.client.batch(cmd)
            inserted += len(chunk)

        return inserted

    def get_set_gene_rids_by_position(self,
                                      chromosome: str,
                                      position: int,
                                      gene_types=['mapped', 'downstream', 'upstream']) -> Dict[str, List[str]]:
        """Return dictionary of mapped gene by chromosal position.

        ALERT: creates new BEL HGNC gene is not exists.
        """
        gene_rids = defaultdict(list)
        sqls = dict()

        sqls['mapped'] = f"""Select symbol
                            from ensembl
                            where
                                start < {position} and
                                stop > {position} and
                                chromosome='{chromosome}' group by symbol"""

        sqls['downstream'] = f"""Select symbol
                            from ensembl
                            where
                                start > {position} and
                                chromosome='{chromosome}'
                            order by start limit 1"""

        sqls['upstream'] = f"""Select symbol
                            from ensembl
                            where
                                stop < {position} and
                                chromosome='{chromosome}'
                            order by stop desc limit 1"""

        for gene_type, sql in sqls.items():
            if gene_type in gene_types:
                results = self.engine.execute(sql)
                for symbol, in results.fetchall():
                    bel = f'g(HGNC:"{symbol}")'
                    data = {'name': symbol,
                            'namespace': "HGNC",
                            'bel': bel,
                            'pure': True}
                    gene_rid = self.get_create_rid('gene', value_dict=data, check_for='bel')
                    gene_rids[gene_type] += [gene_rid]

        return gene_rids

    def class_is_descendant_of(self, child_name: str, descendant_name: str) -> bool:
        """Returns True if child_name is a child class of descendent_name."""
        sql = "Select superClasses from (select expand(classes) from metadata:schema) where name='{}'"
        parents_exists = self.execute(sql.format(child_name))
        if parents_exists:
            data = parents_exists[0].oRecordData
            if data and 'superClasses' in data:
                parent_names = data['superClasses']

                if descendant_name in parent_names:
                    return True
                else:
                    for parent_name in parent_names:
                        return self.class_is_descendant_of(parent_name, descendant_name)
        return False

    def class_has_children(self, class_name) -> bool:
        """Checks if class_name has children that inherit from class_name."""
        sql = f"""Select count(name) from
                    (select expand(classes) from metadata:schema)
                  where '{class_name}' in superClasses"""
        return self.execute(sql)[0].oRecordData['count'] > 0

    def get_child_classes(self, class_name) -> List[str]:
        """Get list of child classes for given class_name."""
        sql = f"Select name from (select expand(classes) from metadata:schema) where '{class_name}' in superClasses"
        return [x.oRecordData['name'] for x in self.execute(sql)]

    def get_leaf_classes_of(self, class_name: str) -> List[str]:
        """Return list of children classes for the given class_name."""
        childs = self.get_child_classes(class_name)

        leafs = []
        for child in childs:
            if not self.class_has_children(child):
                leafs.append(child)
            else:
                leafs += self.get_leaf_classes_of(child)
        return leafs

    def insert(self) -> Dict[str, int]:
        """Check if files missing for download or generic table empty. If True then insert data."""
        inserted = {}
        downloaded = self.download()
        if any(downloaded.values()) or not all(self.number_of_generics.values()):
            inserted_entries = self.clear_and_import_data()
            inserted.update(inserted_entries)
        return inserted

    def update(self) -> None:
        """Check generics and update BEL interactions."""
        self.insert()
        self.update_bel()

    def update_bel(self) -> None:
        """Delete and update all class specific edges."""
        logger.info(f"Clear edges for {self.biodb_name}")
        self.clear_edges()
        logger.info(f"Update interactions for {self.biodb_name}")

        try:
            self.update_interactions()
            logger.info(f"Successfully updated interactions for {self.biodb_name.upper()}")

        except Exception as e:
            logging.error(e, exc_info=e)

    def delete_nodes_with_no_edges(self, class_name=None) -> int:
        """Delete all nodes without any edges."""
        if isinstance(class_name, str) and not self.class_exists(class_name):
            wtext = f'You try to delete nodes with no edges from class {class_name}, ' \
                    f'but node class {class_name} not exits.'
            logger.warning(wtext)
            return 0
        else:
            class_name = class_name if class_name is not None else 'V'
            return self.execute(f"Delete VERTEX {class_name} where both().size() = 0")[0]

    def get_pure_symbol_rids_dict_in_bel_context(self, class_name='protein', namespace='HGNC') -> Dict[str, str]:
        """Return dictionary with HGNC names as key and OrientDB @rid as value.

        Applies to all pure nodes in graph with class name directly or indirectly involved in BEL stmt.
        This method could be helpful to avoid graph explosion.
        """
        # only include symbols which are also part of a BEL statement to avoid explosion of graph
        # Following sql also includes any modification of proteins

        # all pure nodes with bel_relation
        sql = "Select name as symbol, @rid.asString() as rid from " \
              + class_name + " where pure=true and namespace='" \
              + namespace + "' and name in (Select name from (match { class:" \
              + class_name + ", as: p, where:(namespace='" + namespace + \
              "') }.(bothE('bel_relation'){ where: (document IS NOT NULL) }) return distinct(p.name) as name))"
        return {r['symbol']: r['rid'] for r in self.query_get_dict(sql)}

    def get_pure_uniprots_in_bel_context(self) -> Set[str]:
        """Returns a list of all uniprot accessions in BEL annotation context."""
        sql = "match {class:protein, where:(uniprot IS NOT NULL), as:p}.(bothE('bel_relation')" \
              "{class: bel_relation,where:(document IS NOT NULL)}) return distinct(p.uniprot) as uniprot"
        return {x['uniprot'] for x in self.query_get_dict(sql)}

    def get_pure_symbol_rid_df_in_bel_context(self, class_name='protein', namespace='HGNC') -> pd.DataFrame:
        """Return dictionary with gene symbols as keys and node rIDs as values."""
        r = self.get_pure_symbol_rids_dict_in_bel_context(class_name=class_name, namespace=namespace)
        return pd.DataFrame(r.items(), columns=['symbol', 'rid'])

    def get_pure_symbol_rids_dict(self, class_name='protein', namespace='HGNC') -> Dict[str, str]:
        """Return dictionary with protein name as keys and node rIDs as values."""
        results = self.query_class(class_name, pure=True, namespace=namespace)
        return {r['name']: r['rid'] for r in results}

    def get_pure_rid_by_uniprot(self, uniprot: str):
        """Get rIDs of node based on UniProt ID."""
        sql = f"Select @rid.asString() as rid from protein where pure = true and uniprot='{uniprot}' limit 1"
        results = self.query_get_dict(sql)
        if results:
            return results[0]['rid']

    def get_pure_uniprot_rid_dict_in_bel_context(self) -> Dict[str, str]:
        """Return dictionary with UniProt accession id as key and OrientDB @rid as value.

        Applies to all pure nodes in graph with class name directly or indirectly involved in BEL statement.
        This method could be helpful to avoid graph explosion.
        """
        # only include proteins which are also part of a BEL statement to avoid explosion of graph

        sql = """Select uniprot, @rid.asString() as rid from protein where pure=true and uniprot in (
        Select unionall(uniprot_list).asSet() as all_uniprots from (select unionall(in.uniprot, out.uniprot).asSet() as
        uniprot_list from bel_relation where document IS NOT NULL
        and (in.uniprot IS NOT NULL or out.uniprot IS NOT NULL)))"""

        return {r['uniprot']: r['rid'] for r in self.query_get_dict(sql)}

    def get_pure_uniprot_rids_dict(self):
        """Return dictionary with UniProt IDs as keys and node rIDs as values."""
        sql = "Select uniprot, @rid.asString() as rid from protein where uniprot IS NOT NULL and pure=true"
        results = self.query_get_dict(sql)
        return {r['uniprot']: r['rid'] for r in results}
