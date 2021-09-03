"""DisGeNet API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS


class TestDisgenet:
    def test_get_sources(self, client):
        response = client.get(
            'api/v1/disgenet/sources',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_sources = ("BEFREE", "CGI", "CLINGEN", "CLINVAR", "CTD_human", "CTD_mouse", "CTD_rat",
                            "GENOMICS_ENGLAND", "GWASCAT", "GWASDB", "HPO", "LHGDN", "MGD", "ORPHANET", "PSYGENET",
                            "RGD", "UNIPROT")
        assert isinstance(output, dict)
        assert all([col in output for col in expected_sources])
        assert all([isinstance(val, int) for val in output.values()])

    def test_get_disease_name_starts_with(self, client):
        response = client.get(
            'api/v1/disgenet/disease_name/starts_with?disease_name=alz&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "ALZHEIMER DISEASE 10": "C1864828",
            "ALZHEIMER DISEASE 18": "C3810041",
            "ALZHEIMER DISEASE 19": "C3810349",
            "ALZHEIMER DISEASE 2": "C1863051",
            "ALZHEIMER DISEASE 4": "C1847200",
            "ALZHEIMER DISEASE 5": "C1865868",
            "ALZHEIMER DISEASE 6, LATE-ONSET": "C1854187",
            "Alzheimer Disease 12": "C1970209",
            "Alzheimer Disease 14": "C1970144",
            "Alzheimer Disease 7": "C1853555"
        }
        assert output[NUM_RESULTS] >= 26
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert results == expected_results

    def test_get_gene_symbol_starts_with(self, client):
        response = client.get(
            'api/v1/disgenet/gene_symbol/starts_with?gene_symbol=CD18&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {"CD180": 4064}
        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert results == expected_results

    def test_get_gene_disease_pmid_associations(self, client):
        response = client.get(
            'api/v1/disgenet/gene_disease_pmid_associations?gene_id=945&gene_symbol=CD33&disease_id=C0023418&disease_name=leukemia&pmid=15388576&source=LHGDN&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "disease_id": "C0023418",
          "disease_name": "leukemia",
          "gene_id": 945,
          "gene_symbol": "CD33",
          "pmid": 15388576,
          "score": 0.1,
          "source": "LHGDN"
        }
        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_variant_disease_pmid_associations(self, client):
        response = client.get(
            'api/v1/disgenet/variant_disease_pmid_associations?snp_id=rs1001179&chromosome=11&position=34438684&disease_id=C0002395&disease_name=Alzheimer%27s%20Disease&pmid=18248894&source=BEFREE&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "chromosome": "11",
          "disease_id": "C0002395",
          "disease_name": "Alzheimer's Disease",
          "pmid": 18248894,
          "position": 34438684,
          "score": 0.01,
          "snp_id": "rs1001179",
          "source": "BEFREE"
        }
        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_ebel_has_snp_disgenet(self, client):
        response = client.get(
            'api/v1/disgenet/ebel?disease_name=Alzheimer%27s%20Disease&rs_number=rs10408847&pmid=29777097&source=GWASCAT&gene_symbol=MARK4&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expect_cols = ("disease_name", "gene_symbol", "pmids", "relation", "rs_number", "score", "source")
        assert output[NUM_RESULTS] > 0
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expect_cols])
