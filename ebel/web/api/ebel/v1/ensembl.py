"""EnsEMBL API methods."""
from ebel.web.api.ebel.v1 import _get_data
from ebel.manager.rdbms.models import ensembl


def get_ensembl():
    """Get generic ensembl entry."""
    return _get_data(ensembl.Ensembl)
