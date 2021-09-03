"""BioGRID API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestBiogrid:
    """Unit tests for the Biogrid API module."""

    def test_get_has_ppi_bg_by_symbol_taxid(self, client):
        """Test has_ppi collection."""
        # TODO implement once fixed: currently returns an empty list
        pass

    def test_get_sources(self, client):
        response = client.get(
            'api/v1/biogrid/sources',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "BIOGRID": 1,
          "FLYBASE": 4,
          "POMBASE": 2,
          "WORMBASE": 3
        }
        assert isinstance(output, dict)
        assert output == expected_results

    def test_get_has_ppi_bg_by_uniprot(self, client):
        response = client.get(
            'api/v1/ebel/biogrid/modification/by_uniprot?uniprot=P10636',
            content_type='application/json'
        )
        output = format_response_data(response)
        example_result = {  # Used to quickly getting cols
            "biogrid_ids": [
              2623252
            ],
            "modification": "Proteolytic Processing",
            "object_label": "Caspase-7",
            "object_name": "CASP7",
            "object_namespace": "HGNC",
            "object_taxonomy_id": 9606,
            "object_uniprot": "P55210",
            "pmids": [
              12888622
            ],
            "subject_label": "Microtubule-associated protein tau",
            "subject_name": "MAPT",
            "subject_namespace": "HGNC",
            "subject_taxonomy_id": 9606,
            "subject_uniprot": "P10636"
        }
        assert len(output) > 4
        assert isinstance(output, list)
        hit = None

        for entry in output:
            if entry["object_label"] == "Caspase-7":
                hit = entry
                break

        assert bool(hit)
        assert isinstance(hit, dict)
        for key, val in example_result.items():
            assert hit[key] == val

    def test_get_biogrid_by_biogrid_id(self, client):
        response = client.get(
            'api/v1/biogrid/by_biogrid_id/2658248',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "biogrid_a": {
            "entrez": 59272,
            "symbol": "ACE2",
            "systematic_name": "UNQ868/PRO1885",
            "taxonomy": {
              "organism_name": "Homo sapiens",
              "taxonomy_id": 9606
            },
            "trembl": None,
            "uniprot": "Q9BYF1"
          },
          "biogrid_b": {
            "entrez": 43740568,
            "symbol": "S",
            "systematic_name": "GU280_gp02",
            "taxonomy": {
              "organism_name": "Severe acute respiratory syndrome coronavirus 2",
              "taxonomy_id": 2697049
            },
            "trembl": None,
            "uniprot": "P0DTC2"
          },
          "biogrid_id": 2658248,
          "experimental_system": {
            "experimental_system": "Reconstituted Complex",
            "experimental_system_type": "physical",
            "frequency": 58466
          },
          "modification": None,
          "publication": {
            "author_name": "Sun C ",
            "publication_year": 2020,
            "source": "DOI",
            "source_identifier": "10.1101/2020.02.16.951723"
          },
          "qualification": "The Receptor Binding Domain (RBD) of the SARS-CoV-2 Spike protein interacts with human ACE2 in vitro.",
          "score": None,
          "source": "BIOGRID",
          "throughput": {
            "frequency": 366952,
            "throughput": "Low Throughput"
          }
        }
        assert isinstance(output, dict)
        assert output == expected_results

    def test_get_biogrid_by_biogrid_id_using_post(self, client):
        response = client.post(
            'api/v1/biogrid/by_biogrid_id',
            json={"biogrid_id": 2658248},
        )
        output = format_response_data(response)

        expected_results = {
          "biogrid_a": {
            "entrez": 59272,
            "symbol": "ACE2",
            "systematic_name": "UNQ868/PRO1885",
            "taxonomy": {
              "organism_name": "Homo sapiens",
              "taxonomy_id": 9606
            },
            "trembl": None,
            "uniprot": "Q9BYF1"
          },
          "biogrid_b": {
            "entrez": 43740568,
            "symbol": "S",
            "systematic_name": "GU280_gp02",
            "taxonomy": {
              "organism_name": "Severe acute respiratory syndrome coronavirus 2",
              "taxonomy_id": 2697049
            },
            "trembl": None,
            "uniprot": "P0DTC2"
          },
          "biogrid_id": 2658248,
          "experimental_system": {
            "experimental_system": "Reconstituted Complex",
            "experimental_system_type": "physical",
            "frequency": 58466
          },
          "modification": None,
          "publication": {
            "author_name": "Sun C ",
            "publication_year": 2020,
            "source": "DOI",
            "source_identifier": "10.1101/2020.02.16.951723"
          },
          "qualification": "The Receptor Binding Domain (RBD) of the SARS-CoV-2 Spike protein interacts with human ACE2 in vitro.",
          "score": None,
          "source": "BIOGRID",
          "throughput": {
            "frequency": 366952,
            "throughput": "Low Throughput"
          }
        }
        assert isinstance(output, dict)
        assert output == expected_results

    def test_get_experimental_systems(self, client):
        response = client.get(
            'api/v1/biogrid/experimental_systems',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "Affinity Capture-Luminescence": 24,
          "Affinity Capture-MS": 2,
          "Affinity Capture-RNA": 9,
          "Affinity Capture-Western": 5,
          "Biochemical Activity": 12,
          "Co-crystal Structure": 21,
          "Co-fractionation": 6,
          "Co-localization": 20,
          "Co-purification": 19,
          "Dosage Growth Defect": 26,
          "Dosage Lethality": 25,
          "Dosage Rescue": 18,
          "FRET": 22,
          "Far Western": 27,
          "Negative Genetic": 1,
          "PCA": 11,
          "Phenotypic Enhancement": 15,
          "Phenotypic Suppression": 14,
          "Positive Genetic": 4,
          "Protein-RNA": 17,
          "Protein-peptide": 23,
          "Proximity Label-MS": 7,
          "Reconstituted Complex": 8,
          "Synthetic Growth Defect": 10,
          "Synthetic Haploinsufficiency": 28,
          "Synthetic Lethality": 13,
          "Synthetic Rescue": 16,
          "Two-hybrid": 3
        }
        assert isinstance(output, dict)
        assert output == expected_results

    def test_get_taxonomies(self, client):
        response = client.get(
            'api/v1/biogrid/taxonomies',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "Anopheles gambiae (PEST)": 180454,
          "Apis mellifera": 7460,
          "Arabidopsis thaliana (Columbia)": 3702,
          "Bacillus subtilis (168)": 224308,
          "Bos taurus": 9913,
          "Caenorhabditis elegans": 6239,
          "Candida albicans (SC5314)": 237561,
          "Canis familiaris": 9615,
          "Cavia porcellus": 10141,
          "Chlamydomonas reinhardtii": 3055,
          "Chlorocebus sabaeus": 60711,
          "Cricetulus griseus": 10029,
          "Danio rerio": 7955,
          "Dictyostelium discoideum (AX4)": 352472,
          "Drosophila melanogaster": 7227,
          "Emericella nidulans (FGSC A4)": 227321,
          "Equus caballus": 9796,
          "Escherichia coli (K12)": 83333,
          "Escherichia coli (K12/MC4100/BW2952)": 595496,
          "Escherichia coli (K12/MG1655)": 511145,
          "Escherichia coli (K12/W3110)": 316407,
          "Felis Catus": 9685,
          "Gallus gallus": 9031,
          "Glycine max": 3847,
          "Hepatitus C Virus": 11103,
          "Homo sapiens": 9606,
          "Human Herpesvirus 1": 10298,
          "Human Herpesvirus 2": 10310,
          "Human Herpesvirus 3": 10335,
          "Human Herpesvirus 4": 10376,
          "Human Herpesvirus 5": 10359,
          "Human Herpesvirus 6A": 32603,
          "Human Herpesvirus 6B": 32604,
          "Human Herpesvirus 7": 10372,
          "Human Herpesvirus 8": 37296,
          "Human Immunodeficiency Virus 1": 11676,
          "Human Immunodeficiency Virus 2": 11709,
          "Human papillomavirus (10)": 333759,
          "Human papillomavirus (16)": 333760,
          "Human papillomavirus (32)": 333763,
          "Human papillomavirus (5)": 333923,
          "Human papillomavirus (6b)": 10600,
          "Human papillomavirus (7)": 10620,
          "Human papillomavirus (9)": 10621,
          "Leishmania major (Friedlin)": 347515,
          "Macaca mulatta": 9544,
          "Meleagris gallopavo": 9103,
          "Middle-East Respiratory Syndrome-related Coronavirus": 1335626,
          "Monodelphis domestica": 13616,
          "Mus musculus": 10090,
          "Mycobacterium tuberculosis (H37Rv)": 83332,
          "Neurospora crassa (OR74A)": 367110,
          "Nicotiana tomentosiformis": 4098,
          "Oryctolagus cuniculus": 9986,
          "Oryza sativa (Japonica)": 39947,
          "Ovis aries": 9940,
          "Pan troglodytes": 9598,
          "Pediculus humanus": 121224,
          "Plasmodium falciparum (3D7)": 36329,
          "Rattus norvegicus": 10116,
          "Ricinus communis": 3988,
          "Saccharomyces cerevisiae (S288c)": 559292,
          "Schizosaccharomyces pombe (972h)": 284812,
          "Selaginella moellendorffii": 88036,
          "Severe acute respiratory syndrome coronavirus 2": 2697049,
          "Severe acute respiratory syndrome-related coronavirus": 694009,
          "Simian Immunodeficiency Virus": 11723,
          "Simian Virus 40": 10633,
          "Solanum lycopersicum": 4081,
          "Solanum tuberosum": 4113,
          "Sorghum bicolor": 4558,
          "Streptococcus pneumoniae (ATCCBAA255)": 171101,
          "Strongylocentrotus purpuratus": 7668,
          "Sus scrofa": 9823,
          "Tobacco Mosaic Virus": 12242,
          "Ustilago maydis (521)": 237631,
          "Vaccinia Virus": 10245,
          "Vitis vinifera": 29760,
          "Xenopus laevis": 8355,
          "Zea mays": 4577
        }
        assert isinstance(output, dict)
        assert output == expected_results

    def test_get_modifications(self, client):
        response = client.get(
            'api/v1/biogrid/modifications',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "Acetylation": 4,
          "Deacetylation": 10,
          "Demethylation": 14,
          "Deneddylation": 15,
          "Dephosphorylation": 9,
          "Desumoylation": 13,
          "Deubiquitination": 5,
          "FAT10ylation": 19,
          "Glycosylation": 17,
          "Methylation": 7,
          "Nedd(Rub1)ylation": 11,
          "Neddylation": 18,
          "No Modification": 3,
          "Phosphorylation": 1,
          "Prenylation": 16,
          "Proteolytic Processing": 6,
          "Ribosylation": 12,
          "Sumoylation": 8,
          "Ubiquitination": 2,
          "de-ISGylation": 20
        }
        assert isinstance(output, dict)
        assert output == expected_results

    def test_get_biogrid_by_pmid(self, client):
        response = client.get(
            'api/v1/biogrid/by_pmid/21685874',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
            "biogrid_a": {
              "entrez": 853167,
              "symbol": "GCN5",
              "systematic_name": "YGR252W",
              "taxonomy": {
                "organism_name": "Saccharomyces cerevisiae (S288c)",
                "taxonomy_id": 559292
              },
              "trembl": None,
              "uniprot": "Q03330"
            },
            "biogrid_b": {
              "entrez": 852295,
              "symbol": "HHT1",
              "systematic_name": "YBR010W",
              "taxonomy": {
                "organism_name": "Saccharomyces cerevisiae (S288c)",
                "taxonomy_id": 559292
              },
              "trembl": None,
              "uniprot": "P61830"
            },
            "biogrid_id": 543927,
            "experimental_system": {
              "experimental_system": "Biochemical Activity",
              "experimental_system_type": "physical",
              "frequency": 24247
            },
            "modification": {
              "frequency": 846,
              "modification": "Acetylation"
            },
            "publication": {
              "author_name": "Bian C ",
              "publication_year": 2011,
              "source": "PUBMED",
              "source_identifier": "21685874"
            },
            "qualification": "the purified SAGA complex can acetylate histone 3 in vitro",
            "score": None,
            "source": "BIOGRID",
            "throughput": {
              "frequency": 1611845,
              "throughput": "High Throughput"
            }
          }
        assert isinstance(output, list)
        hit = output[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_biogrid(self, client):
        response = client.get(
            'api/v1/biogrid?id_type_a=symbol&interactor_a=MAPT&taxonomy_id_a=9606&id_type_b=symbol&taxonomy_id_b=9606&modification=Acetylation&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "biogrid_a": {
            "entrez": 2033,
            "symbol": "EP300",
            "systematic_name": "RP1-85F18.1",
            "taxonomy": {
              "organism_name": "Homo sapiens",
              "taxonomy_id": 9606
            },
            "trembl": "Q7Z6C1",
            "uniprot": "Q09472"
          },
          "biogrid_b": {
            "entrez": 4137,
            "symbol": "MAPT",
            "systematic_name": None,
            "taxonomy": {
              "organism_name": "Homo sapiens",
              "taxonomy_id": 9606
            },
            "trembl": "B3KTM0",
            "uniprot": "P10636"
          },
          "biogrid_id": 558818,
          "experimental_system": {
            "experimental_system": "Biochemical Activity",
            "experimental_system_type": "physical",
            "frequency": 24247
          },
          "modification": {
            "frequency": 846,
            "modification": "Acetylation"
          },
          "publication": {
            "author_name": "Min SW ",
            "publication_year": 2010,
            "source": "PUBMED",
            "source_identifier": "20869593"
          },
          "qualification": None,
          "score": None,
          "source": "BIOGRID",
          "throughput": {
            "frequency": 366952,
            "throughput": "Low Throughput"
          }
        }
        assert output[NUM_RESULTS] == 4
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_biogrid_using_post(self, client):
        response = client.post(
            'api/v1/biogrid',
            json={
              "experimental_system_id": 2,
              "page": 2,
              "page_size": 3
            },
            follow_redirects=True,
        )
        output = format_response_data(response)

        expected_results = {
          "biogrid_a": {
            "entrez": 1489671,
            "symbol": "E",
            "systematic_name": "SARS-CoV-4",
            "taxonomy": {
              "organism_name": "Severe acute respiratory syndrome-related coronavirus",
              "taxonomy_id": 694009
            },
            "trembl": None,
            "uniprot": "P59637"
          },
          "biogrid_b": {
            "entrez": 83871,
            "symbol": "RAB34",
            "systematic_name": None,
            "taxonomy": {
              "organism_name": "Homo sapiens",
              "taxonomy_id": 9606
            },
            "trembl": "B4DNC0",
            "uniprot": "Q9BZG1"
          },
          "biogrid_id": 2754699,
          "experimental_system": {
            "experimental_system": "Affinity Capture-MS",
            "experimental_system_type": "physical",
            "frequency": 459921
          },
          "modification": None,
          "publication": {
            "author_name": "Stukalov A ",
            "publication_year": 2020,
            "source": "DOI",
            "source_identifier": "10.1101/2020.06.17.156455"
          },
          "qualification": "Affinity capture-MS was carried out using HA-tagged viral proteins as baits in human A549 lung carcinoma cells. Significant interactions were identified as those where the prey protein was at least 4 times enriched against the background (median log2 score > 2) with a p-value <= 1E-3.",
          "score": 8.15622,
          "source": "BIOGRID",
          "throughput": {
            "frequency": 1611845,
            "throughput": "High Throughput"
          }
        }
        assert output[NUM_RESULTS] > 459000
        assert output[PAGE_SIZE] == 3
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results

    def test_get_interactor_by_symbol_starts_with(self, client):
        response = client.get(
            'api/v1/biogrid/interactor/by_symbol_starts_with?symbol=trem&taxonomy_id=9606&page_size=10&page=1',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "entrez": 54210,
          "symbol": "TREM1",
          "systematic_name": None,
          "taxonomy": {
            "organism_name": "Homo sapiens",
            "taxonomy_id": 9606
          },
          "trembl": "Q38L15",
          "uniprot": "Q9NP99"
        }
        assert output[NUM_RESULTS] == 4
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
