"""Test BEL relations against Expression Atlas."""

from ebel.manager.rdbms.models.expression_atlas import FoldChange, GroupComparison, Experiment
from math import ceil
from typing import List, Dict, Tuple, Set
from flask import request
from collections import namedtuple
from sqlalchemy.sql import func

from ebel import Bel
from ebel.web.api.ebel.v1 import _get_pagination

Relation = namedtuple('Relation', ['sub', 'sub_bel', 'rel_rid', 'evidence', 'rel', 'pmid', 'obj', 'obj_bel'])
ComparisonGroupValue = namedtuple('CompGroupFoldChange', ['group_comparison_id', 'log2foldchange', 'p_value'])


def get_fold_changes(session,
                     gene_name: str,
                     l2fc_threshold: float,
                     pv_threshold: float,
                     experiment_names: List[str]) -> Tuple[List[ComparisonGroupValue], List[ComparisonGroupValue]]:
    """Get fold change values for a given set of passed parameters.

    Parameters
    ----------
    session
        SQL session.
    gene_name : str
        Gene name.
    l2fc_threshold : float
        Minimum log2 fold change threshold.
    pv_threshold : float
        P-value threshold. Recommended value: 0.05
    experiment_names : List[str]
        List of experiment names.

    Returns
    -------
    Tuple.
    """
    query = session.query(
        FoldChange.group_comparison_id,
        func.avg(FoldChange.log2foldchange),
        FoldChange.p_value)\
        .filter_by(gene_name=gene_name)\
        .group_by(FoldChange.group_comparison_id, FoldChange.gene_id)
    if experiment_names:
        query = query.join(GroupComparison).join(Experiment).filter(Experiment.name.in_(experiment_names))

    query_up = query.filter(
        FoldChange.log2foldchange >= l2fc_threshold,
        FoldChange.p_value <= pv_threshold)
    query_down = query.filter(
        FoldChange.log2foldchange <= -1 * l2fc_threshold,
        FoldChange.p_value <= pv_threshold)

    up_all = [ComparisonGroupValue(*x) for x in query_up.all()]
    down_all = [ComparisonGroupValue(*x) for x in query_down.all()]
    return down_all, up_all


def validate_bel_against_experiment() -> dict:
    """Check whether BEL edges match experimental results."""
    pagination = _get_pagination()

    subject_class = request.args.get('subject_class', 'genetic_flow')
    subject_name = request.args.get('subject_hgnc_symbol')
    object_class = request.args.get('object_class', 'genetic_flow')
    object_name = request.args.get('object_hgnc_symbol')
    subject_l2fc_threshold = float(request.args.get('subject_log2foldchange_threshold', '2'))
    subject_pv_threshold = float(request.args.get('subject_p_value_threshold', '0.05'))
    object_l2fc_threshold = float(request.args.get('object_log2foldchange_threshold', '2'))
    object_pv_threshold = float(request.args.get('object_p_value_threshold', '0.05'))

    experiment_names = [x.strip() for x in request.args.get('experiment_names', '').split(',') if x.strip()]

    subject_sql = f" and name = '{subject_name}'" if subject_name else ''
    object_sql = f" and name = '{object_name}'" if object_name else ''

    sql_basis = f"""from (
        match {{class:{subject_class}, as:sub,
        where:(namespace = 'HGNC' {subject_sql})}}
        .outE('directly_increases', 'increases','decreases',
        'directly_decreases', 'positive_correlation', 'negative_correlation'){{as:rel}}
        .inV(){{class:{object_class}, as:obj,
        where:(namespace = 'HGNC' {object_sql})}}
        return
            sub.name as sub,
            sub.bel as sub_bel,
            rel.@rid.asString() as rel_rid,
            rel.evidence as evidence,
            rel.@class.asString() as rel,
            rel.pmid as pmid,
            obj.name as obj,
            obj.bel as obj_bel)
        where sub!=obj"""

    bel = Bel()
    session = bel.session
    number_of_results = bel.execute("Select count(*) " + sql_basis)[0].oRecordData['count']
    sql = "Select * " + sql_basis + f" limit {pagination.page_size} skip {pagination.skip}"
    relations: List[Relation] = [Relation(**x.oRecordData) for x in bel.execute(sql)]

    dea_results = {}
    gc_ids = set()

    for gene_name_sub, gene_name_obj in {(x.sub, x.obj) for x in relations}:
        sub_down, sub_up = get_fold_changes(session,
                                            gene_name_sub,
                                            subject_l2fc_threshold,
                                            subject_pv_threshold,
                                            experiment_names)
        sub_down_gc_set = {x.group_comparison_id for x in sub_down}
        sub_up_gc_set = {x.group_comparison_id for x in sub_up}

        if gene_name_sub not in dea_results:
            dea_results[gene_name_sub] = {}

        obj_down, obj_up = get_fold_changes(session,
                                            gene_name_obj,
                                            object_l2fc_threshold,
                                            object_pv_threshold,
                                            experiment_names)
        obj_down_gc_set = {x.group_comparison_id for x in obj_down}
        obj_up_gc_set = {x.group_comparison_id for x in obj_up}

        res = dea_results[gene_name_sub][gene_name_obj] = {}

        # opposite direction
        sub_up_obj_down_values = get_values_for_intersection(sub_up, obj_down, sub_up_gc_set, obj_down_gc_set)
        gc_ids.update(set(sub_up_obj_down_values.keys()))
        res['sub_up_obj_down'] = sub_up_obj_down_values

        sub_down_obj_up_values = get_values_for_intersection(sub_down, obj_up, sub_down_gc_set, obj_up_gc_set)
        gc_ids.update(set(sub_down_obj_up_values.keys()))
        res['sub_down_obj_up'] = sub_down_obj_up_values

        # same direction
        sub_up_obj_up_values = get_values_for_intersection(sub_up, obj_up, sub_up_gc_set, obj_up_gc_set)
        gc_ids.update(set(sub_up_obj_up_values.keys()))
        res['sub_up_obj_up'] = sub_up_obj_up_values

        sub_down_obj_down_values = get_values_for_intersection(sub_down, obj_down, sub_down_gc_set, obj_down_gc_set)
        gc_ids.update(set(sub_down_obj_down_values.keys()))
        res['sub_down_obj_down'] = sub_down_obj_down_values

    return {'dea': dea_results,
            'group_comparisons': get_group_experiment_by_gc_ids(session, gc_ids),
            'bel_relations': get_bel_relations(relations, dea_results),
            'page': pagination.page,
            'page_size': pagination.page_size,
            'number_of_results': number_of_results,
            'pages': ceil(number_of_results / pagination.page_size)
            }


