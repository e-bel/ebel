"""KEGG API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestKegg:
    def test_get_kegg(self, client):
        response = client.get(
            'api/v1/kegg?pathway_identifier=hsa05010&pathway_name=Alzheimer%20disease&kegg_species_id=hsa&kegg_gene_id_a=hsa%3A4137&gene_symbol_a=MAPT&kegg_gene_id_b=hsa%3A100532726&gene_symbol_b=NDUFC2-KCTD14&kegg_int_type=PPrel&interaction_type=inhibition&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "gene_symbol_a": "MAPT",
          "gene_symbol_b": "NDUFC2-KCTD14",
          "id": 95841,
          "interaction_type": "inhibition",
          "kegg_gene_id_a": "hsa:4137",
          "kegg_gene_id_b": "hsa:100532726",
          "kegg_int_type": "PPrel",
          "kegg_species_id": "hsa",
          "pathway_identifier": "hsa05010",
          "pathway_name": "Alzheimer disease"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_by_gene_symbol(self, client):
        response = client.get(
            'api/v1/kegg/by_gene_symbol?gene_symbol=CD19&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        example_results = {  # Copy/paste example results to get col names quickly
            "gene_symbol_a": "MAPT",
            "gene_symbol_b": "NDUFC2-KCTD14",
            "id": 95841,
            "interaction_type": "inhibition",
            "kegg_gene_id_a": "hsa:4137",
            "kegg_gene_id_b": "hsa:100532726",
            "kegg_int_type": "PPrel",
            "kegg_species_id": "hsa",
            "pathway_identifier": "hsa05010",
            "pathway_name": "Alzheimer disease"
        }
        assert output[NUM_RESULTS] >= 36
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in example_results.keys()])
