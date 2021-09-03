"""IUPHAR API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


example_result = {
    "action": "Inhibition",
    "action_comment": None,
    "affinity_high": None,
    "affinity_low": None,
    "affinity_median": 8.77,
    "affinity_units": "pIC50",
    "approved_drug": "0",
    "assay_description": None,
    "concentration_range": None,
    "endogenous": False,
    "id": 9631,
    "ligand": "ACY-738",
    "ligand_context": None,
    "ligand_gene_symbol": None,
    "ligand_id": 11120,
    "ligand_pubchem_sid": 434122180,
    "ligand_species": None,
    "original_affinity_high_nm": None,
    "original_affinity_low_nm": None,
    "original_affinity_median_nm": 1.7,
    "original_affinity_relation": "=",
    "original_affinity_units": "IC50",
    "primary_target": False,
    "pubmed_id": "23954848",
    "receptor_site": None,
    "selectivity": "Not Determined",
    "target": "histone deacetylase 6",
    "target_ensembl_gene_id": "ENSG00000094631",
    "target_gene_symbol": "HDAC6",
    "target_id": 2618,
    "target_ligand": None,
    "target_ligand_ensembl_gene_id": None,
    "target_ligand_gene_symbol": None,
    "target_ligand_id": None,
    "target_ligand_pubchem_sid": None,
    "target_ligand_uniprot": None,
    "target_species": "Human",
    "target_uniprot": "Q9UBN7",
    "type": "Inhibitor"
}


class TestIuphar:
    def test_get_interaction(self, client):
        response = client.get(
            'api/v1/iuphar/interaction?target=CD33&target_id=2601&target_gene_symbol=CD33&target_uniprot=P20138&target_ensembl_gene_id=ENSG00000105383&target_species=Human&ligand=gemtuzumab%20ozogamicin&ligand_id=6775&ligand_pubchem_sid=178103381&approved_drug=1&type=Antibody&action=Binding&selectivity=Selective&primary_target=true&original_affinity_relation=%3D&pubmed_id=10720144&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "action": "Binding",
          "action_comment": None,
          "affinity_high": None,
          "affinity_low": None,
          "affinity_median": None,
          "affinity_units": "-",
          "approved_drug": "1",
          "assay_description": None,
          "concentration_range": None,
          "endogenous": False,
          "id": 4512,
          "ligand": "gemtuzumab ozogamicin",
          "ligand_context": None,
          "ligand_gene_symbol": None,
          "ligand_id": 6775,
          "ligand_pubchem_sid": 178103381,
          "ligand_species": None,
          "original_affinity_high_nm": None,
          "original_affinity_low_nm": None,
          "original_affinity_median_nm": None,
          "original_affinity_relation": "=",
          "original_affinity_units": "-",
          "primary_target": True,
          "pubmed_id": "10720144",
          "receptor_site": None,
          "selectivity": "Selective",
          "target": "CD33",
          "target_ensembl_gene_id": "ENSG00000105383",
          "target_gene_symbol": "CD33",
          "target_id": 2601,
          "target_ligand": None,
          "target_ligand_ensembl_gene_id": None,
          "target_ligand_gene_symbol": None,
          "target_ligand_id": None,
          "target_ligand_pubchem_sid": None,
          "target_ligand_uniprot": None,
          "target_species": "Human",
          "target_uniprot": "P20138",
          "type": "Antibody"
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_ligandby_by_id(self, client):
        response = client.get(
            'api/v1/iuphar/ligand/by_id?id=1',
            content_type='application/json'
        )
        output = format_response_data(response)

        expected_result = {
          "approved": None,
          "gto_immu_pdb": None,
          "gto_mpdb": None,
          "id": 1,
          "inchi": "InChI=1S/C22H26FN3O4/c23-17-6-4-16(5-7-17)22(28)24-8-9-25-10-12-26(13-11-25)19-2-1-3-20-21(19)29-15-18(14-27)30-20/h1-7,18,27H,8-15H2,(H,24,28)/t18-/m0/s1",
          "inchi_key": "NYSDRDDQELAVKP-SFHVURJKSA-N",
          "inn": "flesinoxan",
          "iupac_name": "4-fluoro-N-[2-[4-[(3S)-3-(hydroxymethyl)-2,3-dihydro-1,4-benzodioxin-8-yl]piperazin-1-yl]ethyl]benzamide",
          "labelled": None,
          "name": "flesinoxan",
          "pubchem_cid": "57347",
          "pubchem_sid": 135650267,
          "radioactive": None,
          "smiles": "OC[C@H]1COc2c(O1)cccc2N1CCN(CC1)CCNC(=O)c1ccc(cc1)F",
          "species": None,
          "synonyms": "(+)-flesinoxan|DU-29,373",
          "type": "Synthetic organic",
          "uniprot_id": None,
          "withdrawn": None
        }
        assert isinstance(output, dict)
        assert output == expected_result

    def test_get_interaction_by_target_uniprot(self, client):
        response = client.get(
            'api/v1/iuphar/interaction/by_target_uniprot?target_uniprot=P20138&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)

        expected_cols = example_result.keys()
        assert output[NUM_RESULTS] >= 3
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])

    def test_get_interaction_by_target_gene_symbol(self, client):
        response = client.get(
            'api/v1/iuphar/interaction/by_target_gene_symbol?target_gene_symbol=HDAC6&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)

        expected_cols = example_result.keys()
        assert output[NUM_RESULTS] >= 3
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert all([col in hit for col in expected_cols])
