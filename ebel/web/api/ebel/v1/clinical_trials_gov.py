"""ClinicalTrails.gov API methods."""
import json

from flask import request

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import clinical_trials_gov as ct
from ebel.web.api.ebel.v1 import _get_paginated_query_result, _get_terms_from_model_starts_with


def get_ct_by_nct_id():
    """Get CT entry based on given NCT ID."""
    nct_id = request.args.get('nct_id')
    c = RDBMS.get_session().query(ct.ClinicalTrialGov).filter_by(nct_id=nct_id).first()
    if c:
        return c.as_dict()


# not used, uses too much memory
# def get_ct_by_contains_in_summary_or_description_or_title():
#     search_term = json.loads(request.data)['search_term']
#     search_str = f"%{search_term}%"
#     results = session.query(ct).filter(or_(
#         ct.ClinicalTrialGov.brief_title.like(search_str),
#         ct.ClinicalTrialGov.official_title.like(search_str),
#         ct.ClinicalTrialGov.brief_summary.like(search_str),
#         ct.ClinicalTrialGov.detailed_description.like(search_str)
#     ))
#     return [x.as_dict() for x in results]


def get_ct_by_mesh_term():
    """Get CT entry based on given mesh term."""
    mesh_term = request.args.get('mesh_term', None)
    if not mesh_term:
        return {'error': "Mesh term is required."}
    query = RDBMS.get_session().query(ct.MeshTerm).filter(ct.MeshTerm.mesh_term.like(mesh_term))

    return _get_paginated_query_result(query)


def get_ct_by_intervention():
    """Get CT entry based on given intervention."""
    intervention_name = request.args.get('intervention_name', None)
    intervention_type = request.args.get('intervention_type', None)
    if not (intervention_name or intervention_type):
        return {'error': "At least name or type is required."}
    query = RDBMS.get_session().query(ct.Intervention)

    if intervention_type:
        query = query.filter_by(intervention_type=intervention_type)
    if intervention_type:
        query = query.filter(ct.Intervention.intervention_name.like(intervention_name))

    return _get_paginated_query_result(query)


def get_ct_by_keyword():
    """Get CT entry based on given keyword."""
    keyword = request.args.get('keyword', None)
    if not keyword:
        return {'error': "keyword is required."}
    query = RDBMS.get_session().query(ct.Keyword).filter(ct.Keyword.keyword.like(keyword))

    return _get_paginated_query_result(query)


def get_ct_by_condition():
    """Get CT entry based on given condition."""
    condition = request.args.get('condition', None)
    if not condition:
        return {'error': "Condition is required."}
    query = RDBMS.get_session().query(ct.Condition).filter(ct.Condition.condition.like(condition))

    return _get_paginated_query_result(query)


def get_mesh_term_starts_with():
    """Get CT entry based on beginning of mesh term string."""
    return _get_terms_from_model_starts_with(form_field='mesh_term', sa_column=ct.MeshTerm.mesh_term)


def get_keyword_starts_with():
    """Get CT entry based on beginning of keyword string."""
    return _get_terms_from_model_starts_with(form_field='keyword', sa_column=ct.Keyword.keyword)


def get_condition_starts_with():
    """Get CT entry based on beginning of condition string."""
    return _get_terms_from_model_starts_with(form_field='condition', sa_column=ct.Condition.condition)
