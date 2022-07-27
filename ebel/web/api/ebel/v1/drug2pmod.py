"""Custom drug2pmod API methods."""

import re
from collections import namedtuple, defaultdict
from math import ceil
from typing import List, Union

from flask import request

from ebel import Bel
from ebel.web.api.ebel.v1 import OrientDbSqlOperator, DataType

SQL_MATCH_TEMPLATE = """
    match {{class:drug, as:drug{drug}}}
    .outE('has_drug_target'){{as: has_drug_target{has_drug_target}}}
    .inV(){{class:protein, as:drug_target{drug_target}}}
    .outE('bel_relation', 'has_ppi_bg', 'has_ppi_kg'){{as:drug_target_to_target{drug_target_to_target}}}
    .inV(){{class:protein, as: target{target}}}-has__pmod->
    {{class:pmod, as:pmod{pmod}}}"""


class Column:
    """Column class."""

    def __init__(self,
                 odb_class: str,
                 form_name: str,
                 column: str,
                 sql_operator: OrientDbSqlOperator = OrientDbSqlOperator.EQUALS,
                 data_type: DataType = DataType.STRING):
        """Init method."""
        self.odb_class = odb_class
        self.column = column
        self.display_column = column + ".asString()" if "@" in column else column
        self.sql_operator = sql_operator
        self.form_name = form_name
        self.data_type = data_type
        self.value = None

    def set_search_term(self, value: Union[str, None]):
        """Get the value of a given search term."""
        if value is not None and value.strip():
            self.value = value.strip()
            if '%' not in self.value and self.sql_operator == OrientDbSqlOperator.LIKE:
                self.sql_operator = OrientDbSqlOperator.EQUALS


Pagination = namedtuple('Pagination', ['page', 'page_size', 'skip'])


class Query:
    """Query class for drug2pmod algorithm."""

    def __init__(self, columns: List[Column]):
        """Init method for algorithm."""
        self.columns: List[Column] = columns
        self.ebel = Bel()
        self.wheres_dict: dict = self.get_wheres_dict()

    def get_pagination(self) -> Pagination:
        """Return the results as a collection of paginations."""
        page_size = request.args.get('page_size', '10')
        page_size = int(page_size) if re.search(r"^\d+$", page_size) else 10
        page_size = 10 if page_size >= 100 else page_size
        page = request.args.get('page', '1')
        page = int(page) if re.search(r"^\d+$", page) else 1
        skip = (page - 1) * page_size
        return Pagination(page=page, page_size=page_size, skip=skip)

    def get_wheres_dict(self) -> dict:
        """Generate a generic filter SQL statement."""
        wheres = defaultdict(list)

        for col in self.columns:
            if col.value:
                if col.column.endswith('@rid') and "," in col.value:
                    rids = [x.strip() for x in col.value.split(",") if re.search(r"^#\d+:\d+$", x.strip())]
                    rids_str = "[" + ','.join(rids) + "]"
                    wheres[col.odb_class].append(f"{col.column} in {rids_str}")
                elif col.column != "@class":
                    value = col.value.replace('"', '\\"')

                    if col.data_type in [DataType.STRING, DataType.LIST_STRING]:
                        value = f'"{value}"'
                    else:
                        value = value

                    if col.data_type in [DataType.LIST_STRING, DataType.LIST_NUMBER, DataType.LIST_INTEGER]:
                        wheres[col.odb_class].append(f'{value} {col.sql_operator.value} {col.column}')
                    else:
                        wheres[col.odb_class].append(f'{col.column} {col.sql_operator.value} {value}')

        wheres_dict = {odb_class: '' for odb_class in {c.odb_class for c in self.columns}}
        for odb_class, col_queries in wheres.items():
            if col_queries:
                wheres_dict[odb_class] = ", where:( " + ' AND '.join(col_queries) + " )"

        return wheres_dict

    @property
    def sql(self) -> str:
        """Create the SQL statement."""
        sql = SQL_MATCH_TEMPLATE.format(**self.wheres_dict)
        return sql

    def get_number_of_results(self) -> int:
        """Count the number of results."""
        nodes_edges = ', '.join({c.odb_class for c in self.columns})
        sql = f"SELECT count(*) FROM ({self.sql} return {nodes_edges})"
        print(sql)
        return self.ebel.query_get_dict(sql)[0]['count']

    @property
    def __sql4results(self):
        cols = ', '.join([f"{c.odb_class}.{c.display_column} as {c.form_name}" for c in self.columns])
        return self.sql + " return " + cols

    def get_result(self) -> dict:
        """Return a dictionary of result metadata."""
        p = self.get_pagination()

        number_of_results = self.get_number_of_results()
        pages = ceil(number_of_results / p.page_size)

        results = []
        if number_of_results > 0:
            sql_paginated = self.__sql4results + f" skip {p.skip} limit {p.page_size}"
            results = [x for x in self.ebel.query_get_dict(sql_paginated)]

        return {
            'page': p.page,
            'page_size': p.page_size,
            'number_of_results': number_of_results,
            'pages': pages,
            'results': results}


