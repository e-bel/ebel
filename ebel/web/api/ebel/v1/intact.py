"""IntAct API methods."""
from sqlalchemy import or_
from flask.globals import request

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models.intact import Intact
from ebel.manager.orientdb.odb_structure import intact_edges
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_query_result, _get_paginated_ebel_query_result


def get_intact():
    """Get generic IntAct entry."""
    return _get_data(Intact)


def get_by_uniprot():
    """Get IntAct entry by UniProt ID."""
    ua = request.args.get('uniprot_accession')
    if ua:
        a = Intact.int_a_uniprot_id
        b = Intact.int_a_uniprot_id
        query = RDBMS.get_session().query(Intact).filter(or_(a == ua, b == ua))
        return _get_paginated_query_result(query)


def get_ebel_relation():
    """Get IntAct related eBEL relations."""
    has_ppi_ia_edge = [x for x in intact_edges if x.name == 'has_ppi_ia'][0]
    conf = {x.prop_name: x.prop_name for x in has_ppi_ia_edge.props}
    conf.update({
        'relation_type': "@class",
        'edge_id': "@rid.asString()",
        'interactor_a_rid': "out.@rid.asString()",
        'interactor_a_name': "out.name",
        'interactor_a_namespace': "out.namespace",
        'interactor_a_bel': "out.bel",
        'interactor_b_rid': "in.@rid.asString()",
        'interactor_b_namespace': "in.namespace",
        'interactor_b_name': "in.name",
        'interactor_b_bel': "in.bel",
    })
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM has_ppi_ia"

    ra = request.args
    paras = {k: ra[k] for k in ra if k in conf}
    if paras:
        sql += " WHERE " + ' AND '.join([f'{conf[k].replace(".asString()","")} like "{v}"' for k, v in paras.items()])

    return _get_paginated_ebel_query_result(sql)
