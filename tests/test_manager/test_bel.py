"""Bel module tests."""

from .constants import test_client, TEST_JSON
from .true_values import NODES_EXTENSION, EDGES_EXTENSION

bel = test_client


class TestBel:
    """Test class for bel module."""

    # def test_create_ssfs(self):
    #     """Test that server side functions are properly made."""
    #     bel.clear_server_side_functions()
    #     assert not bel.server_side_function_names()  # Should be no SSFs
    #     bel.create_ssfs()
    #     ssf_names = bel.server_side_function_names()
    #     # Check that the number of functions in db is equal or greater than in odb_ss_functions.py
    #     assert len(ssf_names) == len(ssfs.keys())
    #
    #     # Check that all in odb_ss_functions.py are in db
    #     base_ssfs = [func['name'] for func in ssfs.values()]
    #     assert all([func in base_ssfs for func in ssf_names])

    def test_bel_properties(self):
        """Test that all properties are present."""
        assert hasattr(bel, 'hgnc')
        assert hasattr(bel, 'uniprot')
        # assert hasattr(bel, 'dea')
        assert hasattr(bel, 'drugbank')
        assert hasattr(bel, 'gwas_catalog')
        assert hasattr(bel, 'reactome')
        assert hasattr(bel, 'biogrid')
        assert hasattr(bel, 'stringdb')
        assert hasattr(bel, 'clinical_trials')
        assert hasattr(bel, 'intact')
        assert hasattr(bel, 'clinvar')
        assert hasattr(bel, 'mirtarbase')
        assert hasattr(bel, 'disgenet')
        assert hasattr(bel, 'pathway_commons')
        assert hasattr(bel, 'kegg')
        assert hasattr(bel, 'ensembl')
        assert hasattr(bel, 'iuphar')
        assert hasattr(bel, 'chebi')
        assert hasattr(bel, 'nsides')
        assert hasattr(bel, 'ncbi')
        assert hasattr(bel, 'protein_atlas')

    def test_import_json(self):
        """Tests update_from_protein2gene feature of import_json."""
        # Clear all nodes and edges from test db
        bel.clear_all_nodes_and_edges()
        bel.clear_documents()

        assert all([count == 0 for count in bel.number_of_nodes.values()])
        assert all([count == 0 for count in bel.number_of_edges.values()])

        files_imported = bel.import_json(input_path=TEST_JSON,
                                         update_from_protein2gene=True,
                                         extend_graph=False)

        assert len(files_imported) == 1
        assert bel.number_of_nodes == NODES_EXTENSION
        assert bel.number_of_edges == EDGES_EXTENSION
