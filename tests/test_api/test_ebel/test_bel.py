"""Generic BEL API unit tests."""

from .constants import RESULTS
from .conftest import format_response_data


class TestBel:
    """Unit tests for the BEL API module."""

    def test_get_edge(self, client):
        response = client.get(
            'api/v1/bel/edges?subject_node_class=protein&subject_namespace=HGNC&subject_name=IL4&relation=increases&citation_full_journal_name=Molecular%20neurodegeneration&citation_pub_date=2018-06-12&citation_pub_year=2018&citation_last_author=Landreth%20GE&citation_type=PubMed&title=TREM2%20in%20Neurodegenerative%20Diseases.&doi=10.1186%2Fs13024-017-0197-5&object_node_class=protein&object_namespace=HGNC&object_name=TREM2&page_size=10&page=1',
            content_type='application/json'
        )
        cols = [
            'subject_rid',
            'subject_node_class',
            'subject_namespace',
            'subject_name',
            'subject_bel',
            'subject_gene_symbol_involved_in',
            'subject_other_involved_in',
            'edge_rid',
            'relation',
            'evidence',
            'citation_full_journal_name',
            'citation_pub_date',
            'citation_pub_year',
            'citation_last_author',
            'citation_type',
            'author_in_author_list',
            'title',
            'doi',
            'object_rid',
            'object_node_class',
            'object_namespace',
            'object_name',
            'object_bel',
            'object_gene_symbol_involved_in',
            'object_other_involved_in',
        ]

        output = format_response_data(response)
        assert isinstance(output, dict)
        results = output[RESULTS]
        assert isinstance(results, list)
        assert len(results) == 1
        hit = results[0]
        for col in cols:
            assert col in hit
        assert hit['object_name'] == "IL2"
        assert hit['object_namespace'] == "HGNC"
        assert hit['object_node_class'] == "protein"
        assert hit['citation_last_author'] == "Schellenberg GD"
        assert hit["relation"] == "increases"
