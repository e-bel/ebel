"""CHEBI API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS


class TestChebi:
    def test_get_compound_by_name(self, client):
        response = client.get(
            'api/v1/chebi/compound/by_name?name=donepezil',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {  # only check some of the generated information
            "source": "ChEBI",
            "status": "C",
            "chebi_accession": "CHEBI:53289",
            "name": "donepezil",
        }
        assert isinstance(output, list)
        hit = output[0]
        assert isinstance(hit, dict)
        for key, value in expected_results.items():
            assert key in hit
            assert hit[key] == value

    def test_get_compound_name_by_name_starts_with(self, client):
        response = client.get(
            'api/v1/chebi/compound_name/by_name_starts_with?name=donep',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "donepezil": 53289,
            "donepezil (1+)": 145498,
            "donepezil hydrochloride": 4696
        }
        assert isinstance(output, dict)
        assert expected_results == output

    def test_get_compound_by_id(self, client):
        response = client.get(
            'api/v1/chebi/compound/by_id?id=53289',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {  # only check some of the generated information
            "source": "ChEBI",
            "status": "C",
            "chebi_accession": "CHEBI:53289",
            "name": "donepezil",
        }
        assert isinstance(output, dict)
        for key, value in expected_results.items():
            assert key in output
            assert output[key] == value

    def test_get_compound_by_other_db_accession(self, client):
        response = client.get(
            'api/v1/chebi/compound/by_other_db_accession?db_name=DrugBank%20accession&accession_number=DB00843',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {  # only check some of the generated information
            "status": "C",
            "chebi_accession": "CHEBI:4696",
            "name": "donepezil hydrochloride",
        }
        assert isinstance(output, list)
        hit = output[0]
        assert isinstance(hit, dict)
        for key, value in expected_results.items():
            assert key in hit
            assert hit[key] == value

    def test_get_compound_reference(self, client):
        response = client.get(
            'api/v1/chebi/compound_reference?reference_id=US2006025345&reference_db_name=Patent&reference_name=Substituted%20ethane-1%2C2-diamines%20for%20the%20treatment%20of%20Alzheimer%27s%20disease&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "compound_id": 17596,
          "location_in_ref": None,
          "reference_db_name": "Patent",
          "reference_id": "US2006025345",
          "reference_name": "Substituted ethane-1,2-diamines for the treatment of Alzheimer's disease"
        }
        assert output[NUM_RESULTS] > 20
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_relation(self, client):
        response = client.get(
            'api/v1/chebi/relation?final_id=53289',
            content_type='application/json'
        )
        output = format_response_data(response)
        assert isinstance(output, list)
        assert len(output) > 0
        first_entry = output[0]
        expected_cols = ["final_id", "init_id", "status", "type"]
        assert all([col in first_entry for col in expected_cols])

    def test_get_bel_chebi_ids(self, client):
        response = client.get(
            'api/v1/chebi/ebel/nodes?name=ATP&namespace=CHEBI&chebi=15422&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        assert isinstance(output, dict)
        results = output[RESULTS]
        assert isinstance(results, list)
        assert len(output) >= 5
        hit = results[0]
        assert all([col in hit for col in ('bel', 'chebi', 'name', 'namespace', 'rid')])
        assert hit['name'] == "ATP"
        assert hit["chebi"] == 15422
