"""Collection of methods for handling information caching."""
import re
import logging
import getpass
import pymysql

from lark.lexer import Token
from collections import defaultdict, Counter
from typing import Generator, List, Dict, DefaultDict, Set

from ebel import defaults
from ebel.manager import models
from ebel.tools import BelRdb
from ebel.config import write_to_config
from ebel.warnings import AlsoUsedInOtherNamespace, _Warning
from ebel.constants import URL, PATTERN, LIST, ALLOWED_TYPES
from ebel.constants import GRAMMAR_START_NS, GRAMMAR_START_ANNO
from ebel.errors import NotInNamespaceUrl, NotInAnnotationUrl, WithoutDefinedNamespace, \
    WithoutDefinedAnnotation, NotInNamespaceList, NotInAnnotationList, \
    NotInNamespacePattern, NotInAnnotationPattern, NotDownloadedFromUrl, _Error

# TODO: Because of change of `BelScript.ALLOWED_TYPES` FILE have to be handled on different way

logger = logging.getLogger(__name__)


def set_mysql_interactive() -> tuple:
    """Interactive mode to setup MySQL database."""
    print("Interactive mode\n \
          ================\n \
          1st setup of db and user with root:\n")
    host = input("host[localhost]:") or 'localhost'
    user = input("ebel user[ebel]:") or 'ebel'
    password = getpass.getpass(prompt="ebel password[ebel]:") or 'ebel'
    db = input("database name[ebel]") or 'ebel'
    print("If you want to setup the database automatically,\n \
          then type in the root password, otherwise nothing")
    root_pwd = getpass.getpass(prompt='root password (only for 1st setup):')

    if root_pwd:
        root_host = getpass.getpass(prompt='IP or name mysql server [localhost]:') or 'localhost'
        conn = pymysql.connect(host=root_host, user="root", password=root_pwd)
        c = conn.cursor()
        db_exists = c.execute("show databases like '{}'".format(db))

        if not db_exists:
            c.execute("CREATE DATABASE {} CHARACTER SET utf8 COLLATE utf8_bin".format(db))

        else:
            logger.warning(f"Database '{db}' already exists!")

        user_exists = c.execute("Select 1 from mysql.user where User='{}'".format(user))

        if not user_exists:
            sql = "CREATE USER '{}'@'{}' IDENTIFIED BY '{}'".format(
                user,
                host,
                password,
            )
            c.execute(sql)
        else:
            logger.warning(f"Database '{db}' already exists!")

        privileges_exists = c.execute("Select 1 from mysql.db where User='{}' and Db='{}'".format(user, db))
        if not privileges_exists:
            c.execute("GRANT ALL PRIVILEGES ON {}.* TO '{}'@'%'  IDENTIFIED BY '{}'".format(db, user, password))
        else:
            logger.warning(f"User already has privileges for database '{db}'")

        c.execute("FLUSH PRIVILEGES")

    return host, user, password, db


def set_mysql_connection(host: str = 'localhost',
                         user: str = 'ebel_user',
                         password: str = 'ebel_passwd',
                         db: str = 'ebel',
                         charset: str = 'utf8mb4'):
    """Set the connection using MySQL Parameters.

    Parameters
    ----------
    host : str
        MySQL database host.
    user : str
        MySQL database user.
    password : str
        MySQL database password.
    db : str
        MySQL database name.
    charset : str
        MySQL database charset.

    Returns
    -------
    str
        SQLAlchemy MySQL connection string.

    """
    connection_string = 'mysql+pymysql://{user}:{passwd}@{host}/{db}?charset={charset}'.format(
        host=host,
        user=user,
        passwd=password,
        db=db,
        charset=charset)
    set_connection(connection_string)

    return connection_string


def set_always_create_new_db(always_create_new_db: bool = True) -> None:
    """Set in configuration option `always_create_new_db`.

    Parameters
    ----------
    always_create_new_db : bool
        Option `always_create_new_db` in section `database` in config file.

    """
    write_to_config('database', 'always_create_new', str(always_create_new_db))


