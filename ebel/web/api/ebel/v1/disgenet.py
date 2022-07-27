"""DisGeNet API methods."""
from flask import request

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import disgenet
from ebel.web.api.ebel.v1 import _get_paginated_query_result, _get_terms_from_model_starts_with, \
    _get_paginated_ebel_query_result


def get_sources():
    """Return all sources."""
    d = disgenet.DisgenetSource
    return {x.source: x.id for x in RDBMS.get_session().query(d.source, d.id).all()}


def get_disease_name_starts_with():
    """Get entry based on beginning of disease name."""
    return _get_terms_from_model_starts_with(
        form_field='disease_name',
        sa_column=disgenet.DisgenetDisease.disease_name)


def get_gene_symbol_starts_with():
    """Get entry based on beginning of symbol."""
    return _get_terms_from_model_starts_with(
        form_field='gene_symbol',
        sa_column=disgenet.DisgenetGeneSymbol.gene_symbol)


def get_gene_disease_pmid_associations():
    """Get list of PMIDs with disease genes defined."""
    gene_cols = ['gene_id', 'disease_id', 'pmid']
    gene_paras = {k: v for k, v in request.args.items() if k in gene_cols and v}
    query = RDBMS.get_session().query(disgenet.DisgenetGene).filter_by(**gene_paras)
    gene_symbol = request.args.get('gene_symbol')
    if gene_symbol:
        gs = disgenet.DisgenetGeneSymbol
        query = query.join(gs).filter(gs.gene_symbol.like(gene_symbol))
    disease_name = request.args.get('disease_name')
    if disease_name:
        dd = disgenet.DisgenetDisease
        query = query.join(dd).filter(dd.disease_name.like(disease_name))
    source = request.args.get('source')
    if source:
        so = disgenet.DisgenetSource
        query = query.join(so).filter(so.source.like(source))

    return _get_paginated_query_result(query)


def get_variant_disease_pmid_associations():
    """Get list of PMIDs with disease variants defined."""
    cols = ['snp_id', 'chromosome', 'position', 'disease_id', 'score', 'pmid', 'source_id']
    paras = {k: v for k, v in request.args.items() if k in cols and v}
    query = RDBMS.get_session().query(disgenet.DisgenetVariant).filter_by(**paras)
    disease_name = request.args.get('disease_name')
    if disease_name:
        dd = disgenet.DisgenetDisease
        query = query.join(dd).filter(dd.disease_name.like(disease_name))
    source = request.args.get('source')
    if source:
        so = disgenet.DisgenetSource
        query = query.join(so).filter(so.source.like(source))

    return _get_paginated_query_result(query)


def get_ebel_has_snp_disgenet():
    """Get SNP edge add by e(BE:L) via DiGeNet."""
    edge_class = 'has_snp_disgenet'

    allowed_relations = ['has_snp_disgenet',
                         'has_mapped_snp_dgn',
                         'has_downstream_snp_dgn',
                         'has_upstream_snp_dgn']
    relation = request.args.get('relation')

    where = {'@class': relation if relation in allowed_relations else None,
             'out.name': request.args.get('name'),
             'out.namespace': request.args.get('namespace'),
             'in.rs_number': request.args.get('rs_number')}
    # non-edge parameter
    # edge parameter
    edge_properties = ['disease_name', 'source', 'pmid']
    where.update({k: v for k, v in request.args.items() if k in edge_properties})

    sql = f"""SELECT
        @rid.asString() as rid,
        @class as relation,
        in.rs_number as snp_rs_number,
        in.@rid.asString() as snp_rid,
        score,
        disease_name,
        source,
        set(pmid) as pmids,
        out.@rid.asString() as gene_rid,
        out.name as gene_symbol FROM {edge_class}"""
    if where:
        sql += " WHERE " + " AND ".join([f'{k} like "{v}"' for k, v in where.items() if v])
    sql += " GROUP BY @class, in.rs_number, score, disease_name, source, out.name"

    return _get_paginated_ebel_query_result(sql)
