"""NCBI API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


# class TestNcbi:
#     def test_get_gene_by_go(self, client):
#         response = client.get(
#             'api/v1/ebel/ncbi/gene/by_go?tax_id=9606&gene_id=945&go_id=GO%3A0002765&evidence=IDA&qualifier=involved_in&go_term=immune%20response-inhibiting%20signal%20transduction&category=Process&page_size=10&page=1',
#             content_type='application/json'
#         )
#         output = format_response_data(response)
#         expected_results = {
#             "confidence_value": 0.56,
#             "detection_method": "two hybrid array",
#             "detection_method_psimi_id": 397,
#             "id": 681219,
#             "int_a_uniprot_id": "P20138",
#             "int_b_uniprot_id": "Q9Y5Z9",
#             "interaction_ids": "intact:EBI-23994924|imex:IM-25472-94969",
#             "interaction_type": "physical association",
#             "interaction_type_psimi_id": 915,
#             "pmid": 32296183
#         }
#         assert output[NUM_RESULTS] == 1
#         assert output[PAGE_SIZE] == 10
#         results = output[RESULTS]
#         assert isinstance(results, list)
#         hit = results[0]
#         assert isinstance(hit, dict)
#         assert hit == expected_results
#
#     def test_get_gene_by_mim(self, client):
#         response = client.get(
#             'api/v1/ebel/ncbi/gene/by_mim?mim_number=159590&gene_id=945&type=gene&page_size=10&page=1',
#             content_type='application/json'
#         )
#         output = format_response_data(response)
#         expected_results = {
#             "confidence_value": 0.56,
#             "detection_method": "two hybrid array",
#             "detection_method_psimi_id": 397,
#             "id": 681219,
#             "int_a_uniprot_id": "P20138",
#             "int_b_uniprot_id": "Q9Y5Z9",
#             "interaction_ids": "intact:EBI-23994924|imex:IM-25472-94969",
#             "interaction_type": "physical association",
#             "interaction_type_psimi_id": 915,
#             "pmid": 32296183
#         }
#         assert output[NUM_RESULTS] == 1
#         assert output[PAGE_SIZE] == 10
#         results = output[RESULTS]
#         assert isinstance(results, list)
#         hit = results[0]
#         assert isinstance(hit, dict)
#         assert hit == expected_results
#
#     def test_get_gene_by_ensembl(self, client):
#         response = client.get(
#             'api/v1/ebel/ncbi/gene/by_ensembl?tax_id=9606&gene_id=945&ensembl_gene_identifier=ENSG00000105383&rna_nucleotide_accession_version=NM_001082618.2&ensembl_rna_identifier=ENST00000421133.6&protein_accession_version=NP_001076087.1&ensembl_protein_identifier=ENSP00000410126.1&page_size=10&page=1',
#             content_type='application/json'
#         )
#         output = format_response_data(response)
#         expected_results = {
#             "confidence_value": 0.56,
#             "detection_method": "two hybrid array",
#             "detection_method_psimi_id": 397,
#             "id": 681219,
#             "int_a_uniprot_id": "P20138",
#             "int_b_uniprot_id": "Q9Y5Z9",
#             "interaction_ids": "intact:EBI-23994924|imex:IM-25472-94969",
#             "interaction_type": "physical association",
#             "interaction_type_psimi_id": 915,
#             "pmid": 32296183
#         }
#         assert output[NUM_RESULTS] == 1
#         assert output[PAGE_SIZE] == 10
#         results = output[RESULTS]
#         assert isinstance(results, list)
#         hit = results[0]
#         assert isinstance(hit, dict)
#         assert hit == expected_results
#
#     def test_get_gene_info(self, client):
#         response = client.get(
#             'api/v1/ebel/ncbi/gene/info?gene_id=945&tax_id=9606&symbol=CD33&type_of_gene=protein-coding&chromosome=19&map_location=19q13.41&page_size=10&page=1',
#             content_type='application/json'
#         )
#         output = format_response_data(response)
#         expected_results = {
#             "confidence_value": 0.56,
#             "detection_method": "two hybrid array",
#             "detection_method_psimi_id": 397,
#             "id": 681219,
#             "int_a_uniprot_id": "P20138",
#             "int_b_uniprot_id": "Q9Y5Z9",
#             "interaction_ids": "intact:EBI-23994924|imex:IM-25472-94969",
#             "interaction_type": "physical association",
#             "interaction_type_psimi_id": 915,
#             "pmid": 32296183
#         }
#         assert output[NUM_RESULTS] == 1
#         assert output[PAGE_SIZE] == 10
#         results = output[RESULTS]
#         assert isinstance(results, list)
#         hit = results[0]
#         assert isinstance(hit, dict)
#         assert hit == expected_results
#
#     def test_get_medgen(self, client):
#         response = client.get(
#             'api/v1/ebel/ncbi/medgen?cui=C4021990&name=Abnormality%20of%20the%20microglia&source=GTR&suppress=N&page_size=10&page=1',
#             content_type='application/json'
#         )
#         output = format_response_data(response)
#         expected_results = {
#             "confidence_value": 0.56,
#             "detection_method": "two hybrid array",
#             "detection_method_psimi_id": 397,
#             "id": 681219,
#             "int_a_uniprot_id": "P20138",
#             "int_b_uniprot_id": "Q9Y5Z9",
#             "interaction_ids": "intact:EBI-23994924|imex:IM-25472-94969",
#             "interaction_type": "physical association",
#             "interaction_type_psimi_id": 915,
#             "pmid": 32296183
#         }
#         assert output[NUM_RESULTS] == 1
#         assert output[PAGE_SIZE] == 10
#         results = output[RESULTS]
#         assert isinstance(results, list)
#         hit = results[0]
#         assert isinstance(hit, dict)
#         assert hit == expected_results
#
#     def test_get_medgen_by_pmid(self, client):
#         response = client.get(
#             'api/v1/ebel/ncbi/medgen/by_pmid?pmid=29856956&page_size=10&page=1',
#             content_type='application/json'
#         )
#         output = format_response_data(response)
#         expected_results = {
#             "confidence_value": 0.56,
#             "detection_method": "two hybrid array",
#             "detection_method_psimi_id": 397,
#             "id": 681219,
#             "int_a_uniprot_id": "P20138",
#             "int_b_uniprot_id": "Q9Y5Z9",
#             "interaction_ids": "intact:EBI-23994924|imex:IM-25472-94969",
#             "interaction_type": "physical association",
#             "interaction_type_psimi_id": 915,
#             "pmid": 32296183
#         }
#         assert output[NUM_RESULTS] == 1
#         assert output[PAGE_SIZE] == 10
#         results = output[RESULTS]
#         assert isinstance(results, list)
#         hit = results[0]
#         assert isinstance(hit, dict)
#         assert hit == expected_results
#
#     def test_get_go_by_pmid(self, client):
#         response = client.get(
#             'api/v1/ebel/ncbi/gene/go/by_pmid?pmid=10887109&page_size=10&page=1',
#             content_type='application/json'
#         )
#         output = format_response_data(response)
#         expected_results = {
#             "confidence_value": 0.56,
#             "detection_method": "two hybrid array",
#             "detection_method_psimi_id": 397,
#             "id": 681219,
#             "int_a_uniprot_id": "P20138",
#             "int_b_uniprot_id": "Q9Y5Z9",
#             "interaction_ids": "intact:EBI-23994924|imex:IM-25472-94969",
#             "interaction_type": "physical association",
#             "interaction_type_psimi_id": 915,
#             "pmid": 32296183
#         }
#         assert output[NUM_RESULTS] == 1
#         assert output[PAGE_SIZE] == 10
#         results = output[RESULTS]
#         assert isinstance(results, list)
#         hit = results[0]
#         assert isinstance(hit, dict)
#         assert hit == expected_results
