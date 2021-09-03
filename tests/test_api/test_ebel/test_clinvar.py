"""ClinVAR API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestClinvar:

    def test_get_clinvar(self, client):
        response = client.get(
            'api/v1/clinvar?allele_id=705202&type=single%20nucleotide%20variant&name=NM_001772.4%28CD33%29%3Ac.131T%3EC%20%28p.Phe44Ser%29&gene_id=945&gene_symbol=CD33&hgnc_id=HGNC%3A1659&clinical_significance=Benign&last_evaluated=Jul%2016%2C%202018&rs_db_snp=61736469&rcvaccession=RCV000957991&origin=germline&origin_simple=germline&assembly=GRCh37&chromosome_accession=NC_000019.9&chromosome=19&start=51728567&stop=51728567&reference_allele=na&alternate_allele=na&cytogenetic=19q13.41&review_status=criteria%20provided%2C%20single%20submitter&number_submitters=1&tested_in_gtr=N&submitter_categories=2&variation_id=777507&position_vcf=51728567&reference_allele_vcf=T&alternate_allele_vcf=C&page_size=10&page=1',
            content_type='application/json'
        )

        output = format_response_data(response)

        expected_results = {
          "allele_id": 705202,
          "alternate_allele": "na",
          "alternate_allele_vcf": "C",
          "assembly": "GRCh37",
          "chromosome": "19",
          "chromosome_accession": "NC_000019.9",
          "clin_sig_simple": 0,
          "clinical_significance": "Benign",
          "cytogenetic": "19q13.41",
          "gene_id": 945,
          "gene_symbol": "CD33",
          "guidelines": None,
          "hgnc_id": "HGNC:1659",
          "id": 1132137,
          "last_evaluated": "Jul 16, 2018",
          "name": "NM_001772.4(CD33):c.131T>C (p.Phe44Ser)",
          "nsv_esv_db_var": None,
          "number_submitters": 1,
          "origin": "germline",
          "origin_simple": "germline",
          "otherIdentifiers": [],
          "phenotypeMedgens": [
            "CN517202"
          ],
          "position_vcf": 51728567,
          "rcvaccession": "RCV000957991",
          "reference_allele": "na",
          "reference_allele_vcf": "T",
          "review_status": "criteria provided, single submitter",
          "rs_db_snp": 61736469,
          "start": 51728567,
          "stop": 51728567,
          "submitter_categories": 2,
          "tested_in_gtr": "N",
          "type": "single nucleotide variant",
          "variation_id": 777507
        }

        assert output[NUM_RESULTS] == 1
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_clinvar_simple(self, client):
        response = client.get(
            'api/v1/clinvar/simple?phenotype=Alzheimer%20disease%202&hgnc_id=HGNC%3A4886&assembly=GRCh38&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "allele_id": 15048,
            "assembly": "GRCh38",
            "gene_symbol": "HFE",
            "hgnc_id": "HGNC:4886",
            "id": 14,
            "rs_db_snp": 1800562
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_phenotype_starts_with(self, client):
        response = client.get(
            'api/v1/clinvar/phenotype/starts_with?phenotype=MAN1B1-Related%20Disor&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, dict)
        assert "MAN1B1-Related Disorders" in results
        assert results["MAN1B1-Related Disorders"] >= 6899  # Value changes depending on when data was downloaded

    def test_get_by_other_identifier(self, client):
        response = client.get(
            'api/v1/clinvar/phenotype/by_other_identifier?db=OMIM&identifier=613653.%25&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "allele_id": 15041,
          "assembly": "GRCh37",
          "db": "OMIM",
          "gene_symbol": "AP5Z1",
          "hgnc_id": "HGNC:22197",
          "id": 1,
          "identifier": "613653.0001",
          "rs_db_snp": 397704705
        }
        assert output[NUM_RESULTS] > 10
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_by_medgen(self, client):
        response = client.get(
            'api/v1/clinvar/phenotype/by_medgen?identifier=C0002395&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "allele_id": 15048,
          "assembly": "GRCh37",
          "gene_symbol": "HFE",
          "hgnc_id": "HGNC:4886",
          "id": 13,
          "identifier": "C0002395",
          "rs_db_snp": 1800562
        }
        assert output[NUM_RESULTS] > 300
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