def set_connection(connection: str = defaults.CONN_STR_DEFAULT) -> None:
    """Set the connection string for SQLAlchemy.

    Parameters
    ----------
    connection: str
        SQLAlchemy connection string.

    """
    write_to_config('database', 'sqlalchemy_connection_string', connection)


class _BelScript:
    """Cache the content of the BEL script and methods to find errors and warnings."""

    def __init__(self, force_new_db):
        """Init."""
        # setup database
        engine = BelRdb().engine

        self.force_new_db = force_new_db
        models.reset_tables(engine, self.force_new_db)

        self._namespaces = Namespaces()  # entries Namespace objects
        self._annotations = Annotations()  # entries Annotation objects

        self.__namespace_in_db_updated = False
        self.__annotations_in_db_updated = False

        self._namespace_entries = NamespaceEntries()
        self._annotation_entries = AnnotationEntries()

        self.notDownloadedFromUrls = []

        self.namespace_manager = models.NamespaceManager(
            model=models.Namespace,
            entries_model=models.NamespaceEntry,
            grammar_start=GRAMMAR_START_NS
        )

        self.annotation_manager = models.AnnotationManager(
            model=models.Annotation,
            entries_model=models.AnnotationEntry,
            grammar_start=GRAMMAR_START_ANNO
        )

    def set_namespace_definition(self, as_type, keyword, value):
        """Set an annotation definition with type, keyword and value value could be 'file', 'url' or 'list'.

        :param str as_type: 'file', 'url' or 'list'
        :param str keyword: namespace keyword
        :param str value: URL, file path or list
        """
        if as_type in ALLOWED_TYPES:
            self._namespaces.add(as_type, keyword, value)
            return True
        else:
            logger.error("{} is not a allowed type of {}".format(as_type, ALLOWED_TYPES))
            return False

    def set_annotation_definition(self, as_type, keyword, value):
        """Set an annotation definition with type, keyword and value could be 'file', 'url' or 'list'.

        :param str as_type: 'file', 'url' or 'list'
        :param str keyword: namespace keyword
        :param str value: URL, file path or list
        """
        if as_type in ALLOWED_TYPES:
            self._annotations.add(as_type, keyword, value)
            return True
        else:
            logger.error("{} is not an allowed type of {}".format(as_type, ALLOWED_TYPES))
            return False

    def set_annotation_entry(self, annotation: str, entry: str, token: Token):
        """Set annotation, entry and lark.lexer.Token token.

        :param str annotation: annotation
        :param str entry: entry
        :param lark.lexer.Token token:
        """
        self._annotation_entries.set_annotation_entry(keyword=annotation, entry=entry, token=token)

    def set_namespace_entry(self, namespace: str, entry: str, token: Token):
        """Set namespace, entry and lark.lexer.Token token.

        :param str namespace:
        :param str entry:
        :param lark.lexer.Token token:
        """
        if not isinstance(token, Token):
            raise Exception("expecting Token in cache.set_namespace_entry")

        self._namespace_entries.set_namespace_entry(keyword=namespace, entry=entry, token=token)

    @property
    def errors(self) -> List[_Error]:
        """Execute all methods to find errors and warnings."""
        self.update_database()

        # all errors are children from errors._Error instances
        return (self.notDownloadedFromUrls
                + self.entries_without_namespace
                + self.entries_without_annotation
                + self.entries_not_in_namespace_url
                + self.entries_not_in_annotation_url
                + self.entries_not_in_namespace_list
                + self.entries_not_in_annotation_list
                + self.entries_not_in_namespace_pattern
                + self.entries_not_in_annotation_pattern
                )

    @property
    def warnings(self) -> List[_Warning]:
        """Execute all methods to find warnings."""
        if not (self.__namespace_in_db_updated and self.__annotations_in_db_updated):
            self.update_database()

        # all warnings are children from warnings._Warning instances
        return self.entries_also_in_other_namespace

    @property
    def entries_also_in_other_namespace(self) -> List[AlsoUsedInOtherNamespace]:
        """Return WithoutDefinedNamespace list."""
        ret = []
        # extract all entries used in BEL statements and create a dict of lower entries with all keywords
        entry_keyword_dict = defaultdict(set)
        for keyword1, entries in self._namespace_entries.entries.items():
            for entry in entries:
                entry_keyword_dict[entry.lower()] |= {keyword1}
        # identify all ambiguous entries (in more than 1 namespace)
        ambiguous_entries = {entry: keywords for entry, keywords in entry_keyword_dict.items() if len(keywords) > 1}

        # ToDo: iterate all lower entries an check for permutation
