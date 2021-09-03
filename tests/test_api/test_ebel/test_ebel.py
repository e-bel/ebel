"""eBEL API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestEbel:
    def test_get_bel_edge_statistics_by_uniprot_accession(self, client):
        # TODO implement when activated in YAML
        pass

    def test_get_intact_by_uniprot(self, client):
        # TODO implement when activated in YAML
        pass

    def test_find_all(self, client):
        response = client.post(
            'api/v1/ebel/find_all',
            json={"term": "CD33"},
        )
        output = format_response_data(response)

        assert isinstance(output, int)
        assert output == 2
