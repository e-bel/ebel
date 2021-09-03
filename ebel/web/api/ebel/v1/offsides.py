"""OffSIDES API methods."""

from flask import request

from ebel.manager.rdbms.models.offsides import Offsides
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_ebel_query_result


def get_offsides():
    """Get generic OffSIDES entry."""
    return _get_data(Offsides)


def get_ebel_relation():
    """Get OFFSIDES related eBEL relations."""
    conf = {
        'drugbank_id': "out.drugbank_id",
        'drug_label': "out.label",
        'ppr': "prr",
        'mean_reporting_frequency': "mean_reporting_frequency",
        'condition_meddra_id': "in.condition_meddra_id",
        'side_effect': "in.label",
    }
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM has_side_effect"

    paras = {k: request.args[k] for k in request.args if k in conf}
    if paras:
        wheres = [f'{conf[k].replace(".asString()","")} like "{v}"' for k, v in paras.items()]
        sql += " WHERE " + ' AND '.join(wheres)

    return _get_paginated_ebel_query_result(sql)
