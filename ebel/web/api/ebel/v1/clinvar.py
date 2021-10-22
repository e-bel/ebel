"""ClinVar API methods."""

from flask import request

from ebel import Bel
from math import ceil
from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import clinvar
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_query_result, _get_terms_from_model_starts_with, \
    _get_pagination


def get_clinvar():
    """Get generic ClinVar entry."""
    return _get_data(clinvar.Clinvar)


def get_clinvar_simple():
    """Generic Clinvar result query."""
    cc = clinvar.Clinvar
    cp = clinvar.ClinvarPhenotype
    paras = {k: v for k, v in request.args.items() if
             k in ['gene_id', 'gene_symbol', 'hgnc_id', 'allele_id', 'assembly', 'rs_db_snp']}
    query = RDBMS.get_session().query(cc.id, cc.hgnc_id, cc.allele_id, cc.gene_symbol, cc.assembly, cc.rs_db_snp)\
        .filter_by(**paras).join(clinvar.clinvar__clinvar_phenotype).join(cp)

    phenotype = request.args.get('phenotype')
    if phenotype:
        query = query.filter_by(phenotype='Alzheimer disease')

    return _get_paginated_query_result(query.distinct(), return_dict=True)


def get_phenotype_starts_with():
    """Get Clinvar results by fuzzy phenotype search."""
    return _get_terms_from_model_starts_with('phenotype', clinvar.ClinvarPhenotype.phenotype)


def get_by_other_identifier():
    """Get Clinvar results by other identifier."""
    cc = clinvar.Clinvar
    co = clinvar.ClinvarOtherIdentifier

    db = request.args.get('db')
    identifier = request.args.get('identifier')
    query = RDBMS.get_session().query(co.db,
                                      co.identifier,
                                      cc.id,
                                      cc.hgnc_id,
                                      cc.allele_id,
                                      cc.gene_symbol,
                                      cc.assembly,
                                      cc.rs_db_snp).join(co).filter_by(db=db).filter(co.identifier.like(identifier))

    return _get_paginated_query_result(query.distinct(), return_dict=True)


def get_by_medgen():
    """Get Clinvar results by MedGen identifier."""
    cc = clinvar.Clinvar
    cm = clinvar.ClinvarPhenotypeMedgen

    # db = request.args.get('db')
    identifier = request.args.get('identifier')
    query = RDBMS.get_session().query(cm.identifier,
                                      cc.id,
                                      cc.hgnc_id,
                                      cc.allele_id,
                                      cc.gene_symbol,
                                      cc.assembly,
                                      cc.rs_db_snp).join(cm).filter_by(identifier=identifier)

    return _get_paginated_query_result(query.distinct(), return_dict=True)


def get_ebel_relation():
    """Get ClinVar related e(BE:L) relations."""
    b = Bel()
    p = _get_pagination()
    req = dict(request.args.copy())
    wheres = []
    if req.get('rs_number'):
        wheres.append(f"in.rs_number='{req['rs_number']}'")
    relation_type = req.get('relation_type')
    allowed_relations = ['has_snp_clinvar',
                         'has_mapped_snp_cv',
                         'has_downstream_snp_cv',
                         'has_upstream_snp_cv']
    relation_type = relation_type if relation_type in allowed_relations else allowed_relations[0]
    wheres += [f'out.{k} = "{v}"' for k, v in req.items() if k in ['namespace', 'name']]
    wheres += [f'{k} = "{v}"' for k, v in req.items() if k in ['phenotype', 'keyword']]

    columns = """in.rs_number as rs_number,
                 @class.asString() as relation_type,
                 phenotype,
                 clinical_significance,
                 out.namespace as namespace,
                 out.name as name"""

    from_where_sql = f""" FROM {relation_type}"""
    if wheres:
        from_where_sql += " WHERE " + ' AND '.join(wheres)

    number_of_results = b.query_get_dict(f"Select count(*) {from_where_sql}")[0]['count']

    sql = f"SELECT {columns} {from_where_sql} LIMIT {p.page_size} SKIP {p.skip}"

    return {
        'page': p.page,
        'page_size': p.page_size,
        'number_of_results': number_of_results,
        'pages': ceil(number_of_results / p.page_size),
        'results': b.query_get_dict(sql)
    }
