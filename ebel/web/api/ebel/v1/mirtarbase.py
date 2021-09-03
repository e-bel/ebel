"""miRTarBase API methods."""

from flask import request

from ebel.manager.rdbms.models import mirtarbase
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_ebel_query_result


def get_mirtarbase():
    """Get generic mirtarbase entry."""
    return _get_data(mirtarbase.Mirtarbase)


def get_ebel_relation():
    """Get miRTarBase related eBEL relations."""
    conf = {
        'mirbase_id': "out.name",
        'target_rna_symbol': "in.name",
        'target_namespace': "in.namespace",
        'support_type': "support_type",
        'pmid': "pmid",
        'experiments': "experiments"
    }
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM has_mirgene_target"

    ra = request.args

    wheres = []

    experiment = ra.get('experiment')
    if experiment:
        wheres.append(f'"{experiment}" in experiments')

    paras = {k: ra[k] for k in ra if k in conf}
    if paras:
        wheres += [f'{conf[k].replace(".asString()","")} like "{v}"' for k, v in paras.items()]

    if wheres:
        sql += " WHERE " + ' AND '.join(wheres)

    return _get_paginated_ebel_query_result(sql)