#        for lower_entry in entry_keyword_dict:
#            if lower_entry.count(",") == 1:
#                reverse_without_comma = " ".join([x.strip() for x in lower_entry.split(",")][::-1])
#                if reverse_without_comma in entry_keyword_dict:
#                    print(lower_entry,
        #                    "%s exists in %s" % (reverse_without_comma,
        #                    entry_keyword_dict[reverse_without_comma]))
#                    ret.append(AlsoUsedInOtherNamespace(keyword=keyword2,
#                                                        entry=entry,
#                                                        line_number=token.line,
#                                                        column=token.column,
#                                                        hint=hint))

        # iterate all tokens with namespace entries and check if they are also exists in ambiguous entries
        for keyword2, entries_tokens in self._namespace_entries.tokens.items():
            for entry, tokens in entries_tokens.items():
                if entry.lower() in ambiguous_entries:
                    ambiguous_tokens = self._namespace_entries.tokens[keyword2][entry]
                    for token in ambiguous_tokens:
                        hint = "%s exists also in %s" % (entry, ambiguous_entries[entry.lower()] - {keyword2})
                        ret.append(AlsoUsedInOtherNamespace(keyword=keyword2,
                                                            entry=entry,
                                                            line_number=token.line,
                                                            column=token.column,
                                                            hint=hint))
        return ret

    @property
    def entries_not_in_namespace_pattern(self) -> List[NotInNamespacePattern]:
        """Return a list of entries not fitting a given namespace pattern."""
        ret = []

        ns_pattern_kwds = self.used_namespace_keywords & self._namespaces.keywords_by_type(PATTERN)

        for kwd in ns_pattern_kwds:
            regex = self._namespaces.keyword_dict[kwd].value
            pattern = re.compile("^" + regex + "$")
            elcs = self._namespace_entries.get_entry_line_column_list_by_keyword(kwd)
            for entry, line, column in elcs:
                if not pattern.search(entry):
                    ret.append(NotInNamespacePattern(keyword=kwd,
                                                     entry=entry,
                                                     line_number=line,
                                                     column=column))
        return ret

    @property
    def entries_not_in_annotation_pattern(self) -> List[NotInAnnotationPattern]:
        """Return a list of entries not fitting a given annotation pattern."""
        ret = []

        anno_pattern_kwds = self.used_annotation_keywords & self._annotations.keywords_by_type(PATTERN)

        for kwd in anno_pattern_kwds:
            regex = self._annotations.keyword_dict[kwd].value
            pattern = re.compile("^" + regex + "$")
            elcs = self._annotation_entries.get_entry_line_column_list_by_keyword(kwd)
            for entry, line, column in elcs:
                if not pattern.search(entry):
                    ret.append(NotInAnnotationPattern(keyword=kwd,
                                                      entry=entry,
                                                      line_number=line,
                                                      column=column))
        return ret

    @property
    def entries_not_in_annotation_list(self) -> List[NotInAnnotationList]:
        """Return a list of entries not in a given annotations."""
        ret = []

        anno_kwd_used_and_as_list = self.used_annotation_keywords & self._annotations.keywords_by_type(LIST)

        for kwd in anno_kwd_used_and_as_list:
            elcs = self._annotation_entries.get_entry_line_column_list_by_keyword(kwd)
            for entry, line, column in elcs:
                if entry not in self._annotations.keyword_dict[kwd].value:
                    ret.append(NotInAnnotationList(keyword=kwd,
                                                   entry=entry,
                                                   line_number=line,
                                                   column=column))
        return ret

    @property
    def entries_not_in_namespace_list(self) -> List[NotInNamespaceList]:
        """Return a list of entries not in a given namespace."""
        ret = []

        ns_kwd_used_and_as_list = self.used_namespace_keywords & self._namespaces.keywords_by_type(LIST)

        for kwd in ns_kwd_used_and_as_list:
            elcs = self._namespace_entries.get_entry_line_column_list_by_keyword(kwd)
            for entry, line, column in elcs:
                if entry not in self._namespaces.keyword_dict[kwd].value:
                    ret.append(NotInNamespaceList(keyword=kwd,
                                                  entry=entry,
                                                  line_number=line,
                                                  column=column))
        return ret

    @property
    def entries_without_namespace(self) -> List[WithoutDefinedNamespace]:
        """Return WithoutDefinedNamespace list."""
        ret = []
        for namespace_keyword in self.namespaces_without_definition:
            elcs = self._namespace_entries.get_entry_line_column_list_by_keyword(namespace_keyword)
            for entry, line, column in elcs:
                ret.append(WithoutDefinedNamespace(keyword=namespace_keyword,
                                                   entry=entry,
                                                   line_number=line,
                                                   column=column))
        return ret

    @property
    def entries_without_annotation(self) -> List[WithoutDefinedAnnotation]:
        """Return WithoutDefinedNamespace list."""
        ret = []
        for annotation_keyword in self.annotations_without_definition:
            elcs = self._annotation_entries.get_entry_line_column_list_by_keyword(annotation_keyword)
            for entry, line, column in elcs:
                ret.append(WithoutDefinedAnnotation(keyword=annotation_keyword,
                                                    entry=entry,
                                                    line_number=line,
                                                    column=column))
        return ret

    def update_database(self) -> None:
        """Update namespace and annotation entries in database if not exists by url and keyword."""
        if not (self.__namespace_in_db_updated and self.__annotations_in_db_updated):
            self.__namespace_in_db_updated = self.update_namespaces_in_db()
            self.__annotations_in_db_updated = self.update_annotations_in_db()

    def set_entry_not_in_namespace_list_errors(self):
        pass

    def set_entry_not_in_annotation_list_errors(self):
        pass

    @property
    def entries_not_in_namespace_url(self) -> List[NotInNamespaceUrl]:
        """Return a list of entries not exists in namespaces referenced as URL.

        Returns
        -------
        List[NotInNamespaceUrl]
            Description of returned object.
        """
        entries_not_in_namespace = []

        for keyword in self.used_namespace_keywords:

            namespace = self._namespaces.keyword_dict[keyword]

            if namespace.as_type == URL:

                url = namespace.value
                elc_list = self._namespace_entries.get_entry_line_column_list_by_keyword(keyword)

                names_not_exists = self.namespace_manager.get_entries_not_exists(
                    keyword=keyword,
                    url=url,
                    entry_line_column_list=elc_list,
                )

                for entry, line, column, hint in names_not_exists:
                    error = NotInNamespaceUrl(
                        keyword=keyword,
                        url_or_path=url,
                        entry=entry,
                        line_number=line,
                        column=column,
                        hint=hint
                    )
                    entries_not_in_namespace.append(error)

        return entries_not_in_namespace

    @property
    def entries_not_in_annotation_url(self) -> List[_Error]:
        """Return a list of entries not in the annotation URL."""
        entries_not_in_annotation = []

        for keyword in self.used_annotation_keywords:

            annotation = self._annotations.keyword_dict[keyword]

            if annotation.as_type == URL:

                url = annotation.value
                elc_list = self._annotation_entries.get_entry_line_column_list_by_keyword(keyword)

                names_not_exists = self.annotation_manager.get_entries_not_exists(
                    keyword=keyword,
                    url=url,
                    entry_line_column_list=elc_list
                )

                for entry, line, column, hint in names_not_exists:
                    error = NotInAnnotationUrl(
                        keyword=keyword,
                        url_or_path=url,
                        entry=entry,
                        line_number=line,
                        column=column,
                        hint=hint
                    )
                    entries_not_in_annotation.append(error)
        return entries_not_in_annotation

    def update_annotations_in_db(self) -> bool:
        """Update annotation in database if URL and keyword not exists."""
        import_success = True
        for anno in self._annotations.to_update:

            if anno.keyword in self.used_annotation_keywords:

                if not self.annotation_manager.keyword_url_exists(keyword=anno.keyword, url=anno.value):

                    if anno.as_type == URL:

                        logger.info(f"Update db with annotation {anno.keyword}: download from {anno.value}")

                        successful, error = self.annotation_manager.save_from_url_or_path(
                            keyword=anno.keyword,
                            url_or_path=anno.value,
                            doc_type=anno.as_type,
                        )

                        if not successful:
                            import_success = False
                            error_args = error.args[0].split("\n")
                            string_error = error_args[2] if len(error_args) > 1 else error_args[0]
                            logger.error(f"Annotation {anno.keyword} failed to be added from {anno.value}",
                                         exc_info=False)

                            if "column" in dir(error):  # Indicates it's a Lark error
                                download_error = NotDownloadedFromUrl(
                                    keyword=anno.keyword,
                                    url_or_path=anno.value,
                                    column=error.column,
                                    line=error.line,
                                    hint=f'{error.allowed} error in "{string_error}"'
                                )

                            else:  # It's an HTTPError of some kind
                                download_error = NotDownloadedFromUrl(
                                    keyword=anno.keyword,
                                    url_or_path=anno.value,
                                    column=0,
                                    line=0,
                                    hint=f"{string_error}"
                                )
                            self.notDownloadedFromUrls.append(download_error)

        return import_success

    def update_namespaces_in_db(self) -> bool:
        """Update namespaces in database if URL and keyword does not exist."""
        import_success = True
        for ns in self._namespaces.to_update:

            if ns.keyword in self.used_namespace_keywords:

                if not self.namespace_manager.keyword_url_exists(keyword=ns.keyword, url=ns.value):

                    if ns.as_type == URL:

                        logger.info(f"Update db with namespace {ns.keyword}: download from {ns.value}")

                        successful, error = self.namespace_manager.save_from_url_or_path(
                            keyword=ns.keyword,
                            url_or_path=ns.value,
                            doc_type=ns.as_type,
                        )

                        if not successful:
                            import_success = False
                            error_args = error.args[0].split("\n")
                            string_error = error_args[2] if len(error_args) > 1 else error_args[0]
                            logger.error(f"Namespace {ns.keyword} failed to be added from {ns.value}",
                                         exc_info=False)

                            if "column" in dir(error):  # Indicates it's a Lark error
                                download_error = NotDownloadedFromUrl(
                                    keyword=ns.keyword,
                                    url_or_path=ns.value,
                                    column=error.column,
                                    line=error.line,
                                    hint=f'{error.allowed} error in "{string_error}"'
                                )

                            else:  # It's an HTTPError of some kind
                                download_error = NotDownloadedFromUrl(
                                    keyword=ns.keyword,
                                    url_or_path=ns.value,
                                    column=0,
                                    line=0,
                                    hint=f"{string_error}"
                                )

                            self.notDownloadedFromUrls.append(download_error)

        return import_success

    @property
    def namespaces_with_multiple_definitions(self):
        """Return all Namespace objects with several definitions.

        This is returned as a dictionary (key:keyword, value: list of Namespace objects).
        """
        ret = defaultdict(list)
        multiple_keyword = [k for k, v in Counter(self._namespaces.keywords).items() if v > 1]
        for ns in self._namespaces:
            if ns.keyword in multiple_keyword:
                ret[ns.keyword].append(ns)
        return dict(ret)

    @property
    def annotations_with_multiple_definitions(self):
        """Return all Annotation objects with several definitions.

        This is returned as a dictionary (key:keyword, value: list of Annotation objects).
        """
        ret = defaultdict(list)
        multiple_keyword = [k for k, v in Counter(self._annotations.keywords).items() if v > 1]
        for anno in self._annotations:
            if anno.keyword in multiple_keyword:
                ret[anno.keyword].append(anno)
        return dict(ret)

    @property
    def namespaces_without_definition(self):
        """Return set of namespace keywords used in statements but not defined with a reference.

        :return set: set of str
        """
        return set(self._namespace_entries.keywords) - set(self._namespaces.keywords)

    @property
    def annotations_without_definition(self):
        """Return a set of annotation keywords not defined with a reference.

        :return set: set of str
        """
        return set(self._annotation_entries.keywords) - set(self._annotations.keywords)

    @property
    def used_namespace_keywords(self) -> Set[str]:
        """Return set of used namespace keywords (with reference and used in statements)."""
        return set(self._namespace_entries.keywords) & set(self._namespaces.keywords)

    @property
    def used_annotation_keywords(self) -> Set[str]:
        """Return set of used namespace keywords."""
        return set(self._annotation_entries.keywords) & set(self._annotations.keywords)

    @property
    def namespace_keywords_in_statements(self):
        """Return all unique namespace keywords used in statements."""
        return self._namespace_entries.keywords

    @property
    def annotation_keywords_in_statements(self):
        """Return all unique annotation keywords used in statements."""
        return self._namespace_entries.keywords

    def get_entries_by_namespace_keyword(self, keyword):
        """Get all entries by namespace keyword.

        :param keyword: namespace keyword
        :return set: all entries in the namespace
        """
        return self._namespace_entries.get_entries_by_keyword(keyword)

    def get_entries_by_annotation_keyword(self, keyword):
        """Get all entries by namespace keyword.

        :param keyword: namespace keyword
        :return set: all entries in the namespace
        """
        return self._annotation_entries.get_entries_by_keyword(keyword)


