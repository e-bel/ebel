"""NCBI API methods."""

from flask import request

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import ncbi
from ebel.web.api.ebel.v1 import _get_data, _get_paginated_query_result


def get_gene_by_go():
    """Get gene information using GO."""
    return _get_data(ncbi.NcbiGeneGo)


def get_gene_by_mim():
    """Get gene information using MIM."""
    return _get_data(ncbi.NcbiGeneMim)


def get_gene_by_ensembl():
    """Get gene information using EnsEMBL."""
    return _get_data(ncbi.NcbiGeneEnsembl)


def get_gene_info():
    """Get gene information."""
    return _get_data(ncbi.NcbiGeneInfo)


def get_medgen():
    """Get MedGen terms."""
    return _get_data(ncbi.NcbiMedGenName)


def get_medgen_by_pmid():
    """Get MedGen terms by PMID."""
    n = ncbi.NcbiMedGenName
    p = ncbi.NcbiMedGenPmid
    q = RDBMS.get_session().query(n.cui, n.name).join(p).filter_by(pmid=request.args.get('pmid'))
    return _get_paginated_query_result(q, return_dict=True)


def get_go_by_pmid():
    """Get gene ontology by PMID."""
    q = RDBMS.get_session().query(ncbi.NcbiGeneGo).join(ncbi.NcbiGeneGoPmid).filter_by(pmid=request.args.get('pmid'))
    return _get_paginated_query_result(q, print_sql=True)
