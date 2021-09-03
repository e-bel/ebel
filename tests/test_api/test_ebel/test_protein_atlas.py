"""Protein Atlas API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestProteinAtlas:
    def test_get_rna_brain_fantom(self, client):
        response = client.get(
            'api/v1/ebel/protein_atlas/rna_brain_fantom?gene=ENSG00000105383&gene_name=CD33&brain_region=amygdala&tags_per_million=10.7&scaled_tags_per_million=12.4&nx=3.6&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "brain_region": "amygdala",
          "gene": "ENSG00000105383",
          "gene_name": "CD33",
          "nx": "3.6",
          "scaled_tags_per_million": "12.4",
          "tags_per_million": "10.7"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_rna_mouse_brain_allen(self, client):
        response = client.get(
            'api/v1/ebel/protein_atlas/rna_mouse_brain_allen?gene=ENSG00000095970&gene_name=TREM2&brain_region=amygdala&expression_energy=0.5&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "brain_region": "amygdala",
          "expression_energy": 0.5,
          "gene": "ENSG00000095970",
          "gene_name": "TREM2"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_normal_tissue(self, client):
        response = client.get(
            'api/v1/ebel/protein_atlas/normal_tissue?gene=ENSG00000105383&gene_name=CD33&tissue=adipose%20tissue&cell_type=adipocytes&level=Not%20detected&reliability=Approved&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "cell_type": "adipocytes",
          "gene": "ENSG00000105383",
          "gene_name": "CD33",
          "level": "Not detected",
          "reliability": "Approved",
          "tissue": "adipose tissue"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_subcellular_location(self, client):
        response = client.get(
            'api/v1/ebel/protein_atlas/rna_subcellular_location?gene=ENSG00000105383&gene_name=CD33&reliability=Approved&main_location=Nucleoplasm%3BPlasma%20membrane&supported=Plasma%20membrane&uncertain=Nucleoplasm&go_id=Nucleoplasm%20%28GO%3A0005654%29%3BPlasma%20membrane%20%28GO%3A0005886%29&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "additional_location": None,
          "approved": None,
          "cell_cycle_dependency": None,
          "enhanced": None,
          "extracellular_location": None,
          "gene": "ENSG00000105383",
          "gene_name": "CD33",
          "go_id": "Nucleoplasm (GO:0005654);Plasma membrane (GO:0005886)",
          "main_location": "Nucleoplasm;Plasma membrane",
          "reliability": "Approved",
          "single_cell_variation_intensity": None,
          "single_cell_variation_spatial": None,
          "supported": "Plasma membrane",
          "uncertain": "Nucleoplasm"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_rna_tissue_consensus(self, client):
        response = client.get(
            'api/v1/ebel/protein_atlas/rna_tissue_consensus?gene=ENSG00000105383&gene_name=CD33&tissue=adipose%20tissue&nx=10.2&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "gene": "ENSG00000105383",
          "gene_name": "CD33",
          "nx": 10.2,
          "tissue": "adipose tissue"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_rna_brain_gtex(self, client):
        response = client.get(
            'api/v1/ebel/protein_atlas/rna_brain_gtex?gene=ENSG00000000003&gene_name=TSPAN6&brain_region=amygdala&tpm=7.3&p_tpm=9.0&nx=7.0&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "brain_region": "amygdala",
          "gene": "ENSG00000000003",
          "gene_name": "TSPAN6",
          "nx": 7,
          "p_tpm": 9,
          "tpm": 7.3
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