class Entries:
    """Abstract class representing namespaces and annotations."""

    tokens = defaultdict(dict)
    entries = defaultdict(set)

    def get_entry_line_column_list_by_keyword(self, keyword: str) -> Generator[str, int, int]:
        """Get generator of tuple(entry, line, column) by keyword.

        Parameters
        ----------
        keyword: str
            Description of parameter `keyword: str`.

        Returns
        -------
        Generator
            Generator of tuple(entry: str, line: int, column: int).
        """
        for entry, tokens in self.tokens[keyword].items():
            for token in tokens:
                yield entry, token.line, token.column

    @property
    def keywords(self):
        """Return a list of unique keywords used in SETs."""
        return self.entries.keys()

    def get_entries_by_keyword(self, keyword: str) -> Set:
        """Get entries by keyword.

        :param str keyword: keyword to retrieve from dict
        """
        return self.entries.get(keyword, set())

    def get_tokens_by_keyword(self, keyword: str) -> Dict:
        """Get tokens by keyword.

        :param str keyword: keyword to retrieve from dict
        """
        return self.entries.get(keyword, set())

    def __str__(self):
        """String representation of object."""
        return str(dict(self.tokens))


class NamespaceEntries(Entries):
    """Namespace subclass of Entries."""

    def __init__(self):
        """Init."""
        self.entries = defaultdict(set)
        self.tokens = defaultdict(dict)

    def set_namespace_entry(self, keyword, entry, token):
        """Set namespace,  entry and lark.lexer.Token.

        :param str keyword: namespace
        :param str entry: entry
        :param lark.lexer.Token token: Token object from lark library
        """
        if isinstance(token, Token):
            self.entries[keyword] |= {entry}
            if keyword in self.tokens and entry in self.tokens[keyword]:
                self.tokens[keyword][entry].append(token)
            else:
                self.tokens[keyword][entry] = [token]
        else:
            raise "Argument token is type {} not {}".format(type(token), 'lark.lexer.Token')


