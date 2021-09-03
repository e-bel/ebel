"""HGNC API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestHgnc:
    def test_get_by_symbol(self, client):
        response = client.get(
            'api/v1/hgnc/by_symbol?symbol=CD33',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "agr": "HGNC:1659",
            "alias_names": [
                "sialic acid binding Ig-like lectin 3"
            ],
            "alias_symbols": [
                "SIGLEC3",
                "SIGLEC-3",
                "p67",
                "FLJ00391"
            ],
            "bioparadigms_slc": None,
            "ccdss": [
                "CCDS46157",
                "CCDS54299",
                "CCDS33084"
            ],
            "cd": "CD33",
            "cosmic": None,
            "date_approved_reserved": "1986-01-01",
            "date_modified": "2016-10-05",
            "date_name_changed": "2006-03-28",
            "date_symbol_changed": None,
            "enas": [
                "M23197"
            ],
            "ensembl_gene_id": "ENSG00000105383",
            "entrez_id": 945,
            "enzymes": [],
            "gene_group_ids": [
                471,
                590,
                745
            ],
            "gene_group_names": [
                "CD molecules",
                "V-set domain containing",
                "Sialic acid binding Ig like lectins"
            ],
            "hgnc_id": "HGNC:1659",
            "homeodb": None,
            "horde_id": None,
            "imgt": None,
            "intermediate_filament_db": None,
            "iuphar": "objectId:2601",
            "kznf_gene_catalog": None,
            "lncipedia": None,
            "lncrnadb": None,
            "location": "19q13.41",
            "location_sortable": "19q13.41",
            "locus_group": "protein-coding gene",
            "locus_type": "gene with protein product",
            "lsdbs": [],
            "mamit_trnadb": None,
            "merops": None,
            "mgds": [
                "MGI:99440"
            ],
            "mirbase": None,
            "name": "CD33 molecule",
            "omims": [
                159590
            ],
            "orphanet": None,
            "pre_symbols": [],
            "prev_names": [
                "CD33 antigen (gp67)"
            ],
            "pseudogene_org": None,
            "pubmeds": [
                3139766,
                9465907
            ],
            "refseqs": [
                "NM_001772"
            ],
            "rgds": [
                "RGD:1596020"
            ],
            "rna_centrals": [],
            "snornabase": None,
            "status": "Approved",
            "symbol": "CD33",
            "ucsc_id": "uc002pwa.3",
            "uniprots": [
                "P20138"
            ],
            "uuid": "982e665a-2cc7-4ef3-b9f6-4406e08ed6c8",
            "vega_id": "OTTHUMG00000182891",
            "version": 1702607059790331904
        }
        assert isinstance(output, dict)
        assert output == expected_results

    def test_get_uniprot_accession_by_hgnc_symbol(self, client):
        response = client.get(
            'api/v1/hgnc/uniprot_accession_by_hgnc_symbol?symbol=CD33',
            content_type='application/json'
        )
        output = format_response_data(response)
        assert isinstance(output, str)
        assert output == "P20138"

    def test_get_hgnc(self, client):
        response = client.get(
            'api/v1/hgnc?symbol=CD33&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "agr": "HGNC:1659",
          "alias_names": [
            "sialic acid binding Ig-like lectin 3"
          ],
          "alias_symbols": [
            "SIGLEC3",
            "SIGLEC-3",
            "p67",
            "FLJ00391"
          ],
          "bioparadigms_slc": None,
          "ccdss": [
            "CCDS46157",
            "CCDS54299",
            "CCDS33084"
          ],
          "cd": "CD33",
          "cosmic": None,
          "date_approved_reserved": "1986-01-01",
          "date_modified": "2016-10-05",
          "date_name_changed": "2006-03-28",
          "date_symbol_changed": None,
          "enas": [
            "M23197"
          ],
          "ensembl_gene_id": "ENSG00000105383",
          "entrez_id": 945,
          "enzymes": [],
          "gene_group_ids": [
            471,
            590,
            745
          ],
          "gene_group_names": [
            "CD molecules",
            "V-set domain containing",
            "Sialic acid binding Ig like lectins"
          ],
          "hgnc_id": "HGNC:1659",
          "homeodb": None,
          "horde_id": None,
          "imgt": None,
          "intermediate_filament_db": None,
          "iuphar": "objectId:2601",
          "kznf_gene_catalog": None,
          "lncipedia": None,
          "lncrnadb": None,
          "location": "19q13.41",
          "location_sortable": "19q13.41",
          "locus_group": "protein-coding gene",
          "locus_type": "gene with protein product",
          "lsdbs": [],
          "mamit_trnadb": None,
          "merops": None,
          "mgds": [
            "MGI:99440"
          ],
          "mirbase": None,
          "name": "CD33 molecule",
          "omims": [
            159590
          ],
          "orphanet": None,
          "pre_symbols": [],
          "prev_names": [
            "CD33 antigen (gp67)"
          ],
          "pseudogene_org": None,
          "pubmeds": [
            3139766,
            9465907
          ],
          "refseqs": [
            "NM_001772"
          ],
          "rgds": [
            "RGD:1596020"
          ],
          "rna_centrals": [],
          "snornabase": None,
          "status": "Approved",
          "symbol": "CD33",
          "ucsc_id": "uc002pwa.3",
          "uniprots": [
            "P20138"
          ],
          "uuid": "982e665a-2cc7-4ef3-b9f6-4406e08ed6c8",
          "vega_id": "OTTHUMG00000182891",
          "version": 1702607059790331904
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
