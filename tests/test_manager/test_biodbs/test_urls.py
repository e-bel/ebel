"""Unit tests for checking the URLs."""

import ftplib
import requests

from ..constants import test_client
from ebel.manager.orientdb.constants import DRUGBANK, HGNC, CHEBI, ENSEMBL, GWAS_CATALOG, CLINVAR, UNIPROT, REACTOME, \
    STRINGDB, INTACT, BIOGRID, MIRTARBASE, PATHWAY_COMMONS, DISGENET, KEGG, IUPHAR, NSIDES, CLINICAL_TRIALS, \
    PROTEIN_ATLAS, NCBI

bel = test_client


class TestUrls:
    """Goes through URLs for bioDBs and checks whether link is still valid."""

    @staticmethod
    def check_links(urls: dict):
        """Checks every link in dict is downloadable."""
        for url_name, url in urls.items():
            if url.startswith("ftp"):  # FTP conns need to be handled
                remove_prefix = url.split("://")[1]
                base_name, path = remove_prefix.split("/", 1)
                ftp_conn = ftplib.FTP(base_name)
                ftp_conn.login("anonymous", "anonymous")
                assert ftp_conn.size(path) > 0  # Check file is there
                ftp_conn.close()

            else:
                if "kegg" in url_name:  # Special case - returns plain text
                    resp = requests.get(url)
                    assert resp.ok
                    continue

                headers = requests.head(url, allow_redirects=True).headers
                if 'Content-disposition' in headers:  # Check file attachment
                    assert "filename" in headers.get('Content-disposition')

                elif "Content-Encoding" in headers:
                    assert headers.get("Content-Encoding") == "gzip"  # Check if it's a gzip file

                else:
                    file_size = int(headers.get('Content-Length'))
                    assert file_size > 0

    def test_urls(self):
        """Iterates through BioDBs."""
        biodbs = {
            HGNC: bel.hgnc,
            CHEBI: bel.chebi,
            ENSEMBL: bel.ensembl,
            GWAS_CATALOG: bel.gwas_catalog,
            CLINVAR: bel.clinvar,
            UNIPROT: bel.uniprot,
            REACTOME: bel.reactome,
            STRINGDB: bel.stringdb,
            INTACT: bel.intact,
            BIOGRID: bel.biogrid,
            MIRTARBASE: bel.mirtarbase,
            PATHWAY_COMMONS: bel.pathway_commons,
            DISGENET: bel.disgenet,
            KEGG: bel.kegg,
            DRUGBANK: bel.drugbank,
            IUPHAR: bel.iuphar,
            NSIDES: bel.nsides,
            CLINICAL_TRIALS: bel.clinical_trials,
            PROTEIN_ATLAS: bel.protein_atlas,
            NCBI: bel.ncbi,
        }
        for db in biodbs.values():
            self.check_links(db.urls)
