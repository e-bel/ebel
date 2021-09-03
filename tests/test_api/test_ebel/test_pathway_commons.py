"""Pathway Commons API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestPathwayCommons:
    def test_get_pathway_commons(self, client):
        response = client.get(
            'api/v1/pathway_commons?participant_a=CSF3&interaction_type=controls-expression-of&participant_b=CD33&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "id": 804357,
          "interaction_type": "controls-expression-of",
          "participant_a": "CSF3",
          "participant_b": "CD33",
          "pathway_names": [],
          "pmids": [
            12627849
          ],
          "sources": [
            "CTD"
          ]
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
            'api/v1/pathway_commons/by_gene_symbol?gene_symbol=CD33&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_cols = ("id", "interaction_type", "participant_a", "participant_b", "pathway_names", "pmids",
                         "sources")
        assert output[NUM_RESULTS] >= 19
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
        assert hit["participant_b"] == "CD33"

    def test_get_by_pathway_name(self, client):
        response = client.get(
            'api/v1/pathway_commons/by_pathway_name?pathway_name=Activation%20and%20oligomerization%20of%20BAK%20protein&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_result = {
          "id": 69305,
          "interaction_type": "in-complex-with",
          "participant_a": "BAK1",
          "participant_b": "BID",
          "pathway_names": [
            "Activation and oligomerization of BAK protein"
          ],
          "pmids": [],
          "sources": [
            "Reactome"
          ]
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_result

    def test_get_by_pmid(self, client):
        response = client.get(
            'api/v1/pathway_commons/by_pmid?pmid=12627849&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_cols = ("id", "interaction_type", "participant_a", "participant_b", "pathway_names", "pmids",
                         "sources")
        assert output[NUM_RESULTS] >= 6
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
        assert 12627849 in hit["pmids"]

    def test_get_pathway_name_starts_with(self, client):
        response = client.get(
            'api/v1/pathway_commons/pathway_name/starts_with?pathway_name=Activation%20and%20oligomerization%20of%20BAK&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        hit = output[RESULTS]

        assert isinstance(hit, dict)
        assert "Activation and oligomerization of BAK protein" in hit
        assert isinstance(hit["Activation and oligomerization of BAK protein"], int)
