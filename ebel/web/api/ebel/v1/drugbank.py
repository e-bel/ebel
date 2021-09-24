"""DrugBank API methods."""
from flask import request
from sqlalchemy.orm.attributes import InstrumentedAttribute

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import drugbank
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_query_result, _get_paginated_ebel_query_result


def get_by_id():
    """Get DrugBank entry by ID."""
    drugbank_id = request.args.get('drugbank_id')
    if drugbank_id:
        query = RDBMS.get_session().query(drugbank.Drugbank).filter_by(drugbank_id=drugbank_id.strip())
        return query.first().as_dict()


def get_drugbank():
    """Get generic DrugBank entry."""
    return _get_data(drugbank.Drugbank)


def get_interaction():
    """Get DrugBank drug interactions."""
    return _get_data(drugbank.DrugInteraction)


def _get_model(model):
    """Get tables connected to Drugbank - paginated."""
    drugbank_id = request.args.get('drugbank_id')
    columns_like = {
        col_obj.like(request.args[col_name]) for col_name, col_obj in model.__dict__.items()
        if isinstance(col_obj, InstrumentedAttribute) and col_name in request.args and col_name != 'drugbank_id'
    }
    query = RDBMS.get_session().query(model).filter(*columns_like)
    if drugbank_id:
        query = query.join(drugbank.Drugbank).filter_by(drugbank_id=drugbank_id)
    return _get_paginated_query_result(query, print_sql=True)


def get_pathway():
    """Get DrugBank involved pathways."""
    return _get_model(drugbank.Pathway)


def get_status():
    """Get DrugBank statuses."""
    return _get_model(drugbank.Status)


def get_patent():
    """Get DrugBank patents."""
    return _get_model(drugbank.Patent)


def get_external_identifier():
    """Get DrugBank external identifiers."""
    return _get_model(drugbank.ExternalIdentifier)


def get_reference():
    """Get DrugBank references."""
    return _get_model(drugbank.Reference)


def get_target():
    """Get DrugBank targets."""
    return _get_model(drugbank.Target)


def get_product_name():
    """Get DrugBank product names."""
    return _get_model(drugbank.ProductName)


def get_synonym():
    """Get DrugBank synonyms."""
    return _get_model(drugbank.Synonym)


def get_has_drug_target_db():
    """Get DrugBank related eBEL relations."""
    conf = {
        'target_rid': "in.@rid.asString()",
        'target_name': "in.name",
        'target_namespace': "in.namespace",
        'target_uniprot_accession': "in.uniprot",
        'drugbank_id': "out.drugbank_id",
        'drug_name': "out.label",
        'drug_rid': "out.@rid.asString()",
        'edge_rid': "@rid.asString()",
        'action': "action",
        'known_action': "known_action"
    }
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM has_drug_target_db"
    ra = request.args
    paras = {k: ra[k] for k in ra if k in conf}
    if paras:
        sql += " WHERE " + ' AND '.join([f'{conf[k]} = "{v}"' for k, v in paras.items()])
    return _get_paginated_ebel_query_result(sql)
