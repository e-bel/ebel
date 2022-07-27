"""Base methods for API."""

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from typing import Dict, List, Union
from pymysql.converters import escape_string
from sqlalchemy_utils import create_database, database_exists

from ebel import Bel
from ebel.tools import _get_connection_string


class RDBMS:
    """Representation of the RDBMS."""

    engine = None
    session = None

    @staticmethod
    def get_engine():
        """Return the RDBMS engine."""
        if not RDBMS.engine:
            RDBMS.engine = create_engine(_get_connection_string())
        return RDBMS.engine

    @staticmethod
    def get_session():
        """Return the RDBMS session."""
        if not RDBMS.session:
            engine = RDBMS.get_engine()
            if not database_exists(engine.url):
                create_database(engine.url)

            RDBMS.session = Session(bind=engine, autocommit=True, autoflush=True)
        return RDBMS.session


class OdbRequest:
    """OrientDB class definition for interfacing with the ODB server."""

    def __init__(self, request_query_dict: Dict[str, Dict[str, Dict[str, Union[str, int, bool, float, None]]]]):
        """Init method."""
        self.__request_query_dict = request_query_dict
        if self.validate():
            self.__odb_classes = request_query_dict
        else:
            raise TypeError("RequestQuery must be initialized with Dict[str, Dict[str, Dict[str, str]]]")

    @property
    def odb_classes(self) -> Dict[str, Dict[str, Dict[str, Union[str, int, bool, float, None]]]]:
        """Return ODB classes: structure: {'odb_class', {'odb_column': {'option':str, 'value': str}, ...}}}."""
        return self.__odb_classes

    def validate(self):
        """Check if request_query_dict is correct."""
        validated: bool = False
        if isinstance(self.__request_query_dict, Dict):
            for odb_class, column_params in self.__request_query_dict.items():  # k=ODB class, v=columns
                if isinstance(odb_class, str) and isinstance(column_params, Dict):
                    for column_name, value_option_dict in column_params.items():
                        if isinstance(value_option_dict, Dict):
                            keywords_exists = {'value', 'option'}.issubset(set(value_option_dict.keys()))
                            value_types_ok = isinstance(value_option_dict['value'],
                                                        (str, int, bool, float, type(None)))
                            if keywords_exists and value_types_ok:
                                validated = True
        return validated


class TabColSelectSql:
    """Formatter for OrientDb SQL columns Select part."""

    def __init__(self, odbclass_columns_dict, with_rids: bool = True, with_class: bool = True):
        """Init method."""
        self.odbclass_columns_dict = odbclass_columns_dict
        self.with_rids = with_rids
        self.with_class = with_class

    def __str__(self):
        """Define string method."""
        return self.get_sql()

    def __unicode__(self):
        """Unicode definition."""
        return self.__str__()

    def get_sql(self):
        """Retrieve the SQL query."""
        sql_list = []
        sql_class = "{odb_class}.@class.asString() as {odb_class}__class"
        sql_rid = "{odb_class}.@rid.asString() as {odb_class}__rid"
        for odb_class, columns in self.odbclass_columns_dict.items():
            if self.with_rids:
                sql_list.append(sql_rid.format(odb_class=odb_class))
            if self.with_class:
                sql_list.append(sql_class.format(odb_class=odb_class))
            for column in columns:
                sql_list.append(f"{odb_class}.{column} as {odb_class}__{column.replace('.', '_')}")
        return ', '.join(sql_list)


