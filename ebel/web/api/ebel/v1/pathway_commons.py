"""Pathway Commons API methods."""

from flask import request
from sqlalchemy import or_

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models.pathway_commons import PathwayCommons, PathwayName, pathway_commons__pathway_name, Pmid
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_ebel_query_result, _get_paginated_query_result, \
    _get_terms_from_model_starts_with


def get_pathway_commons():
    """Get paginated list of Pathway Commons entries."""
    return _get_data(PathwayCommons)


def get_by_gene_symbol():
    """Get entries by gene symbol."""
    gene_symbol = request.args.get('gene_symbol')
    query = RDBMS.get_session().query(PathwayCommons).filter(
        or_(PathwayCommons.participant_a == gene_symbol, PathwayCommons.participant_b == gene_symbol))
    return _get_paginated_query_result(query)


def get_by_pathway_name():
    """Get entries by pathway name."""
    pathway_name = request.args.get('pathway_name')
    query = RDBMS.get_session().query(PathwayCommons) \
        .join(pathway_commons__pathway_name) \
        .join(PathwayName) \
        .filter_by(name=pathway_name)
    return _get_paginated_query_result(query)


def get_by_pmid():
    """Get entries by PMID."""
    pmid = request.args.get('pmid')
    query = RDBMS.get_session().query(PathwayCommons) \
        .join(Pmid) \
        .filter_by(pmid=pmid)
    return _get_paginated_query_result(query)


def get_pathway_name_starts_with():
    """Get entries where pathway starts with given value."""
    return _get_terms_from_model_starts_with('pathway_name', PathwayName.name)


def get_ebel_relation():
    """Get Pathway Commons related eBEL relations."""
    conf = {
        'interactor_a_rid': "out.rid.asString()",
        'interactor_a_namespace': "out.namespace",
        'interactor_a_name': "out.name",
        'edge_rid': "rid.asString()",
        'relation_type': "type",
        'sources': "sources",
        'pmids': "pmids",
        'pathways': "pathways.name",
        'interactor_b_rid': "in.rid.asString()",
        'interactor_b_namespace': "in.namespace",
        'interactor_b_name': "in.name",
    }
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM has_action_pc"

    ra = request.args
    wheres = []

    source = ra.get('source')
    if source:
        wheres.append(f'"{source}" in sources')

    pmid = ra.get('pmid')
    if source:
        wheres.append(f'{pmid} in pmids')

    pathway = ra.get('pathway')
    if pathway:
        wheres.append(f'"{pathway}" in pathways.name')

    paras = {k: request.args[k] for k in request.args if k in conf}
    if paras:
        wheres += [f'{conf[k].replace(".asString()","")} like "{v}"' for k, v in paras.items()]

    if wheres:
        sql += " WHERE " + ' AND '.join(wheres)

    return _get_paginated_ebel_query_result(sql)
