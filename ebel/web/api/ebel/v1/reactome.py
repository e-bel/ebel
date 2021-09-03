"""Reactome API methods."""

from flask import request

from ebel.manager.rdbms.models import reactome
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_ebel_query_result


def get_reactome():
    """Get generic Reactome entry."""
    return _get_data(reactome.Reactome)


def get_bel_node_by_pathway_name():
    """Get Reactome related eBEL nodes by pathway name."""
    pathway_name = request.args.get('pathway_name')
    sql = f'''SELECT
            @rid.asString() as rid,
            namespace,
            name,
            bel,
            reactome_pathways
        FROM
            protein
        WHERE
            pure=true AND
            "{pathway_name}" in reactome_pathways
    '''
    return _get_paginated_ebel_query_result(sql)