def get_bel_relations(relations: List[Relation], dea_results) -> List[dict]:
    """Create a list of dictionaries describing BEL edges that are associated with the gene symbols for some DEA.

    Parameters
    ----------
    relations : List[Relation]
    dea_results : dict

    Returns
    -------
    List of BEL relation metadata.
    """
    results = []
    for relation in relations:
        dea = dea_results[relation.sub][relation.obj]
        rel_dict = relation._asdict()
        same_direction = list(dea['sub_up_obj_up'].keys()) + list(dea['sub_down_obj_down'].keys())
        opposite_direction = list(dea['sub_up_obj_down'].keys()) + list(dea['sub_down_obj_up'].keys())
        if relation.rel in ['directly_increases', 'increases', 'positive_correlation']:
            rel_dict['supported_by'] = same_direction
            rel_dict['in_contradiction_to'] = opposite_direction
        elif relation.rel in ['directly_decreases', 'decreases', 'negative_correlation']:
            rel_dict['supported_by'] = opposite_direction
            rel_dict['in_contradiction_to'] = same_direction
        results.append(rel_dict)
    return results


def get_group_experiment_by_gc_ids(session, group_comparison_ids: Set[int]) -> dict:
    """Return a dictionary of experimental metadata for a given set of group comparison IDs.

    Parameters
    ----------
    session
        SQL session.
    group_comparison_ids : Set[int]
        Group comparison IDs.

    Returns
    -------
    Dictionary with group comparison ID as the keys and the associated experiment metadata as a value dictionary.
    """
    results = {}
    for group_comparison_id in group_comparison_ids:
        gc: GroupComparison = session.query(GroupComparison).filter_by(id=group_comparison_id).first()
        results[group_comparison_id] = {
            'experiment_id': gc.experiment.id,
            'experiment': gc.experiment.name,
            'experiment_title': gc.experiment.title,
            'group_comparison': gc.group_comparison,
            'group_comparison_title': gc.name
        }
    return results


def get_values_for_intersection(sub: List[ComparisonGroupValue],
                                obj: List[ComparisonGroupValue],
                                sub_gc_set: Set[int],
                                obj_gc_set: Set[int]) -> Dict[int, dict]:
    """Get the log2 fold changes and p values for the intersection of a given subject and object.

    Parameters
    ----------
    sub : List[ComparisonGroupValue]
    obj : List[ComparisonGroupValue]
    sub_gc_set : Set[int]
    obj_gc_set : Set[int]

    Returns
    -------
    Dictionary with group comparison ID as keys and the log2 fold changes + p values as a value dictionary.
    """
    sub_obj_gc_ids = sub_gc_set & obj_gc_set
    gc_sub_dict = {x.group_comparison_id: {'l2fc': x.log2foldchange, 'pv': x.p_value} for x in sub}
    gc_obj_dict = {x.group_comparison_id: {'l2fc': x.log2foldchange, 'pv': x.p_value} for x in obj}

    results = {}
    for sub_obj_gc_id in sub_obj_gc_ids:
        results[sub_obj_gc_id] = {'sub': gc_sub_dict[sub_obj_gc_id], 'obj': gc_obj_dict[sub_obj_gc_id]}
    return results