def get_drug2pmod() -> dict:
    """Create a table of relations and information fulfilling the algorithm."""
    columns: List[Column] = [
        Column('drug', 'drug__cas_number', 'cas_number', OrientDbSqlOperator.LIKE),
        Column('drug', 'drug__description', 'description', OrientDbSqlOperator.LIKE),
        Column('drug', 'drug__drugbank_id', 'drugbank_id', OrientDbSqlOperator.LIKE),
        Column('drug', 'drug__indication', 'indication', OrientDbSqlOperator.LIKE),
        Column('drug', 'drug__label', 'label', OrientDbSqlOperator.LIKE),
        Column('drug', 'drug__mechanism_of_action', 'mechanism_of_action', OrientDbSqlOperator.LIKE),
        Column('drug', 'drug__metabolism', 'metabolism', OrientDbSqlOperator.LIKE),
        Column('drug', 'drug__pharmacodynamics', 'pharmacodynamics', OrientDbSqlOperator.LIKE),
        Column('drug', 'drug__toxicity', 'toxicity', OrientDbSqlOperator.LIKE),
        Column('has_drug_target', 'has_drug_target__action', 'action', OrientDbSqlOperator.LIKE),
        Column('has_drug_target', 'has_drug_target__known_action', 'known_action', OrientDbSqlOperator.LIKE),
        Column('drug_target', 'drug_target__name', 'name', OrientDbSqlOperator.LIKE),
        Column('drug_target', 'drug_target__bel', 'bel', OrientDbSqlOperator.LIKE),
        Column('drug_target', 'drug_target__label', 'label', OrientDbSqlOperator.LIKE),
        Column('drug_target', 'drug_target__uniprot', 'uniprot', OrientDbSqlOperator.LIKE),
        Column('drug_target', 'drug_target__reactome_pathways', 'reactome_pathways', OrientDbSqlOperator.IN,
               DataType.LIST_STRING),
        Column('drug_target_to_target', 'drug_target_to_target__relation', '@class', OrientDbSqlOperator.EQUALS),
        Column('drug_target_to_target', 'drug_target_to_target__evidence', 'evidence', OrientDbSqlOperator.LIKE),
        Column('drug_target_to_target', 'drug_target_to_target__pmid', 'pmid', OrientDbSqlOperator.LIKE),
        Column('drug_target_to_target', 'drug_target_to_target__citation', 'citation', OrientDbSqlOperator.LIKE),
        Column('target', 'target__name', 'name', OrientDbSqlOperator.LIKE),
        Column('target', 'target__bel', 'bel', OrientDbSqlOperator.LIKE),
        Column('target', 'target__label', 'label', OrientDbSqlOperator.LIKE),
        Column('target', 'target__uniprot', 'uniprot', OrientDbSqlOperator.LIKE),
        Column(
            'target', 'target__reactome_pathways', 'reactome_pathways', OrientDbSqlOperator.IN, DataType.LIST_STRING
        ),
        Column('pmod', 'pmod__amino_acid', 'amino_acid', OrientDbSqlOperator.LIKE),
        Column('pmod', 'pmod__name', 'name', OrientDbSqlOperator.LIKE),
        Column('pmod', 'pmod__namespace', 'namespace', OrientDbSqlOperator.LIKE),
        Column('pmod', 'pmod__position', 'position', OrientDbSqlOperator.LIKE),
        Column('pmod', 'pmod__type', 'type', OrientDbSqlOperator.LIKE),
        Column('pmod', 'pmod__bel', 'bel', OrientDbSqlOperator.LIKE)
    ]

    for column in columns:
        column.set_search_term(request.args.get(column.form_name))

    query = Query(columns)

    return query.get_result()