class AnnotationEntries(Entries):
    """Annotation subclass of Entries."""

    def __init__(self):
        """Init."""
        self.entries = defaultdict(set)
        self.tokens = defaultdict(dict)

    def set_annotation_entry(self, keyword: str, entry, token):
        """Set annotation,  entry and lark.lexer.Token.

        :param str keyword: annotation
        :param entry: entry
        :param lark.lexer.Token token: Token object from lark library
        """
        if isinstance(token, Token):
            self.entries[keyword] |= {entry}
            if keyword in self.tokens and entry in self.tokens[keyword]:
                self.tokens[keyword][entry].append(token)
            else:
                self.tokens[keyword][entry] = [token]
        else:
            raise "argument token is type {} not {}".format(type(token), 'lark.lexer.Token')


class NsAnsBase:
    """Parent class for class Namespace and Annotation."""

    def __init__(self, obj_class):
        """Init."""
        self.__objs = []
        self.class_ = obj_class

    def add(self, as_type: str, keyword: str, value: str):
        """Add obj to list of objs.

        :param str as_type: allowed keywords 'file', 'url' or 'list'
        :param str keyword: keyword used in object
        :param str value: value of object
        :return:
        """
        obj = self.class_(as_type, keyword, value)
        self.__objs.append(obj)

    @property
    def type_dict(self) -> DefaultDict:
        """Convert to list of dictionaries."""
        ret = defaultdict(list)
        [ret[obj.as_type].append(obj) for obj in self]
        return ret

    def by_type(self, as_type: str):
        """Return list of Namespace objects by 'list', 'url' or 'file'."""
        if as_type not in ALLOWED_TYPES:
            raise "{} not in allowed types {}".format(as_type, ALLOWED_TYPES)
        return [obj for obj in self if obj.as_type == as_type]

    def keywords_by_type(self, as_type: str) -> Set[str]:
        """Return a set of keywords by Namespace type 'list', 'url' or 'file'."""
        if as_type not in ALLOWED_TYPES:
            raise "{} not in allowed types {}".format(as_type, ALLOWED_TYPES)
        return set([obj.keyword for obj in self if obj.as_type == as_type])

    @property
    def keyword_dict(self) -> Dict:
        """Return a dictionary of key=keyword, value: Namespace or Annotation object."""
        ret = dict()
        for obj in self:
            ret[obj.keyword] = obj
        return ret

    @property
    def keywords(self) -> List[str]:
        """Return all keywords."""
        return [obj.keyword for obj in self.__objs]

    @property
    def to_update(self) -> List:
        """Return a list of all Namespace or Annotation (NS_or_Anno) objects with URL or file path.

        :return list: list of all Namespace or Annotation (NS_or_Anno) objects with URL or file path
        """
        return self.type_dict[URL]

    def __iter__(self):
        """Return a generator of objects (Namespace or Annotation)."""
        for obj in self.__objs:
            yield obj


