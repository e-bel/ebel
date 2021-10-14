"""GWAS Catalog API methods."""
from flask import request

from ebel.manager.rdbms.models import gwas_catalog
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_ebel_query_result


def get_gwas_catalog():
    """Get egenric GWAS catalog entry."""
    return _get_data(gwas_catalog.GwasCatalog)


def get_ebel_relation():
    """Get GWAS Catalog related eBEL relations."""
    allowed_relations = ['has_snp_gwascatalog',
                         'has_mapped_snp_gc',
                         'has_downstream_snp_gc',
                         'has_upstream_snp_gc']
    relation = request.args.get('relation')
    relation = relation if relation in allowed_relations else allowed_relations[0]

    conf = {
        'snp_rid': "in.@rid.asString()",
        'namespace': "out.namespace",
        'name': "out.name",
        'gene_rid': "out.@rid.asString()",
        'pubmed_id': "pubmed_id",
        'disease_trait': "disease_trait",
        'rs_number': "in.rs_number",
        'edge_rid': "@rid.asString()"
    }

    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += f" FROM {relation}"

    ra = request.args
    paras = {k: ra[k] for k in ra if k in conf}
    if paras:
        sql += " WHERE " + ' AND '.join([f'{conf[k]} like "{v}"' for k, v in paras.items()])

    return _get_paginated_ebel_query_result(sql, print_sql=True)
