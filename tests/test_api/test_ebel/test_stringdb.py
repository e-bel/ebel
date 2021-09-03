"""StringDB API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestStringdb:
    def test_get_stringdb(self, client):
        response = client.get(
            'api/v1/string?protein1=9606.ENSP00000000412&protein2=9606.ENSP00000000233&symbol1=M6PR&symbol2=ARF5&neighborhood=0&neighborhood_transferred=0&fusion=0&cooccurence=0&homology=0&coexpression=82&coexpression_transferred=61&experiments=0&experiments_transferred=0&database=0&database_transferred=0&textmining=105&textmining_transferred=0&combined_score=161&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)

        expected_results = {
            "coexpression": 82,
            "coexpression_transferred": 61,
            "combined_score": 161,
            "cooccurence": 0,
            "database": 0,
            "database_transferred": 0,
            "experiments": 0,
            "experiments_transferred": 0,
            "fusion": 0,
            "homology": 0,
            "neighborhood": 0,
            "neighborhood_transferred": 0,
            "protein1": "9606.ENSP00000000412",
            "protein2": "9606.ENSP00000000233",
            "symbol1": "M6PR",
            "symbol2": "ARF5",
            "textmining": 105,
            "textmining_transferred": 0
        }

        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_stringdb_action(self, client):
        response = client.get(
            'api/v1/string/action?item_id_a=9606.ENSP00000216366&item_id_b=9606.ENSP00000000233&symbol1=AP4S1&symbol2=ARF5&mode=binding&score=165&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)

        expected_results = {
          "a_is_acting": False,
          "action": None,
          "is_directional": False,
          "item_id_a": "9606.ENSP00000216366",
          "item_id_b": "9606.ENSP00000000233",
          "mode": "binding",
          "score": 165,
          "symbol1": "AP4S1",
          "symbol2": "ARF5"
        }

        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

