"""Reactome API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestReactome:
    def test_get_reactome(self, client):
        response = client.get(
            'api/v1/reactome?identifier=R-HSA-198933&uniprot_accession=P20138&organism=Homo%20sapiens&name=Immunoregulatory%20interactions%20between%20a%20Lymphoid%20and%20a%20non-Lymphoid%20cell&evidence_type=TAS&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "evidence_type": "TAS",
          "id": 140784,
          "identifier": "R-HSA-198933",
          "name": "Immunoregulatory interactions between a Lymphoid and a non-Lymphoid cell",
          "organism": "Homo sapiens",
          "uniprot_accession": "P20138"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
