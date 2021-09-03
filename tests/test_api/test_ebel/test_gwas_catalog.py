"""GWAS Catalog API unit tests."""

from .conftest import format_response_data
from .constants import RESULTS, NUM_RESULTS, PAGE_SIZE


class TestGwasCatalog:
    def test_get_gwas_catalog(self, client):
        response = client.get(
            'api/v1/gwas_catalog/gwas_catalog?date_added_to_catalog=2013-10-24&pubmedid=23563609&first_author=Wheeler%20E&date=2013-04-07&journal=Nat%20Genet&link=www.ncbi.nlm.nih.gov%2Fpubmed%2F23563609&study=Genome-wide%20SNP%20and%20CNV%20analysis%20identifies%20common%20and%20low-frequency%20variants%20associated%20with%20severe%20early-onset%20obesity.&disease_trait=Obesity%20%28early%20onset%20extreme%29&initial_sample_size=1%2C509%20European%20ancestry%20cases%2C%205%2C380%20European%20ancestry%20controls&replication_sample_size=971%20European%20ancestry%20cases%2C%201%2C990%20European%20ancestry%20controls&region=16q12.2&chr_id=16&chr_pos=53767042&reported_gene_s=FTO&mapped_gene=FTO&strongest_snp_risk_allele=rs1421085-C&snp=rs1421085&snp_id_current=1421085&context=intron_variant&risk_allele_frequency=0.41&p_value=3e-28&pvalue_mlog=27.5229&or_or_beta=1.44&_95_ci_text=%5B1.35-1.54%5D&platform_snps_passing_qc=Affymetrix%20%5B~%202000000%5D%20%28imputed%29&cnv=N',
            content_type='application/json'
        )
        output = format_response_data(response)
        expected_results = {
          "_95_ci_text": "[1.35-1.54]",
          "chr_id": "16",
          "chr_pos": "53767042",
          "cnv": "N",
          "context": "intron_variant",
          "date": "2013-04-07",
          "date_added_to_catalog": "2013-10-24",
          "disease_trait": "Obesity (early onset extreme)",
          "downstream_gene_distance": None,
          "downstream_gene_id": None,
          "first_author": "Wheeler E",
          "id": 146661,
          "initial_sample_size": "1,509 European ancestry cases, 5,380 European ancestry controls",
          "intergenic": 0,
          "journal": "Nat Genet",
          "link": "www.ncbi.nlm.nih.gov/pubmed/23563609",
          "mapped_gene": "FTO",
          "merged": 0,
          "or_or_beta": 1.44,
          "p_value": 3e-28,
          "p_value_text": None,
          "platform_snps_passing_qc": "Affymetrix [~ 2000000] (imputed)",
          "pubmedid": 23563609,
          "pvalue_mlog": 27.5229,
          "region": "16q12.2",
          "replication_sample_size": "971 European ancestry cases, 1,990 European ancestry controls",
          "reported_gene_s": "FTO",
          "risk_allele_frequency": "0.41",
          "snp": "rs1421085",
          "snp_genes": [
            "ENSG00000140718"
          ],
          "snp_id_current": "1421085",
          "strongest_snp_risk_allele": "rs1421085-C",
          "study": "Genome-wide SNP and CNV analysis identifies common and low-frequency variants associated with severe early-onset obesity.",
          "upstream_gene_distance": None,
          "upstream_gene_id": None
        }
        assert output[NUM_RESULTS] == 1
        assert output[PAGE_SIZE] == 10
        results = output[RESULTS]
        assert isinstance(results, list)
        hit = results[0]
        assert isinstance(hit, dict)
        assert hit == expected_results
