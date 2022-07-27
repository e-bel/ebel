"""Essential API query methods."""

import json
import re
from collections import namedtuple
from enum import Enum
from math import ceil
from typing import Dict, Type
from typing import List

from flask import request
from sqlalchemy import inspect, not_
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm.query import Query

from ebel import Bel
from ebel.web.api import RDBMS

Pagination = namedtuple('Pagination', ['page', 'page_size', 'skip'])


class OrientDbSqlOperator(Enum):
    """String constant definitions."""

    EQUALS = "="
    LIKE = "like"
    IN = "in"
    STARTS_WITH = "like"
    ENDS_WITH = "like"
    CONTAINS = "like"


class DataType(Enum):
    """String constant definitions."""

    STRING = 1
    INTEGER = 2
    NUMBER = 3
    LIST_STRING = 4
    LIST_INTEGER = 5
    LIST_NUMBER = 6


class SubRelObj(Enum):
    """String constant definitions."""

    SUBJECT = 's'
    RELATION = 'r'
    OBJECT = 'o'


def _get_pagination() -> Pagination:
    """Get page and page_size from request."""
    request_obj = request.args if request.args else json.loads(request.data)
    page_size = request_obj.get('page_size', 10)
    page_size = int(page_size) if (isinstance(page_size, int) or re.search(r"^\d+$", page_size)) else 10
    page = request_obj.get('page', 1)
    page = int(page) if (isinstance(page, int) or re.search(r"^\d+$", page)) else 1
    skip = (page - 1) * page_size
    return Pagination(page=page, page_size=page_size, skip=skip)


def _get_data(model: Type[DeclarativeMeta], print_sql=False, order_by: List[InstrumentedAttribute] = []):
    columns: Dict[str, InstrumentedAttribute] = {
        col_name: col_obj for col_name, col_obj in model.__dict__.items()
        if isinstance(col_obj, InstrumentedAttribute)
    }
    bool_map = {'true': 1, 'false': 0}
    request_obj = request.args if request.args else json.loads(request.data)
    params = {k: (bool_map[v] if v in bool_map else v) for k, v in request_obj.items() if k in columns and v}
    like_queries = [columns[k].like(v) for k, v in params.items()]
    query = RDBMS.get_session().query(model).filter(*like_queries)
    return _get_paginated_query_result(query, print_sql=print_sql, order_by=order_by)


def _get_paginated_query_result(query: Query, return_dict=False, print_sql=False,
                                order_by: List[InstrumentedAttribute] = []):
    """Return paginated query result if sqlalchemy model have as_dict method.

    Method requires page_size and page in `request.args`
    """
    p = _get_pagination()

    if not (p.page and p.page_size):
        return {'error': "Please add page and page_size to your method."}

    number_of_results = query.count()
    limit = int(p.page_size)
    page = int(p.page)
    offset = (page - 1) * limit
    offset = offset if offset <= 100 else 100
    pages = ceil(number_of_results / limit)
    if order_by:
        for col in order_by:
            query = query.order_by(col)
    q = query.limit(limit).offset(offset)

    if print_sql:
        print(q.statement.compile(compile_kwargs={"literal_binds": True}))

    if return_dict:
        results = [row._asdict() for row in q.all()]
    else:
        results = [x.as_dict() for x in q.all()]

    return {
        'page': page,
        'page_size': limit,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': results
    }


def _get_paginated_ebel_query_result(sql: str, print_sql=False):
    """Return paginated ebel query result. Method requires page_size and page in `request.args`."""
    b = Bel()
    p = _get_pagination()

    if not (p.page and p.page_size):
        return {'error': "Please add page and page_size to your method."}

    number_of_results = b.query_get_dict(f"SELECT count(*) from ({sql})")[0]['count']
    limit = int(p.page_size)
    page = int(p.page)
    offset = (page - 1) * limit
    offset = offset if offset <= 100 else 100
    pages = ceil(number_of_results / limit)
    sql_paginated = sql + f" skip {offset} limit {limit}"

    if print_sql:
        print(sql_paginated)

    return {
        'page': page,
        'page_size': limit,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': [x for x in b.query_get_dict(sql_paginated)]
    }


