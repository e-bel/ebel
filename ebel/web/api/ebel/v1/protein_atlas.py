"""Protein Atlas API methods."""
from ebel.web.api.ebel.v1 import _get_data
from ebel.manager.rdbms.models import protein_atlas


def get_rna_brain_fantom():
    """Get RNA from mouse brain - FANTOM."""
    return _get_data(protein_atlas.ProteinAtlasRnaBrainFantom)


def get_rna_mouse_brain_allen():
    """Get RNA from mouse brain - ALLEN."""
    return _get_data(protein_atlas.ProteinAtlasRnaMouseBrainAllen)


def get_normal_tissue():
    """Get normal tissues."""
    return _get_data(protein_atlas.ProteinAtlasNormalTissue)


def get_subcellular_location():
    """Get subcellular location."""
    return _get_data(protein_atlas.ProteinAtlasSubcellularLocation)


def get_rna_tissue_consensus():
    """Get RNA tissue consensus."""
    return _get_data(protein_atlas.ProteinAtlasRnaTissueConsensus)


def get_rna_brain_gtex():
    """Get RNA Brain GTEX."""
    return _get_data(protein_atlas.ProteinAtlasRnaBrainGtex)
