"""This module contains the SQLAlchemy database models that support the definition cache and graph cache."""

import os
import re
import urllib
import codecs
import logging
import requests
import datetime
import sqlalchemy
import pandas as pd

from tqdm import tqdm
from lark import Lark
from urllib.parse import urlencode, quote_plus
from typing import List, Tuple, Optional, Union

from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Column, ForeignKey, Integer, String, Index, Boolean

from sqlalchemy_utils import create_database, database_exists

from ebel import parser
from ebel.tools import BelRdb
from ebel.constants import GRAMMAR_NS_ANNO_PATH, GRAMMAR_START_NS, GRAMMAR_START_ANNO, URL, FILE


Base = declarative_base()
logger = logging.getLogger(__name__)


def reset_tables(engine: sqlalchemy.engine.Engine, force_new_db: bool) -> None:
    """Drop all tables in database.

    Parameters
    ----------
    engine: sqlalchemy.engine.Engine
        sqlalchemy.engine.Engine
    force_new_db: bool : bool
        True forces to create new tables.
    """
    if not database_exists(engine.url):
        create_database(engine.url)

    if force_new_db:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine, checkfirst=True)


def foreign_key_to(table_name):
    """Create a standard foreign key to a table in the database.

    :param table_name: name of the table without TABLE_PREFIX
    :type table_name: str
    :return: foreign key column
    :rtype: sqlalchemy.Column
    """
    foreign_column = table_name + '.id'
    return Column(Integer, ForeignKey(foreign_column))


class MasterModel(object):
    """Parent class of all models in PyHGNC.

    Automatic creation of table name by class name with project prefix.
    """

    @declared_attr
    def __tablename__(self):
        """Return name of class table."""
        return self.__name__.lower()

    __mapper_args__ = {'always_refresh': True}

    id = Column(Integer, primary_key=True)

    def _to_dict(self):
        """Protected method for converting values to dictionary."""
        data_dict = self.__dict__.copy()
        del data_dict['_sa_instance_state']
        del data_dict['id']
        for k, v in data_dict.items():
            if isinstance(v, datetime.date):
                data_dict[k] = data_dict[k].strftime('%Y-%m-%d')
        return data_dict

    def to_dict(self):
        """Return values as dictionary."""
        return self._to_dict()


class Namespace(Base, MasterModel):
    """Represents a BEL Namespace."""

    __tablename__ = "namespace"
    __table_args__ = (Index("idx_url", "url", mysql_length=100),)

    url = Column(String(2048), nullable=False)
    keyword = Column(String(255, collation="utf8_bin"), index=True)
    cacheable = Column(Boolean)
    case_sensitive = Column(Boolean)

    entries = relationship("NamespaceEntry", back_populates="namespace")


class NamespaceEntry(Base, MasterModel):
    """Represents a name within a BEL namespace."""

    __tablename__ = "namespace_entry"
    __table_args__ = (Index("idx_name", "name", mysql_length=100),)

    name = Column(String(2048, collation="utf8_bin"), nullable=True)
    encoding = Column(String(8), nullable=True)

    namespace__id = foreign_key_to('namespace')
    namespace = relationship('Namespace', back_populates="entries")


class Annotation(Base, MasterModel):
    """Represents a BEL Annotation."""

    __tablename__ = "annotation"
    __table_args__ = (Index("idx_url2", "url", mysql_length=100),)

    url = Column(String(2048), nullable=False)
    keyword = Column(String(255, collation="utf8_bin"), index=True)
    cacheable = Column(Boolean)
    case_sensitive = Column(Boolean)

    entries = relationship("AnnotationEntry", back_populates="annotation", cascade="all, delete-orphan")


class AnnotationEntry(Base, MasterModel):
    """Represents a name within a BEL annotation."""

    __tablename__ = "annotation_entry"
    __table_args__ = (Index("idx_identifier", "identifier", mysql_length=100),)

    name = Column(String(2048, collation="utf8_bin"), nullable=True)
    identifier = Column(String(255, collation="utf8_bin"), nullable=True)

    annotation__id = foreign_key_to('annotation')
    annotation = relationship('Annotation', back_populates="entries")


