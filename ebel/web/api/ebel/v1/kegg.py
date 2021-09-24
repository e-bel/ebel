"""KEGG API methods."""

from sqlalchemy import or_
from flask.globals import request

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models.kegg import Kegg
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_query_result, _get_paginated_ebel_query_result


def get_kegg():
    """Get generic KEGG entry."""
    return _get_data(Kegg)


def get_by_gene_symbol():
    """Get KEGG entry by gene symbol."""
    symbol = request.args.get('gene_symbol')
    query_filter = or_(Kegg.gene_symbol_a == symbol, Kegg.gene_symbol_b == symbol)
    query = RDBMS.get_session().query(Kegg).filter(query_filter)
    return _get_paginated_query_result(query)


def get_ebel_relation():
    """Get KEGG related eBEL relations."""
    conf = {
        'interaction_type': 'interaction_type',
        'pathway_names': "pathway_name",
        'edge_id': "@rid.asString()",
        'interactor_a_rid': "out.@rid.asString()",
        'interactor_a_name': "out.name",
        'interactor_a_namespace': "out.namespace",
        'interactor_a_bel': "out.bel",
        'interactor_b_rid': "in.@rid.asString()",
        'interactor_b_namespace': "in.namespace",
        'interactor_b_name': "in.name",
        'interactor_b_bel': "in.bel",
        'relation': "@class.asString()",
    }
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM has_ppi_kg"

    ra = request.args
    paras = {k: ra[k] for k in ra if k in conf}
    pathway_name = request.args.get('pathway_name')
    if paras or pathway_name:
        wheres = []
        if paras:
            wheres += [f'{conf[k].replace(".asString()","")} like "{v}"' for k, v in paras.items()]
        if pathway_name:
            wheres += [f'"{pathway_name}" in pathway_name']

        sql += " WHERE " + ' AND '.join(wheres)

    return _get_paginated_ebel_query_result(sql)
