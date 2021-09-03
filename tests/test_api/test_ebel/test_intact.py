"""IntAct API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestIntAct:
    def test_get_by_uniprot(self, client):
        response = client.get(
            'api/v1/intact?confidence_value=0.56&detection_method=two%20hybrid%20array&detection_method_psimi_id=397&int_a_uniprot_id=P20138&int_b_uniprot_id=Q9Y5Z9&interaction_ids=%25EBI-23994924%25&interaction_type=physical%20association&interaction_type_psimi_id=915&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "confidence_value": 0.56,
          "detection_method": "two hybrid array",
          "detection_method_psimi_id": 397,
          "id": 681219,
          "int_a_uniprot_id": "P20138",
          "int_b_uniprot_id": "Q9Y5Z9",
          "interaction_ids": "intact:EBI-23994924|imex:IM-25472-94969",
          "interaction_type": "physical association",
          "interaction_type_psimi_id": 915,
          "pmid": 32296183
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