class ModelManager:
    """Manager for all models - superclass."""

    def __init__(self, model, entries_model, grammar_start):
        """Init method."""
        self.grammar_start = grammar_start

        self.model = model
        self.entries_model = entries_model
        self.name = model.__tablename__

        self.urls = {}
        self.lists = {}

        self.session = BelRdb().session

        self.errors = []

    def get_entries_not_exists(self, keyword: str, url: str,
                               entry_line_column_list) -> List[Tuple[str, int, int, str]]:
        """Get entries in namespace or annotation linked to URL for entry_line_column_list(generator).

        Parameters
        ----------
        keyword : str
            Keyword.
        url : str
            URL string.
        entry_line_column_list : Generator[tuple]
            Generator of tuples with (entry:str , line: int, column: int).

        Returns
        -------
        List[Tuple[str, int, int, str]]
            List of tuples with entry, line, column, hint.

        """
        exists_cache = set()
        not_exists_cache = dict()

        names_not_exists = []

        search_for = self.session.query(self.model.id).filter(self.model.keyword == keyword, self.model.url == url)

        desc = 'Check BEL for {}: '.format(keyword)

        for entry, line, column in tqdm(list(entry_line_column_list), desc=desc, ncols=100):

            if entry in not_exists_cache:
                hint = not_exists_cache[entry]
                names_not_exists.append((entry, line, column, hint))

            elif (keyword, url, entry) not in exists_cache:

                exists = search_for.join(self.entries_model).filter(self.entries_model.name == entry).count()

                if exists:
                    exists_cache.update(set([(keyword, url, entry)]))
                else:
                    hint = ""
                    alternatives = self.session.query(
                        self.entries_model.name,
                        self.model.keyword,
                        self.model.url
                    ).join(self.model).filter(self.entries_model.name.like(entry)).all()

                    if alternatives:
                        hint = "Did you mean: "
                        hint += ", ".join([x[1] + ":\"" + x[0] + "\"(" + x[2] + ")" for x in alternatives])

                    else:
                        if len(entry) >= 6:
                            similars = self.session.query(
                                self.entries_model.name,
                                self.model.keyword
                            )\
                                .join(self.model)\
                                .filter(self.entries_model.name.like(entry[:-2] + "%"))\
                                .filter(func.length(self.entries_model.name) < len(entry) + 3)\
                                .limit(20)\
                                .all()

                            if similars:
                                hint = "Similar: "
                                hint += ", ".join([x[1] + ":\"" + x[0] + "\"" for x in set(similars)])

                    if not hint:
                        url_query_string = urlencode({'q': entry}, quote_via=quote_plus)
                        hint = "[OLS suggests](https://www.ebi.ac.uk/ols/search?%s)" % url_query_string

                    names_not_exists.append((entry, line, column, hint))
                    not_exists_cache[entry] = hint

        return names_not_exists

    @staticmethod
    def download_url(url: str) -> Tuple[bool, Union[Exception, str]]:
        """Short summary.

        Parameters
        ----------
        url : str
            Description of parameter `url`.

        Returns
        -------
        Tuple[bool, str]
            Description of returned object.

        """
        filename = os.path.basename(urllib.parse.urlparse(url).path)

        try:
            path_to_file = filename
            r = requests.get(url)
            r.raise_for_status()

            open(path_to_file, 'wb').write(r.content)

        except requests.exceptions.HTTPError as ex:
            return False, ex

        except requests.exceptions.ConnectionError as ex:
            return False, ex

        except FileNotFoundError as urlex:
            return False, f"{str(urlex)}\n{url} does not return a valid belns or belanno file"

        return True, path_to_file

    @staticmethod
    def get_namespace_header(file_path: str) -> Tuple[str, int]:
        """Return header and line number where header ends.

        Parameters
        ----------
        file_path : str
            path to namespace.

        Returns
        -------
        Tuple[str, int]
            header and line number where header ends.

        """
        header = ""
        ends_in_line = 0
        with codecs.open(file_path, 'r', encoding="utf-8") as fd:
            for line in fd:
                ends_in_line += 1
                if not re.search(r"^[ \t]*(\[Values\])\s*(\r\n|\r|\n)", line):
                    header += line
                else:
                    break
        return header, ends_in_line

    def save_from_url_or_path(self, keyword: str, url_or_path: str, doc_type: str):
        """Short summary.

        Parameters
        ----------
        keyword : str
            Description of parameter `keyword`.
        url_or_path : str
            Description of parameter `url_or_path`.
        doc_type : str
            Description of parameter `doc_type`.

        Returns
        -------
        type
            Description of returned object.

        """
        path_to_file = None

        if doc_type == URL:

            downloaded, path_to_file_or_error = self.download_url(url_or_path)

            if not downloaded:
                error = path_to_file_or_error
                return False, error

            else:
                path_to_file = path_to_file_or_error

        elif doc_type == FILE:

            path_to_file = url_or_path

        saved, save_error = self.save_in_db(path_to_file=path_to_file, url=url_or_path, keyword=keyword)

        if doc_type == URL:
            os.remove(path_to_file)

        return saved, save_error

    def save_in_db(self, path_to_file: str, url: str, keyword: str) -> Tuple[bool, Optional[Exception]]:
        """Save content of namespace or annotation file from URL with keyword in database.

        Parameters
        ----------
        path_to_file : str
            Description of parameter `path_to_file`.
        url : str
            Description of parameter `url`.
        keyword : str
            Description of parameter `keyword`.

        Returns
        -------
        type
            Description of returned object.
        """
        grammar = parser.load_grammar(GRAMMAR_NS_ANNO_PATH)
        header, header_ends_in_line = self.get_namespace_header(path_to_file)
        lark_parser = Lark(grammar, start=self.grammar_start)

        try:
            tree = lark_parser.parse(header)

        except Exception as e:
            return False, e

        delimiter = parser.first_token_value(tree, 'pr_delimiter_string')
        case_sensitive = parser.first_token_value(tree, 'pr_case_sensitive_flag')
        cacheable = parser.first_token_value(tree, 'pr_cacheable_flag')
        is_case_sensitive = False if re.search("no", case_sensitive, re.I) else False
        is_cacheable = False if re.search("no", cacheable, re.I) else True

        keyword_in_anno = parser.first_token_value(tree, 'keyword')
        if keyword != keyword_in_anno:
            warning = f"Keyword {keyword} in BEL namespace URL {url} is different from keyword in BEL script"
            logger.warning(warning)
            # ToDo save in Error classes
            self.errors += [warning]

        model_instance = self.model(url=url,
                                    keyword=keyword,
                                    cacheable=is_cacheable,
                                    case_sensitive=is_case_sensitive)
        self.session.add(model_instance)
        self.session.commit()

        table_name = self.name + '_entry'
        second = {'annotation': 'identifier', 'namespace': 'encoding'}
        second_column = second[self.name]

        df = pd.read_csv(path_to_file,
                         delimiter=delimiter,
                         skip_blank_lines=True,
                         skiprows=header_ends_in_line,
                         names=['name', second_column]
                         )
        df[self.name + '__id'] = model_instance.id
        df.set_index(['name', second_column], inplace=True)

        logger.info(f"Import `{keyword}` table '{table_name}' of engine '{self.session.bind.engine}'")

        df.to_sql(table_name, self.session.bind.engine, if_exists="append", chunksize=1000)
        self.session.commit()
        return True, None

    def keyword_url_exists(self, keyword: str, url: str) -> bool:
        """Check if keyword or annotation exists in the database.

        Parameters
        ----------
        keyword : type
            Description of parameter `keyword`.
        url : type
            Description of parameter `url`.

        Returns
        -------
        type
            Description of returned object.

        """
        result = self.session.query(self.model).filter(
            self.model.keyword == keyword,
            self.model.url == url)

        if result.count() == 0:
            exists = False

        else:
            exists = True
            ns_or_anno = result.one()
            if ns_or_anno.cacheable is False:
                self.session.delete(ns_or_anno)
                self.session.commit()
                exists = False

        return exists


class NamespaceManager(ModelManager):
    """Manager for namespaces."""

    def __int__(self, session_obj):
        """Init method."""
        super(NamespaceManager, self).__int__(model=Namespace,
                                              entries_model=NamespaceEntry,
                                              grammar_start=GRAMMAR_START_NS)


class AnnotationManager(ModelManager):
    """Manager for annotations."""

    def __int__(self, session_obj):
        """Init method."""
        super(AnnotationManager, self).__int__(model=Annotation,
                                               entries_model=AnnotationEntry,
                                               grammar_start=GRAMMAR_START_ANNO)