def _get_terms_from_model_starts_with(form_field: str, sa_column: InstrumentedAttribute, by="args"):
    return _get_terms_from_model_like(form_field, sa_column, how="starts_with", by=by)


def _get_terms_from_model_ends_with(form_field: str, sa_column: InstrumentedAttribute, by="args"):
    return _get_terms_from_model_like(form_field, sa_column, how="starts_with", by=by)


def _get_terms_from_model_contains(form_field: str, sa_column: InstrumentedAttribute, by="args"):
    return _get_terms_from_model_like(form_field, sa_column, how="contains", by=by)


def _get_terms_from_model_like(form_field: str, sa_column: InstrumentedAttribute, how="like", by="args"):
    """Get terms from SQL Alchemy models field. Alchemy models field should be unique.

    :param form_field: name of form field
    :param sa_column: column of SQL Alchemy model
    :param how: (like, starts_with, ends_with, contains)
    :param by: (args, data)
    """
    search_term, page, page_size = None, None, None
    if by == "args":
        page_size = request.args.get('page_size', 10)
        page = request.args.get('page', 1)
        search_term = request.args.get(form_field, None)
    elif by == "data":
        page_size = request.data.get('page_size', 10)
        page = request.data.get('page', 1)
        search_term = request.data.get(form_field, None)

    if not (search_term and page and page_size):
        return {'error': f"{form_field} is required."}

    if how == "starts_with":
        search_term = f"{search_term}%"
    elif how == "ends_with":
        search_term = f"%{search_term}"
    elif how == "contains":
        search_term = f"%{search_term}%"

    model = sa_column.class_
    primary_key = inspect(model).primary_key[0]
    query = RDBMS.get_session().query(
        primary_key, sa_column
    ).filter(
        sa_column.like(f"{search_term}%")
    ).order_by(sa_column)

    number_of_results = query.count()

    limit = int(page_size)
    page = int(page)
    offset = (page - 1) * limit
    offset = offset if offset <= 100 else 100
    pages = ceil(number_of_results / limit)

    return {
        'page': page,
        'page_size': limit,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': {x[1]: x[0] for x in query.limit(limit).offset(offset).all()}
    }


def add_query_filters(query: Query, columns_params: Dict[str, Dict[str, str]], model: DeclarativeMeta):
    """Add optional filters to query."""
    col_filters = []
    for column_name, v in columns_params.items():
        if v.get('how2search') and v.get('value'):
            how2search = v['how2search']
            print(how2search)
            value = v['value'].strip() if isinstance(v['value'], str) else v['value']

            column = inspect(model).columns[column_name]
            if how2search in ('exact', 'exact_numeric'):
                col_filters.append(column == value)
            elif how2search == 'starts_with':
                col_filters.append(column.like(value + '%'))
            elif how2search == 'ends_with':
                col_filters.append(column.like('%' + value))
            elif how2search == 'contains':
                col_filters.append(column.like('%' + value + '%'))
            elif how2search == 'greater_than':
                col_filters.append(column.__gt__(value))
            elif how2search == 'greater_equals_than':
                col_filters.append(column.__ge__(value))
            elif how2search == 'smaller_than':
                col_filters.append(column.__lt__(value))
            elif how2search == 'smaller_equals_than':
                col_filters.append(column.__le__(value))
            elif how2search == 'not_equals':
                col_filters.append(column != value)
            elif how2search == 'exclude':
                col_filters.append(not_(column.like(value)))
            elif how2search == 'between':
                found_2_values = re.search(
                    r"(?P<value_1>[+-]?\d+(\.\d+)?).*?[-,;:/].*?(?P<value_2>[+-]?\d+(\.\d+)?)",
                    value
                )
                if found_2_values:
                    values = sorted(found_2_values.groupdict().values(), reverse=True)
                    col_filters.append(column.between(*values))

    query = query.filter(*col_filters)
    return query
