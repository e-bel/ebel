"""IUPHAR API methods."""
from flask.globals import request
from ebel.manager.orientdb.odb_structure import iuphar_edges

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import iuphar
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_ebel_query_result


def get_interaction():
    """Get generic IUPHAR entry."""
    return _get_data(iuphar.IupharInteraction)


def get_ligandby_by_id():
    """Get IUPHAR ligand entry by ID."""
    ligand_id = request.args.get('id')
    return RDBMS.get_session().query(iuphar.IupharLigand).get(ligand_id).as_dict()


def get_interaction_by_target_uniprot():
    """Get IUPHAR interaction entry by target UniProt ID."""
    return get_interaction()


def get_interaction_by_target_gene_symbol():
    """Get IUPHAR interaction entry by target gene symbol."""
    return get_interaction()


def get_ebel_relation():
    """Get Iuphar related eBEL relations."""
    as_iuphar_edge = [x for x in iuphar_edges if x.name == 'iuphar_interaction'][0]
    conf = {x.prop_name: x.prop_name for x in as_iuphar_edge.props}
    conf.update({
        'edge_id': "@rid.asString()",
        'interactor_a_rid': "out.@rid.asString()",
        'interactor_a_name': "out.name",
        'interactor_a_namespace': "out.namespace",
        'interactor_b_rid': "in.@rid.asString()",
        'interactor_b_namespace': "in.namespace",
        'interactor_b_name': "in.name",
        'relation': "@class.asString()"
    })
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM iuphar_interaction"

    ra = request.args
    paras = {k: ra[k] for k in ra if k in conf}
    pmid = request.args.get('pmid')
    if paras or pmid:
        wheres = []
        if paras:
            wheres += [f'{conf[k].replace(".asString()","")} like "{v}"' for k, v in paras.items()]
        if pmid:
            wheres += [f"{pmid} in pmids"]

        sql += " WHERE " + ' AND '.join(wheres)

    return _get_paginated_ebel_query_result(sql)
