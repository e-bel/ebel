"""DisGeNet."""
import logging
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB

from ebel.manager.orientdb.constants import DISGENET
from ebel.manager.orientdb import odb_meta, urls, odb_structure
from ebel.tools import get_file_path, get_disease_trait_keywords_from_config

from ebel.manager.rdbms.models import disgenet

logger = logging.getLogger(__name__)


class DisGeNet(odb_meta.Graph):
    """DisGeNet (https://www.disgenet.org)."""

    def __init__(self, client: OrientDB = None):
        """Init DisGeNet."""
        self.client = client
        self.biodb_name = DISGENET
        self.urls = {
            'disgenet_gene': urls.DISGENET_GDP_ASSOC,
            'disgenet_variant': urls.DISGENET_VDP_ASSOC,
        }
        super().__init__(tables_base=disgenet.Base,
                         edges=odb_structure.disgenet_edges,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

        self.disease_keywords = get_disease_trait_keywords_from_config()

    def __len__(self):
        return self.number_of_generics

    def __contains__(self, item):
        # TODO: To be implemented
        return True

    def __repr__(self) -> str:
        """Represent DisGeNet as string."""
        template = "{{BioDatabase:DisGeNet}}[url:{url}, edges:{edges}, generics:{generics}]"
        representation = template.format(
            url=self.urls,
            edges=self.number_of_edges,
            generics=self.number_of_generics
        )
        return representation

    def insert_data(self) -> Dict[str, int]:
        """Insert data into database."""
        logger.info(f"Import {self.biodb_name.upper()}")
        inserted = dict()
        inserted['sources'] = self._insert_sources()
        inserted['gene_symbols'] = self._insert_gene_symbols()
        inserted['gene_disease_names'] = self._insert_disease_names()
        inserted['gene_disease_pmid_associations'] = self._insert_gene_disease_pmid_associations()
        inserted['variant_disease_pmid_associations'] = self._insert_variant_disease_pmid_associations()
        return inserted

    def __get_file_for_model(self, model):
        """Return filepath of given model."""
        return get_file_path(self.urls[model.__tablename__], self.biodb_name)

    @property
    def file_path_gene(self):
        """Return filepath of gene."""
        return self.__get_file_for_model(disgenet.DisgenetGene)

    @property
    def file_path_variant(self):
        """Return filepath of variant."""
        return self.__get_file_for_model(disgenet.DisgenetVariant)

    def _insert_sources(self):
        df_g = pd.read_csv(self.file_path_gene, sep="\t", usecols=['source']).drop_duplicates()
        df_v = pd.read_csv(self.file_path_variant, sep="\t", usecols=['source']).drop_duplicates()
        df = pd.concat([df_g, df_v]).drop_duplicates()
        df.reset_index(inplace=True, drop=True)
        df.index += 1
        df.index.rename('id', inplace=True)
        df.to_sql(disgenet.DisgenetSource.__tablename__, self.engine, if_exists='append')
        return df.shape[0]

    def _insert_disease_names(self) -> int:
        columns_disease = {'diseaseId': 'disease_id', 'diseaseName': 'disease_name'}

        df_gene = pd.read_csv(self.file_path_gene, sep="\t", usecols=columns_disease.keys()) \
            .rename(columns=columns_disease) \
            .drop_duplicates().set_index('disease_id')

        df_variant = pd.read_csv(self.file_path_variant, sep="\t", usecols=columns_disease.keys()) \
            .rename(columns=columns_disease) \
            .drop_duplicates().set_index('disease_id')

        df_concat = pd.concat([df_gene, df_variant]).drop_duplicates()
        df_concat.to_sql(disgenet.DisgenetDisease.__tablename__, self.engine, if_exists='append')
        return df_concat.shape[0]

    def _insert_gene_symbols(self) -> int:
        columns_gene_symols = {'geneId': "gene_id", 'geneSymbol': "gene_symbol"}
        df = pd.read_csv(self.file_path_gene, sep="\t", usecols=columns_gene_symols.keys()) \
            .rename(columns=columns_gene_symols) \
            .drop_duplicates().set_index('gene_id')
        df.to_sql(disgenet.DisgenetGeneSymbol.__tablename__, self.engine, if_exists='append')
        return df.shape[0]

    def _merge_with_source(self, df):
        df_sources = pd.read_sql_table(disgenet.DisgenetSource.__tablename__, self.engine) \
            .rename(columns={'id': 'source_id'})
        return pd.merge(df, df_sources, on="source").drop(columns=['source'])

    def _insert_gene_disease_pmid_associations(self) -> int:
        usecols_gene = ['geneId', 'diseaseId', 'score', 'pmid', 'source']
        rename_dict = dict(zip(usecols_gene, self._standardize_column_names(usecols_gene)))
        df = pd.read_csv(self.file_path_gene, sep="\t", usecols=usecols_gene) \
            .rename(columns=rename_dict)

        df = self._merge_with_source(df)
        df.index += 1
        df.index.rename('id', inplace=True)
        df.to_sql(disgenet.DisgenetGene.__tablename__, self.engine, if_exists='append')
        return df.shape[0]

    def _insert_variant_disease_pmid_associations(self) -> Dict[str, int]:
        usecols_variant = ['snpId', 'chromosome', 'position', 'diseaseId', 'score', 'pmid', 'source']
        rename_dict = dict(zip(usecols_variant, self._standardize_column_names(usecols_variant)))
        df = pd.read_csv(self.file_path_variant, sep="\t", usecols=usecols_variant) \
            .rename(columns=rename_dict)

        df = self._merge_with_source(df)
        df.index += 1
        df.index.rename('id', inplace=True)
        df.to_sql(disgenet.DisgenetVariant.__tablename__, self.engine, if_exists='append')

        return df.shape[0]

    def update_interactions(self) -> int:
        """Update edges with disgenet metadata."""
        self.clear_nodes_and_edges()
        # self.update_diseases()
        inserted = self.update_snps()
        self.delete_nodes_with_no_edges('snp')
        return inserted

    def update_diseases(self):
        """Update disease information."""
        # TODO: to be implemented, but disease node class did not exist before and definitions are unclear
        # query = self.session.query(disgenet.DisgenetDisease).filter(
        #     disgenet.DisgenetDisease.disease_name.like('%alzheimer%'))
        # diseases = [x.disease_id for x in query.all()]
        pass

    def update_snps(self) -> int:
        """Update SNP information."""
        snp_type = {'mapped': "mapped", 'downstream': "upstream", 'upstream': "downstream"}
        # TODO: replace SQL with SQL Alchemy statement
        sql_temp = """Select
                snp_id,
                chromosome,
                position,
                disease_name,
                pmid,
                score,
                source
            FROM
                disgenet_variant v INNER JOIN
                disgenet_source s on (v.source_id=s.id) INNER JOIN
                disgenet_disease d on (v.disease_id=d.disease_id)
            WHERE
                disease_name like '%%{}%%' and
                source!='BEFREE'
            GROUP BY
                snp_id,
                chromosome,
                position,
                disease_name,
                pmid,
                score,
                source"""

        results = dict()
        for kwd in self.disease_keywords:
            sql = sql_temp.format(kwd)
            rows = self.engine.execute(sql)
            results[kwd] = rows

        inserted = 0

        snps = {x['rs_number']: x['rid'] for x in self.query_class('snp', columns=['rs_number'])}

        for trait, kwd_disease_results in results.items():
            for r in tqdm(kwd_disease_results,
                          desc=f'Update DisGeNET variant interactions for {trait}',
                          total=kwd_disease_results.rowcount):
                snp_id, chromosome, position, disease_name, pmid, score, source = r

                if snp_id in snps:
                    snp_rid = snps[snp_id]

                else:
                    snp_rid = self.insert_record(class_name='snp', value_dict={'rs_number': snp_id})
                    snps[snp_id] = snp_rid

                gene_type_rids = self.get_set_gene_rids_by_position(chromosome, position)

                for gene_type, gene_rids in gene_type_rids.items():
                    for gene_rid in gene_rids:
                        value_dict = {'disease_name': disease_name,
                                      'score': score,
                                      'source': source,
                                      'pmid': pmid
                                      }
                        class_name = f"has_{snp_type[gene_type]}_snp_dgn"
                        self.create_edge(class_name=class_name,
                                         from_rid=gene_rid,
                                         to_rid=snp_rid,
                                         value_dict=value_dict)
                inserted += 1

        return inserted
