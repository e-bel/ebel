"""UniProt API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestUniprot:
    def test_get_uniprot(self, client):
        response = client.get(
            'api/v1/uniprot?accession=P20138&gene_symbol=CD33&taxonomy_id=9606&keyword=Phosphoprotein&xref_db=ChEMBL&xref_id=CHEMBL1842&subcellular_location=Peroxisome&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_sample = {  # Only check a subset of data
            "accession": "P20138",
            "gene_names": [
                "CD33",
                "SIGLEC3"
            ],
            "gene_symbol": "CD33",
            "taxid": 9606,
            "name": "CD33_HUMAN",
            "organism": "Homo sapiens",
            "recommended_name": "Myeloid cell surface antigen CD33",
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([hit[key] == value for key, value in expected_sample.items()])

    def test_get_keyword_starts_with(self, client):
        response = client.get(
            'api/v1/uniprot/keyword/starts_with?keyword=Phago&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert "Phagocytosis" in results
        assert isinstance(results["Phagocytosis"], int)

    def test_get_subcellular_location_starts_with(self, client):
        response = client.get(
            'api/v1/uniprot/subcellular_location/starts_with?subcellular_location=Endo&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        assert output[NUM_RESULTS] == 10
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert "Endoplasmic reticulum-Golgi intermediate compartment" in results
        assert isinstance(results["Endoplasmic reticulum-Golgi intermediate compartment"], int)

    def test_get_gene_symbol_starts_with(self, client):
        response = client.get(
            'api/v1/uniprot/gene_symbol/starts_with?gene_symbol=CD18&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "CD180": 2690,
            "Cd180": 22498
        }
        assert output[NUM_RESULTS] == 2
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert results == expected_results

    def test_get_gene_starts_with(self, client):
        response = client.get(
            'api/v1/uniprot/gene/starts_with?gene=CD11&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "CD1176A": 294700,
            "CD11A": 1040093,
            "CD11B": 1040099,
            "CD11C": 1040111
        }
        assert output[NUM_RESULTS] == 4
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert results == expected_results

    def test_get_organism_starts_with(self, client):
        response = client.get(
            'api/v1/uniprot/organism/starts_with?organism=Homo%20sapiens&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "Homo sapiens": 9606,
            "Homo sapiens neanderthalensis": 63221
        }
        assert output[NUM_RESULTS] == 2
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert results == expected_results

    def test_get_function_starts_with(self, client):
        response = client.get(
            'api/v1/uniprot/function/starts_with?description=Phosphatase%202A&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "Phosphatase 2A affects a variety of biological processes in the cell such as transcription, cell cycle progression and cellular morphogenesis, and provides an initial identification of critical substrates for this phosphatase. The regulatory subunit may direct the catalytic subunit to distinct, albeit overlapping, subsets of substrates (By similarity).": 15,
            "Phosphatase 2A affects a variety of biological processes in the cell such as transcription, cell cycle progression and cellular morphogenesis, and provides an initial identification of critical substrates for this phosphatase. The regulatory subunit may direct the catalytic subunit to distinct, albeit overlapping, subsets of substrates.": 16
        }
        assert output[NUM_RESULTS] == 2
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert results == expected_results
