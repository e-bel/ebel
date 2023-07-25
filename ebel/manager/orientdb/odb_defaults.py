"""OrientDB defaults."""
from enum import Enum


class OIndexType(Enum):
    """Allowed OrientDB Index types."""

    NOTUNIQUE = 'notunique'
    UNIQUE = 'unique'
    FULLTEXT = 'fulltext'
    DICTIONARY = 'dictionary'
    UNIQUE_HASH_INDEX = 'unique_hash_index'
    NOTUNIQUE_HASH_INDEX = 'notunique_hash_index'
    FULLTEXT_HASH_INDEX = 'fulltext_hash_index'
    DICTIONARY_HASH_INDEX = 'dictionary_hash_index'


class ODataType(Enum):
    """Allowed OrientDB Data types."""

    BOOLEAN = 'BOOLEAN'
    BINARY = 'BINARY'
    BYTE = 'BYTE'
    DATE = 'DATE'
    DATETIME = 'DATETIME'
    DECIMAL = 'DECIMAL'
    DOUBLE = 'DOUBLE'
    EMBEDDED = 'EMBEDDED'
    EMBEDDEDLIST = 'EMBEDDEDLIST'
    EMBEDDEDSET = 'EMBEDDEDSET'
    EMBEDDEDMAP = 'EMBEDDEDMAP'
    FLOAT = 'FLOAT'
    INTEGER = 'INTEGER'
    LONG = 'LONG'
    LINK = 'LINK'
    LINKLIST = 'LINKLIST'
    LINKSET = 'LINKSET'
    LINKMAP = 'LINKMAP'
    LINKBAG = 'LINKBAG'
    STRING = 'STRING'
    SHORT = 'SHORT'
