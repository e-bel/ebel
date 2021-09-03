"""DrugBank API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestDrugbank:
    def test_get_by_id(self, client):
        response = client.get(
            'api/v1/drugbank/by_id?drugbank_id=DB00843',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {  # Only check a subset
            "cas_number": "120014-06-4",
            "drugbank_id": "DB00843",
            "name": "Donepezil",
        }

        assert isinstance(output, dict)
        assert all([output[key] == value for key, value in expected_results.items()])

    def test_get_drugbank(self, client):
        response = client.get(
            'api/v1/drugbank?drugbank_id=DB00843&name=Donepezil&description=%25Aricept%25&cas_number=120014-06-4&unii=8SSC91326P&state=solid&indication=%25mild%20to%20moderate%20Alzheimer%E2%80%99s%20Disease%25&pharmacodynamics=%25inhibiting%25&toxicity=%25rat%20oral%20LD50%25&metabolism=%25CYP3A4%25&absorption=%25gastrointestinal%20tract%25&half_life=%25hours%25&route_of_elimination=%25urine%25&volume_of_distribution=%25mg%20dose%25&clearance=%25plasma%25&mechanism_of_action=%25cognitive%20and%20behavioral%20decline%25&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {  # Only check a subset
            "cas_number": "120014-06-4",
            "drugbank_id": "DB00843",
            "name": "Donepezil",
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([hit[key] == value for key, value in expected_results.items()])

    def test_get_interaction(self, client):
        response = client.get(
            'api/v1/drugbank/interaction?drugbank_id=DB06605&name=Apixaban&description=%25hemorrhage%25&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_cols = ("description", "drugbank_id", "interactor_drugbank_id", "name")
        assert output[NUM_RESULTS] >= 150
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
        assert hit["name"] == "Apixaban"

    def test_get_pathway(self, client):
        response = client.get(
            'api/v1/drugbank/pathway?drugbank_id=DB00114&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_cols = ("drugbank_id", "smpdb_id")
        assert output[NUM_RESULTS] == 30
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
        assert hit["drugbank_id"] == "DB00114"

    def test_get_status(self, client):
        response = client.get(
            'api/v1/drugbank/status?drugbank_id=DB06605&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "drugbank_id": "DB06605",
          "smpdb_id": "approved"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_patent(self, client):
        response = client.get(
            'api/v1/drugbank/patent?drugbank_id=DB00843&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_cols = ("approved", "country", "drugbank_id", "expires", "number", "pediatric_extension")
        assert output[NUM_RESULTS] == 19
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
        assert hit["drugbank_id"] == "DB00843"

    def test_get_external_identifier(self, client):
        response = client.get(
            'api/v1/drugbank/external_identifier?drugbank_id=DB00114&resource=BindingDB&identifier=50118216&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "drugbank_id": "DB00114",
          "identifier": "50118216",
          "resource": "BindingDB"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_reference(self, client):
        response = client.get(
            'api/v1/drugbank/reference?drugbank_id=DB06605&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_cols = ("drugbank_id", "pmid")
        assert output[NUM_RESULTS] == 2
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
        assert hit["drugbank_id"] == "DB06605"
        assert hit["pmid"] == 18832478

    def test_get_target(self, client):
        response = client.get(
            'api/v1/drugbank/target?drugbank_id=DB06605&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "action": "inhibitor",
          "drugbank_id": "DB06605",
          "known_action": "yes",
          "uniprot": "P00742"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_product_name(self, client):
        response = client.get(
            'api/v1/drugbank/product_name?drugbank_id=DB06605&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_cols = ("drugbank_id", "name")
        assert output[NUM_RESULTS] == 3
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
        assert hit["drugbank_id"] == "DB06605"

    def test_get_synonym(self, client):
        response = client.get(
            'api/v1/drugbank/synonym?drugbank_id=DB06605&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_cols = ("drugbank_id", "synonym")
        assert output[NUM_RESULTS] == 3
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
        assert hit["drugbank_id"] == "DB06605"
        synonyms = set([x["synonym"] for x in results])
        assert all([syn in synonyms for syn in ("Apixaban", "apixabán", "apixabanum")])
