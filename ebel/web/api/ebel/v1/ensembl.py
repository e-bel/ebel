"""EnsEMBL API methods."""
from ebel.manager.rdbms.models import ensembl
from ebel.web.api.ebel.v1 import _get_data


def get_ensembl():
    """Get generic ensembl entry."""
    return _get_data(ensembl.Ensembl)
