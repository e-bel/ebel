"""Unit tests for the enrich methods."""

from ..constants import test_client, TEST_JSON

bel = test_client


class TestEnrich:

    # TODO: Erasing and reimporting causes an error when these tests are run with test_bel.py
    # Make sure test DB is populated
    bel.clear_all_nodes_and_edges()
    bel.clear_documents()

    assert all([count == 0 for count in bel.number_of_nodes.values()])
    assert all([count == 0 for count in bel.number_of_edges.values()])

    bel.import_json(input_path=TEST_JSON,
                    update_from_protein2gene=True,
                    extend_graph=False,)

    def test_uniprot_enrich(self):
        updated = bel.uniprot.update_bel()
        assert isinstance(updated, dict)
        assert all([species in updated for species in ("HGNC", "MGI", "RGD")])
        assert all([isinstance(val, int) for val in updated.values()])
        assert updated['HGNC'] == 3

    def test_hgnc_enrich(self):
        updated = bel.hgnc.update_bel()
        assert isinstance(updated, int)
        assert updated == 4

    def test_chebi_enrich(self):
        updated = bel.chebi.update_bel()
        assert isinstance(updated, int)
        assert updated == 1

    def test_gwas_enrich(self):
        updated = bel.gwas_catalog.update_bel()
        assert isinstance(updated, dict)
        assert updated == {'has_mapped_snp_gc': 1141, 'has_downstream_snp_gc': 401, 'has_upstream_snp_gc': 394}

    def test_clinvar_enrich(self):
        updated = bel.clinvar.update_bel()
        assert isinstance(updated, int)
        assert updated == 2326

    def test_reactome_enrich(self):
        updated = bel.reactome.update_interactions()
        assert isinstance(updated, int)
        assert updated == 3

    def test_stringdb_enrich(self):
        updated = bel.stringdb.update_interactions()
        assert isinstance(updated, dict)
        assert updated == {'interactions': 43, 'actions': 152}

    def test_biogrid_enrich(self):
        updated = bel.biogrid.update_interactions()
        assert isinstance(updated, int)
        assert updated == 0

    def test_mirtarbase_enrich(self):
        updated = bel.mirtarbase.update_interactions()
        assert isinstance(updated, int)
        assert updated == 0

    def test_pc_enrich(self):
        updated = bel.pathway_commons.update_interactions()
        assert isinstance(updated, dict)
        assert updated == {'controls-transport-of': 19,
                           'controls-expression-of': 71,
                           'controls-phosphorylation-of': 12}

    def test_disgenet_enrich(self):
        updated = bel.disgenet.update_interactions()
        assert isinstance(updated, int)
        assert updated == 2948

    def test_kegg_enrich(self):
        updated = bel.kegg.update_interactions()
        assert isinstance(updated, int)
        assert updated == 0

    def test_drugbank_enrich(self):
        updated = bel.drugbank.update_interactions()
        assert isinstance(updated, int)
        assert updated == 3

    def test_iuphar_enrich(self):
        updated = bel.iuphar.update_interactions()
        assert isinstance(updated, int)
        assert updated == 3

    def test_nsides_enrich(self):
        updated = bel.nsides.update_bel()
        assert isinstance(updated, int)
        assert updated == 297

    def test_ct_enrich(self):
        # currently disabled
        pass
