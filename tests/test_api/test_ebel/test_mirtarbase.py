"""miRTarBase API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestMirTarBase:
    def test_get_mirtarbase(self, client):
        response = client.get(
            'api/v1/mirtarbase?mi_rtar_base_id=MIRT019168&mi_rna=hsa-miR-335-5p&species_mi_rna=Homo%20sapiens&target_gene=CD33&target_gene_entrez_id=945&species_target_gene=Homo%20sapiens&experiments=Microarray&support_type=Functional%20MTI%20%28Weak%29&references_pmid=18185580&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "experiments": "Microarray",
          "id": 15465,
          "mi_rna": "hsa-miR-335-5p",
          "mi_rtar_base_id": "MIRT019168",
          "references_pmid": 18185580,
          "species_mi_rna": "Homo sapiens",
          "species_target_gene": "Homo sapiens",
          "support_type": "Functional MTI (Weak)",
          "target_gene": "CD33",
          "target_gene_entrez_id": 945
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
