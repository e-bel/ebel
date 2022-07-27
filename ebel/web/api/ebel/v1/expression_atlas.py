"""Expression Atlas API methods."""
import math
import re
import json
from ebel.web.api import RDBMS
from . import _get_paginated_query_result, add_query_filters

from ebel.web.api.ebel.v1 import _get_data
from flask import request
from sqlalchemy import inspect

from collections import Counter
from ebel.manager.rdbms.models.expression_atlas import (
    GroupComparison,
    Gsea,
    FoldChange,
    Experiment,
    Idf,
    SdrfCondensed)
from ebel import Bel

models_dict = {
    'experiment': Experiment,
    'idf': Idf,
    'gsea': Gsea,
    'group_comparison': GroupComparison,
    'foldchange': FoldChange,
    'sdrf_condensed': SdrfCondensed
}


def get_expriment():
    """Get list of experiments."""
    return _get_data(Experiment)


def get_idf():
    """Get list of IDFs."""
    return _get_data(Idf)


def get_group_comparison():
    """Get list of group comparisons."""
    return _get_data(GroupComparison)


def get_fold_change():
    """Get list of fold changes."""
    return _get_data(FoldChange)


def get_sdrf_condensed():
    """Get list of condensed version of SDRFs."""
    return _get_data(SdrfCondensed)


def get_gsea():
    """Get GSEA data."""
    return _get_data(Gsea, order_by=[Gsea.p_adj_non_dir])


class GseaType:
    """String constant definitions."""

    GO = 'go'
    REACTOME = 'reactome'
    INTERPRO = 'interpro'


def get_most_common_gseas_by_group_comparison_ids() -> list:
    """Identify most often ocurring GSEAs based on group comparison IDs."""
    b = Bel()
    group_comparison_ids_str = request.args.get('group_comparison_ids', '')
    group_comparison_ids = [
        int(x.strip())
        for x in group_comparison_ids_str.split(',')
        if isinstance(x, str) and re.search(r"\s*\d+\s*", x)
    ]
    query = b.session.query(
        Gsea.accession,
        Gsea.term,
        Gsea.gsea_type
    ).filter(Gsea.group_comparison_id.in_(group_comparison_ids))

    gsea_type = request.args.get('gsea_type', '')
    gsea_type = gsea_type if gsea_type in [GseaType.GO, GseaType.REACTOME, GseaType.INTERPRO] else ''

    if gsea_type:
        query = query.filter(Gsea.gsea_type == gsea_type)

    p_adj_non_dir = request.args.get('p_adj_non_dir', '')
    p_adj_non_dir = float(p_adj_non_dir) if re.search(r'\s*\d+(\.\d+)?\s*', p_adj_non_dir) else None
    if isinstance(p_adj_non_dir, float):
        query = query.filter(Gsea.p_adj_non_dir <= p_adj_non_dir)

    results = [x for x in query.all()]

    return [{'accession': x[0][0], 'term': x[0][1], 'type': x[0][2], 'occurence': x[1]}
            for x in Counter(results).most_common() if x[1] > 1]


def get_comparison_groups_by_genes():
    """Get experiments, comparion groups and foldchanges by 2 genes."""
    gene_1 = request.args.get('gene_symbol_1')
    gene_2 = request.args.get('gene_symbol_2')
    return _get_comparison_groups_by_genes(gene_1, gene_2)


def _get_comparison_groups_by_genes(gene_1, gene_2):
    """Get experiments, comparion groups and foldchanges by 2 genes."""
    result_keys = [
        'fold_change_gene_symbol_1',
        'fold_change_gene_symbol_2',
        'group_comparison',
        'experiment_title',
        'experiment_identifier',
        'is_positive_correlated'
    ]
    sql = f"""Select
        a.log2foldchange,
        b.log2foldchange,
        gc.name,
        e.title,
        e.name,
        if(((a.log2foldchange>0 and b.log2foldchange>0) or (a.log2foldchange<0 and b.log2foldchange<0)),1,0)
    from (Select
            group_comparison_id,
            log2foldchange
        from
            expression_atlas_foldchange where gene_name = '{gene_1}') a
    inner join (Select
            group_comparison_id,
            log2foldchange
        from expression_atlas_foldchange where gene_name = '{gene_2}') b
    using(group_comparison_id)
    inner join expression_atlas_group_comparison gc on (gc.id=group_comparison_id)
    inner join expression_atlas_experiment e on (e.id = gc.experiment_id)
    order by (a.log2foldchange + b.log2foldchange) desc"""
    with Bel().engine.connect() as con:
        return list([dict(zip(result_keys, x)) for x in con.execute(sql).fetchall()])


def get_comparison_groups_by_edge_rid():
    """Use edge rIDs to get different groups to compare."""
    rid = request.args.get('edge_rid')
    res = Bel().query_get_dict(f"""Select
                                    in.name as name_in,
                                    in.namespace as ns_in,
                                    out.name as name_out,
                                    out.namespace as ns_out,
                                    in.bel as in_bel,
                                    out.bel as out_bel,
                                    @class.asString() as relation,
                                    citation,
                                    annotation,
                                    evidence
                                from {rid}""")
    if(res):
        has_all_cols = all([(x in res[0]) for x in ['name_in', 'ns_in', 'name_out', 'ns_out']])
        if has_all_cols:
            both_ns_hgnc = res[0]['ns_in'] == 'HGNC' and res[0]['ns_out'] == 'HGNC'
            not_the_same = res[0]['name_in'] != res[0]['name_out']
            if has_all_cols and both_ns_hgnc and not_the_same:
                gene_symbol_1 = res[0]['name_in']
                gene_symbol_2 = res[0]['name_out']
                comparisons = _get_comparison_groups_by_genes(gene_symbol_1, gene_symbol_2)
                return {
                    'gene_symbol_1': gene_symbol_1,
                    'gene_symbol_2': gene_symbol_2,
                    'citation': res[0].get('citation'),
                    'annotation': res[0].get('annotation'),
                    'evidence': res[0].get('evidence'),
                    'relation': res[0].get('relation'),
                    'comparisons': comparisons,
                    'bel_object': res[0].get('in_bel'),
                    'bel_subject': res[0].get('out_bel'),
                }
    return []


def get_expression_atlas():
    """Get EA results."""
    columns = [
        Experiment.name,
        GroupComparison.name,
        Experiment.title,
        GroupComparison.group_comparison,
        GroupComparison.id
    ]
    data = json.loads(request.data)
    b = Bel()
    query = b.session.query(Experiment).join(GroupComparison)
    for table, columns_params in [(k, v) for k, v in data.items() if k not in ('page', 'page_size')]:
        any_value = any([v['value'].strip() for k, v in columns_params.items()])
        if any_value:
            model = models_dict[table]

            if model not in (Experiment, GroupComparison):
                query = query.join(model)
            query = add_query_filters(query, columns_params, model)
    query = query.with_entities(*columns)
    query = query.group_by(Experiment.id, GroupComparison.id)
    limit = int(data['page_size']) if data.get('page_size') else 10
    page = int(data['page']) if data.get('page') else 1
    count = query.count()
    query = query.limit(limit).offset(limit * (page - 1))

    print(query.statement.compile(compile_kwargs={"literal_binds": True}))
    column_names = [f"{x.parent.class_.__tablename__}.{x.name}" for x in [inspect(c) for c in columns]]
    return {
        'page': page,
        'pages': math.ceil(count / limit),
        'count': count,
        'page_size': limit,
        'column_names': column_names,
        'results': [tuple(x) for x in query.all()]
    }
