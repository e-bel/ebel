"""NSIDES API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestNsides:
    def test_get_nsides(self, client):
        response = client.get(
            'api/v1/nsides?drug_rxnorn_id=4024&drug_concept_name=ergoloid%20mesylates%2C%20USP&condition_meddra_id=10002034&condition_concept_name=Anaemia&a=6&b=126&c=21&d=1299&prr=2.85714&prr_error=0.45382&mean_reporting_frequency=0.0454545&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "a": 6,
            "b": 126,
            "c": 21,
            "condition_concept_name": "Anaemia",
            "condition_meddra_id": 10002034,
            "d": 1299,
            "drug_concept_name": "ergoloid mesylates, USP",
            "drug_rxnorn_id": "4024",
            "id": 1,
            "mean_reporting_frequency": 0.0454545,
            "prr": 2.85714,
            "prr_error": 0.45382,
            "source": "offsides"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
