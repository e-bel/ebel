"""HGNC API methods."""
from flask import request

from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import hgnc
from ebel.web.api.ebel.v1 import _get_data


def get_by_symbol():
    """Get paginated list of HGNC entries by given gene symbol."""
    symbol = request.args.get('symbol')
    if symbol:
        db_entry = RDBMS.get_session().query(hgnc.Hgnc).filter_by(symbol=symbol).first()
        if db_entry:
            return db_entry.as_dict()


def get_uniprot_accession_by_hgnc_symbol():
    """Return UniProt accession number by HGCN gene symbol."""
    symbol = request.args.get('symbol')
    if symbol:
        db_entry = RDBMS.get_session().query(hgnc.Hgnc).filter_by(symbol=symbol).first()
        if db_entry:
            return db_entry.uniprots[0].accession


def get_hgnc():
    """Get paginated list of HGNC entries."""
    return _get_data(hgnc.Hgnc)


def get_gene_group_name():
    """Get paginated list of HGNC entries."""
    return _get_data(hgnc.GeneGroupName)