class ValueOption:
    """Class for defining the different values in a table."""

    def __init__(self, value: Union[str, None], option: str):
        """Init method."""
        self.value = value
        self.option = option

    def get_operator_value_sql_string(self, dialect: Union[str, None] = None) -> Union[str, None]:
        """Get "operator value" part of a WHERE SQL statement.

        Option is translated to dialect specific Operator like 'exact' to '='. Value will be escaped.

        Future implementations:
        Possible dialects are m (MySQL), o (OrientDB) or None. If dialect is None
        no further checks will be performed. Not implemented in the moment.

        Parameters
        ----------
        dialect: str
            SQL dialect can be set as m (=MySQL), o (=OrientDB).

        Returns
        -------
        str
            Operator-Value string.
        """
        if self.value:
            if isinstance(self.value, str):
                search_value = escape_string(self.value.strip(), 'utf-8')

            else:
                search_value = self.value

            if self.option in ['=', 'exact']:
                operator = '='

            elif self.option == 'regular expression':
                operator = 'RLIKE'

            else:
                operator = 'LIKE'

            option_choices = {
                "exact": f"'{self.value}'",
                "contains": f"'%{self.value}%'",
                "starts with": f"'{self.value}%'",
                "ends with": f"'{self.value}%'",
                "regular expression": f"'{self.value}'"
            }

            if self.option in option_choices:
                search_value = option_choices[self.option]

            elif self.option in ['>', '>=', '<=', '<']:
                operator = self.option

            elif operator == "LIKE":
                search_value = f"'%{self.value}%'"

            return f"{operator} {search_value}"


def get_sql_match(odb_request: OdbRequest,
                  columns_dict: Dict[str, List[str]],
                  match_template: str) -> str:
    """Return an OrientDB match string.

    Example:
        - request_query_dict = {'class_name1': {'column1': {'option': 'exact', 'value': 'value1'}}, ...}
        - columns_dict = {'class_name1': ['column1', 'column2'], ...}
        - match_template:
            match {{ class: class_name1, as: class_name1 {class_name1} }}
            .outE(){{ class: class_name2, as: class_name2 {class_name2} }}
            .inV(){{ class: class_name3, as:class_name3 {class_name3} }}
        - return_value: match_template:
            match {{ class: class_name1, as: class_name1, where:(column1='value1') }}
            .outE(){{ class: class_name2, as: class_name2 {class_name2} }}
            .inV(){{ class: class_name3, as:class_name3 {class_name3} }}

    Parameters
    ----------
    odb_request : OdbRequest
        Description of parameter `request_query_dict`.
    columns_dict : Dict[str, List[str]]
        Description of parameter `columns_dict`.
    match_template : str
        Description of parameter `sql_match_template`.

    Returns
    -------
    str
        Description of returned object.
    """
    where_dict = {}
    for odb_class in columns_dict.keys():
        if odb_request.odb_classes.get(odb_class):
            where_array = []
            for column, values in odb_request.odb_classes[odb_class].items():
                if values['value']:
                    operator_value_string = ValueOption(**values).get_operator_value_sql_string()
                    if operator_value_string:
                        where_array.append(f"`{column}` {operator_value_string}")
            where_dict[odb_class] = ", where:(" + " and ".join(where_array) + ")" if where_array else ''

    sql_match = match_template.format(**where_dict)
    return sql_match


def get_odb_results(query_request: OdbRequest, class_column_dict: dict, sql_match_template: str):
    """Return OrientDB results for a given query."""
    query_get_dict = Bel().query_get_dict
    select_sql = TabColSelectSql(class_column_dict)
    sql_match = get_sql_match(query_request, class_column_dict, sql_match_template)

    query_string = f"""Select {select_sql}
        from
        ({sql_match}
        return {', '.join(class_column_dict.keys())})"""
    results = query_get_dict(query_string)

    return results


def get_odb_options(column: str, query_request: OdbRequest, class_column_dict, sql_match_template) -> List[str]:
    """Short summary.

    Returns
    -------
    List[str]
        Description of returned object.

    """
    client = Bel().client

    sql_match = get_sql_match(query_request, class_column_dict, sql_match_template)

    query_string = f"""Select distinct(option) as option
        from
        ({sql_match}
        return {column} as option) where option IS NOT NULL and option!='' order by option"""

    results = [str(x.oRecordData.get('option')) for x in client.command(query_string)]

    return results
