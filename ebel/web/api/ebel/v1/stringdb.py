"""StringDB API methods."""

from flask import request

from ebel.manager.rdbms.models.stringdb import StringDb, StringDbAction
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_ebel_query_result


def get_stringdb():
    """Get generic StringDB entry."""
    return _get_data(StringDb)


def get_stringdb_action():
    """Get StringDB entry by action."""
    return _get_data(StringDbAction)


def get_ebel_relation():
    """Get StringDB related eBEL relations."""
    conf = {
        'interactor_a_rid': "out.@rid.asString()",
        'interactor_a_name': "out.name",
        'interactor_a_namespace': "out.namespace",
        'interactor_a_uniprot': "out.uniprot",
        'edge_id': "@rid.asString()",
        'relation': "@class.asString()",
        'interactor_b_rid': "in.@rid.asString()",
        'interactor_b_namespace': "in.namespace",
        'interactor_b_name': "in.name",
        'interactor_b_uniprot': "in.uniprot",
    }
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM has_action_st"

    ra = request.args
    paras = {k: ra[k] for k in ra if k in conf}

    if paras:
        wheres = [f'{conf[k].replace(".asString()","")} like "{v}"' for k, v in paras.items()]
        sql += " WHERE " + ' AND '.join(wheres)

    return _get_paginated_ebel_query_result(sql)