class Namespaces(NsAnsBase):
    """Namespace child class."""

    def __init__(self):
        """init."""
        super(Namespaces, self).__init__(obj_class=Namespace)


class Annotations(NsAnsBase):
    """Annotation child class."""

    def __init__(self):
        """init."""
        super(Annotations, self).__init__(obj_class=Annotation)


class Namespace:
    """Namespace class to represent BEL statement namespaces."""

    def __init__(self, as_type, keyword, value):
        """Namespace init."""
        self.as_type = as_type
        self.keyword = keyword
        self.value = value

    def to_dict(self):
        """Convert class values to dictionary."""
        return {'as_type': self.as_type, 'keyword': self.keyword, 'value': self.value}

    def __unicode__(self):
        return "Namespace:" + str(self.to_dict())

    def __str__(self):
        return self.__unicode__()


class Annotation:
    """Annotation class to represent BEL statement annotations."""

    def __init__(self, as_type, keyword, value):
        """Annotation init."""
        self.as_type = as_type
        self.keyword = keyword
        self.value = value

    def to_dict(self):
        """Convert class values to dictionary."""
        return {'as_type': self.as_type, 'keyword': self.keyword, 'value': self.value}

    def __unicode__(self):
        return "Annotation" + str(self.to_dict())

    def __str__(self):
        return self.__unicode__()
