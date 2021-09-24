"""Expression Atlas API methods."""
from ebel.web.api.ebel.v1 import _get_data
from ebel.manager.rdbms.models import expression_atlas
from flask import request
import re
from collections import Counter
from ebel.manager.rdbms.models.expression_atlas import Gsea
from ebel import Bel


def get_expriment():
    """Get list of experiments."""
    return _get_data(expression_atlas.Experiment)


def get_idf():
    """Get list of IDFs."""
    return _get_data(expression_atlas.Idf)


def get_group_comparison():
    """Get list of group comparisons."""
    return _get_data(expression_atlas.GroupComparison)


def get_fold_change():
    """Get list of fold changes."""
    return _get_data(expression_atlas.FoldChange)


def get_sdrf_condensed():
    """Get list of condensed version of SDRFs."""
    return _get_data(expression_atlas.SdrfCondensed)


def get_gsea():
    """Get GSEA data."""
    return _get_data(expression_atlas.Gsea, order_by=[expression_atlas.Gsea.p_adj_non_dir])


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
