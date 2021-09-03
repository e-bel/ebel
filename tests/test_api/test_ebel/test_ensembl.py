"""EnsEMBL API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestEnsembl:
    def test_get_ensembl(self, client):
        response = client.get(
            'api/v1/ebel/ensembl/ensembl?enst=ENST00000436584&chromosome=19',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "chromosome": "19",
          "enst": "ENST00000436584",
          "gene_id": "ENSG00000105383.15",
          "gene_id_short": "ENSG00000105383",
          "hgnc_id": "HGNC:1659",
          "id": 29665,
          "orientation": 1,
          "start": 51225064,
          "stop": 51236572,
          "symbol": "CD33",
          "version": 38
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
