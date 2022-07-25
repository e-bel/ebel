"""GwasCatalog implementation. Depends on HGNC."""

import logging
import numpy as np
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB

from ebel.constants import RID
from ebel.manager.orientdb.biodbs.hgnc import Hgnc
from ebel.manager.orientdb.constants import GWAS_CATALOG
from ebel.manager.orientdb import odb_meta, urls, odb_structure
from ebel.tools import get_disease_trait_keywords_from_config, get_file_path

from ebel.manager.rdbms.models import gwas_catalog

logger = logging.getLogger(__name__)


class GwasCatalog(odb_meta.Graph):
    """GWAS Catalog (EBI)."""

    def __init__(self, client: OrientDB = None,
                 disease_trait_keyword: str = "Alzheimer", overwrite_config: bool = False):
        """Init GwasCatalog."""
        self.snp_cache = {}
        self._ensembl_gene_rid_dict: Dict[str:str] = {}
        self.disease_keywords = get_disease_trait_keywords_from_config(disease_trait_keyword,
                                                                       overwrite=overwrite_config)
        self.client = client
        self.biodb_name = GWAS_CATALOG
        self.url = urls.GWAS_CATALOG
        self.urls = {self.biodb_name: self.url}
        super().__init__(nodes=odb_structure.gwascatalog_nodes,
                         edges=odb_structure.gwascatalog_edges,
                         tables_base=gwas_catalog.Base,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

    def __len__(self) -> int:
        """Get number of edges in OrientDB."""
        return self.number_of_edges

    def __contains__(self, rs_number: int) -> bool:
        """Checks if RS number (without prefix RS) exists in BEL graph."""
        return self.entry_exists(self.biodb_name, rs_number=rs_number)

    def insert_data(self) -> Dict[str, int]:
        """Insert GwasCatalog data in generic table `gwascatalog`."""
        # TODO: inform data provider about problems in dataset
        df = pd.read_csv(get_file_path(self.urls[self.biodb_name], self.biodb_name),
                         sep="\t",
                         low_memory=False,
                         on_bad_lines='warn')
        df.columns = self._standardize_column_names(df.columns)
        df.replace(np.inf, np.nan, inplace=True)  # Get rid of infinity
        # replace non-dates with np.nan
        # non_date = ~df.date_added_to_catalog.str.match(r'^\d{4}-\d{2}-\d{2}$')
        # df.loc[non_date, 'date_added_to_catalog'] = np.nan

        df.index += 1
        df.rename(columns={'snps': 'snp'}, inplace=True)
        df.index.rename('id', inplace=True)

        df.upstream_gene_id = df.upstream_gene_id.str.strip()
        df.downstream_gene_id = df.downstream_gene_id.str.strip()

        columns_main_table = [x for x in df.columns if x != 'snp_gene_ids']

        table_name = gwas_catalog.GwasCatalog.__tablename__

        df[columns_main_table].to_sql(table_name, self.engine, if_exists='append')

        df.snp_gene_ids = df.snp_gene_ids.str.strip().str.split(", ")
        df[table_name + "_id"] = df.index

        df_snp_gene_ids = df[[table_name + "_id", 'snp_gene_ids']].explode('snp_gene_ids')
        df_snp_gene_ids.dropna(inplace=True)
        df_snp_gene_ids.index = range(1, df_snp_gene_ids.shape[0] + 1)
        df_snp_gene_ids.rename(columns={'snp_gene_ids': 'ensembl_identifier'}, inplace=True)
        df_snp_gene_ids.index.rename('id', inplace=True)
        df_snp_gene_ids.to_sql(gwas_catalog.SnpGene.__tablename__, self.engine, if_exists='append')

        self.session.commit()

        return {self.biodb_name: df.shape[0]}

    def update_bel(self) -> Dict[str, int]:
        """Add human SNPs to OrientDB graph depending on keyword (disease or trait)."""
        hgnc = Hgnc(client=self.client)
        hgnc.update_bel()  # to make sure that all ensembl IDs are available
        logger.info(f"Clear edges for {self.biodb_name}")
        self.clear_edges()
        updated = self.update_interactions()

        if sum(updated.values()) > 0:
            hgnc.update_bel()  # GWAS adds new genes

        return updated

    def update_interactions(self) -> Dict[str, int]:
        """Update mapped, down and upstream has_snp edges."""
        inserted = {}
        logger.info(f"Update interactions for {self.biodb_name}")
        self.clear_edges()
        inserted['has_mapped_snp_gc'] = self.update_mapped_genes()
        inserted['has_downstream_snp_gc'] = self.update_upstream_genes()
        inserted['has_upstream_snp_gc'] = self.update_downstream_genes()
        logger.info(f"Successfully updated interactions for {self.biodb_name}")
        return inserted

    def update_mapped_genes(self) -> int:
        """Update mapped gene information."""
        inserted = 0
        for disease_keyword in self.disease_keywords:
            query_results = self.session.query(gwas_catalog.SnpGene) \
                .join(gwas_catalog.GwasCatalog) \
                .filter(gwas_catalog.GwasCatalog.disease_trait.like(f'%{disease_keyword}%')).with_entities(
                gwas_catalog.SnpGene.ensembl_identifier,
                gwas_catalog.GwasCatalog.snp,
                gwas_catalog.GwasCatalog.disease_trait,
                gwas_catalog.GwasCatalog.pubmedid
            ).all()

            inserted += self.insert_snps(query_results, 'has_mapped_snp_gc', disease_keyword)
        return inserted

    def update_upstream_genes(self):
        """Update upstream SNP information."""
        inserted = 0

        for disease_keyword in self.disease_keywords:
            query = self.session.query(gwas_catalog.GwasCatalog).filter(
                gwas_catalog.GwasCatalog.disease_trait.like(f'%{disease_keyword}%'),
                gwas_catalog.GwasCatalog.upstream_gene_id.isnot(None))
            query_results = query.with_entities(
                gwas_catalog.GwasCatalog.upstream_gene_id,
                gwas_catalog.GwasCatalog.snp,
                gwas_catalog.GwasCatalog.disease_trait,
                gwas_catalog.GwasCatalog.pubmedid
            ).all()

            inserted += self.insert_snps(query_results, 'has_downstream_snp_gc', disease_keyword)
        return inserted

    def update_downstream_genes(self):
        """Update downstream SNP information."""
        inserted = 0

        for disease_keyword in self.disease_keywords:
            query = self.session.query(gwas_catalog.GwasCatalog).filter(
                gwas_catalog.GwasCatalog.disease_trait.like(f'%{disease_keyword}%'),
                gwas_catalog.GwasCatalog.downstream_gene_id.isnot(None))
            query_results = query.with_entities(
                gwas_catalog.GwasCatalog.downstream_gene_id,
                gwas_catalog.GwasCatalog.snp,
                gwas_catalog.GwasCatalog.disease_trait,
                gwas_catalog.GwasCatalog.pubmedid
            ).all()

            inserted += self.insert_snps(query_results, 'has_upstream_snp_gc', disease_keyword)
        return inserted

    def insert_snps(self, query_results, edge_class: str, keyword: str):
        """Insert SNP metadata into database."""
        columns = ['ensembl_gene_id', 'snp', 'disease_trait', 'pubmedid']
        snps = pd.DataFrame(query_results, columns=columns)
        snps.set_index('ensembl_gene_id', inplace=True)

        inserted = 0
        desc = f'Update {edge_class} for {keyword}'
        for ensembl_gene_id, row in tqdm(snps.iterrows(), total=snps.shape[0], desc=desc):
            snp_rid = self._get_set_snp_rid(row.snp)
            value_dict = {'disease_trait': row.disease_trait, 'pubmed_id': row.pubmedid}

            gene_rid = self._get_gene_rid(ensembl_id=ensembl_gene_id)

            if gene_rid:
                self.create_edge(edge_class,
                                 gene_rid,
                                 snp_rid,
                                 value_dict=value_dict,
                                 if_not_exists=True)
                inserted += 1
        return inserted

    def _get_set_snp_rid(self, rs_number: str) -> str:
        """Insert snp (if not exists) and returns OrientDB @rid."""
        results = self.query_class(class_name='snp', limit=1, columns=[], rs_number=rs_number)

        if results:
            rid = results[0][RID]
        else:
            content = {'rs_number': rs_number}
            rid = self.insert_record('snp', content)

        return rid

    @property
    def ensembl_gene_rid_dict(self):
        """Return dict of ensembl IDs as keys and their rIDs as values."""
        if not self._ensembl_gene_rid_dict:
            sql = "Select hgnc.ensembl_gene_id as ensembl, @rid.asString() as rid from gene " \
                  "where hgnc.ensembl_gene_id IS NOT NULL and namespace='HGNC' and pure=true"
            self._ensembl_gene_rid_dict = {r['ensembl']: r[RID] for r in
                                           [x.oRecordData for x in self.execute(sql)]}
        return self._ensembl_gene_rid_dict

    def _get_gene_rid(self, ensembl_id: str):
        """Insert gene (if not exists) and returns OrientDB @rid."""
        rid = None
        if ensembl_id in self._ensembl_gene_rid_dict:
            rid = self._ensembl_gene_rid_dict[ensembl_id]
        else:
            hgnc_found = self.query_class('hgnc',
                                          columns=['symbol'],
                                          limit=1,
                                          ensembl_gene_id=ensembl_id)
            if hgnc_found:
                r = hgnc_found[0]
                bel = f'g(HGNC:"{r["symbol"]}")'
                data = {'pure': True,
                        'bel': bel,
                        'name': r['symbol'],
                        'namespace': "HGNC",
                        'hgnc': r[RID]
                        }
                rid = self.get_create_rid('gene', data, check_for='bel')
                self._ensembl_gene_rid_dict[ensembl_id] = rid
        return rid
