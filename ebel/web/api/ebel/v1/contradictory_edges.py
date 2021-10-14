"""API queries for collecting contraidctory edges."""

from ebel import Bel
from flask import request
from ebel.web.api.ebel.v1 import _get_pagination
from math import ceil
from typing import Dict


def _get_where_sql(where_dict: Dict[str, str]) -> str:
    where = ""
    if any(where_dict.values()):
        where = ", WHERE:(" + " AND ".join([f"{k} = '{v}'" for k, v in where_dict.items() if v]) + ")"
    return where


def get_contradictory_edges():
    """Return list of nodes with a given namespace."""
    b = Bel()

    subject_class = request.args.get('subject_class', 'bel')
    object_class = request.args.get('object_class', 'bel')

    sub, obj = {}, {}
    sub['namespace'] = request.args.get('subject_namespace')
    sub['name'] = request.args.get('subject_name')
    obj['namespace'] = request.args.get('object_namespace')
    obj['name'] = request.args.get('object_name')

    pagination = _get_pagination()
    match = f"match {{class:{subject_class}, as:subject_1 {_get_where_sql(sub)} }}" \
            ".outE('directly_increases', 'increases'){as:relation_1}" \
            f".inV(){{class:{object_class}, as:object {_get_where_sql(obj)} }}" \
            ".inE('decreases', 'directly_decreases'){as:relation_2}" \
            f".outV(){{class:{subject_class}, as:subject_2, where:($matched.subject_1=$currentMatch)}}" \
            """ return
                subject_1.@rid.asString() as subject_rid,
                subject_1.@class.asString() as subject_class,
                subject_1.namespace as subject_namespace,
                subject_1.name as subject_name,
                subject_1.bel as subject_bel,
                relation_1.@rid.asString() as relation_1_rid,
                relation_1.@class as relation_1_class,
                relation_1.evidence as relation_1_evidence,
                relation_1.pmid as relation_1_pmid,
                relation_1.annotation as relation_1_annotation,
                object.@rid.asString() as object_rid,
                object.@class.asString() as object_class,
                object.namespace as object_namespace,
                object.name as object_name,
                object.bel as object_bel,
                relation_2.@rid.asString() as relation_2_rid,
                relation_2.@class as relation_2_class,
                relation_2.evidence as relation_2_evidence,
                relation_2.pmid as relation_2_pmid,
                relation_2.annotation as relation_2_annotation"""

    number_of_results = b.execute(f"Select count(*) as number from ({match})")[0].oRecordData['number']

    sql_pagination = f"Select * from ({match}) limit {pagination.page_size} skip {pagination.skip}"
    results = [x.oRecordData for x in b.execute(sql_pagination)]
    pages = ceil(number_of_results / pagination.page_size)

    return {
        'page': pagination.page,
        'page_size': pagination.page_size,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': results
    }
