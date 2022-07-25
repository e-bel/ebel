"""NCBI module."""
import pandas as pd

from tqdm import tqdm
from pyorientdb import OrientDB
from typing import Dict, Optional

from ebel.manager.orientdb.constants import NCBI
from ebel.manager.orientdb import odb_meta, urls
from ebel.tools import get_file_path, get_standard_name

from ebel.manager.rdbms.models import ncbi


class Ncbi(odb_meta.Graph):
    """NCBI Gene (https://ftp.ncbi.nih.gov/gene/DATA/)."""

    def __init__(self, client: OrientDB = None):
        """Init NcbiGene."""
        self.client = client
        self.biodb_name = NCBI
        self.urls = {ncbi.NcbiGeneInfo.__tablename__: urls.NCBI_GENE_INFO,
                     ncbi.NcbiGeneMim.__tablename__: urls.NCBI_GENE_2MIM,
                     ncbi.NcbiGeneEnsembl.__tablename__: urls.NCBI_GENE_2ENSEMBL,
                     ncbi.NcbiGeneGo.__tablename__: urls.NCBI_GENE_2GO,
                     ncbi.NcbiGenePubmed.__tablename__: urls.NCBI_GENE_2PUBMED,
                     ncbi.NcbiGeneOrtholog.__tablename__: urls.NCBI_GENE_ORTHOLOG,
                     ncbi.NcbiMedGenName.__tablename__: urls.NCBI_GENE_MEDGEN_NAMES,
                     ncbi.NcbiMedGenPmid.__tablename__: urls.NCBI_GENE_MEDGEN_PUBMED,
                     'neighbors': urls.NCBI_GENE_NEIGHBORS,
                     }
        super().__init__(urls=self.urls,
                         tables_base=ncbi.Base,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.session.query(ncbi.NcbiGeneInfo).count()

    def __contains__(self, gene_id) -> bool:
        count = self.session.query(ncbi.NcbiGeneInfo).filter(ncbi.NcbiGeneInfo.gene_id == gene_id).count()
        return bool(count)

    def insert_data(self) -> Dict[str, int]:
        """Insert NCBI gene data.

        :return Dict[str, int]: Tables as keys and inserted rows and values.
        """
        self.recreate_tables()
        inserts = dict()
        inserts[ncbi.NcbiGeneInfo.__tablename__] = self._insert_info()
        inserts[ncbi.NcbiGeneGo.__tablename__] = self._insert_go()
        inserts[ncbi.NcbiGeneEnsembl.__tablename__] = self._insert_ensembl()
        # inserts[ncbi.NcbiGeneMim.__tablename__] = self._insert_mim()
        inserts[ncbi.NcbiGenePubmed.__tablename__] = self._insert_pubmeds()
        inserts[ncbi.NcbiGeneOrtholog.__tablename__] = self._insert_orthologs()
        inserts.update(self._insert_neighbors())
        inserts[ncbi.NcbiMedGenName.__tablename__] = self._insert_medgen()
        return inserts

    def __insert_table(self, model, use_cols=None, sep: str = "\t", chunksize: Optional[int] = None) -> int:
        """Generic method to insert data.

        :param model: NCBI SQLAlchemy model
        :param use_cols: Column names to be used in file
        :param sep: Column separator
        :return:
        """
        table = model.__tablename__
        file_path = get_file_path(self.urls[table], self.biodb_name)
        dfs = pd.read_csv(file_path, sep=sep, usecols=use_cols, chunksize=chunksize)
        if chunksize is None:
            dfs = [dfs]

        number_of_inserts = 0

        for df in dfs:
            self._standardize_dataframe(df)
            df.to_sql(table, self.engine, if_exists="append", index=False)
            number_of_inserts += df.shape[0]

        return number_of_inserts

    def _insert_medgen(self) -> int:
        """Insert MedGen names.

        :return: Number of inserts
        """
        table_name = ncbi.NcbiMedGenName.__tablename__
        file_path_name = get_file_path(self.urls[table_name], self.biodb_name)
        use_cols_name = ["#CUI", "name", "source", "SUPPRESS"]
        df_name = pd.read_csv(file_path_name, usecols=use_cols_name, sep='|').rename_axis('id')
        df_name.index += 1
        self._standardize_dataframe(df_name)
        df_name.to_sql(table_name, self.engine, if_exists="append")

        table_pmid = ncbi.NcbiMedGenPmid.__tablename__
        file_path_pmid = get_file_path(self.urls[table_pmid], self.biodb_name)
        use_cols_pmid = ["CUI", "PMID"]
        dfs_pmid = pd.read_csv(file_path_pmid, index_col='CUI', usecols=use_cols_pmid, sep='|', chunksize=1000000)

        df_name['ncbi_medgen_name_id'] = df_name.index
        df_name_fk = df_name.set_index('cui')[['ncbi_medgen_name_id']]

        inserted = 0
        for df in dfs_pmid:
            df.columns = [get_standard_name(x) for x in df.columns]
            df_join = df.join(df_name_fk).reset_index(drop=True)
            inserted += df_join.shape[0]
            df_join.to_sql(table_pmid, self.engine, if_exists="append", index=False)

        return inserted

    def _insert_go(self) -> int:
        """Insert Gene Ontology mapping to Gene IDs.

        :return: Number of inserts
        """
        table = ncbi.NcbiGeneGo.__tablename__
        file_path = get_file_path(self.urls[table], self.biodb_name)
        df = pd.read_csv(file_path, sep="\t")

        table_pmid = ncbi.NcbiGeneGoPmid.__tablename__

        self._standardize_dataframe(df)
        df.index += 1
        df.index.rename('id', inplace=True)
        df.pub_med = df.pub_med.str.split('|')
        rename_columns = {'id': "ncbi_gene_go_id", 'pub_med': "pmid"}
        df_pub_med = df[['pub_med']].explode('pub_med').dropna() \
            .reset_index().rename(columns=rename_columns)

        df.drop(columns=['pub_med'], inplace=True)
        df.to_sql(table, self.engine, if_exists="append")
        df_pub_med.to_sql(table_pmid, self.engine, if_exists="append", index=False)

        return df.shape[0]

    def _insert_ensembl(self) -> int:
        """Insert Ensembl mapping to Gene IDs.

        :return: Number of inserts
        """
        return self.__insert_table(ncbi.NcbiGeneEnsembl)

    def _insert_mim(self) -> int:
        """Insert OMIM (Online Mendelian Inheritance in Man) mapping to Gene IDs.

        :return: Number of inserts
        """
        return self.__insert_table(ncbi.NcbiGeneMim)

    def _insert_pubmeds(self) -> int:
        """Insert PubMed references to Gene IDs.

        :return: Number of inserts
        """
        return self.__insert_table(ncbi.NcbiGenePubmed, chunksize=1000000)

    def _insert_orthologs(self) -> int:
        """Insert orthologs to Gene IDs.

        :return: Number of inserts
        """
        use_cols = ['#tax_id', 'GeneID', 'Other_tax_id', 'Other_GeneID']
        return self.__insert_table(ncbi.NcbiGeneOrtholog, use_cols, chunksize=1000000)

    def _insert_neighbors(self) -> Dict[str, int]:
        """Insert overlapping, right and left neighbors.

        :return int: Number of inserts
        """
        usecols = ['GeneID', 'GeneIDs_on_left', 'GeneIDs_on_right', 'overlapping_GeneIDs']
        file_path = get_file_path(self.urls['neighbors'], self.biodb_name)

        neighbor_types = {'overlapping_gene_ids': ncbi.NcbiGeneOverlapping,
                          'gene_ids_on_right': ncbi.NcbiGeneOnRight,
                          'gene_ids_on_left': ncbi.NcbiGeneOnLeft}

        inserted = {neighbor_type: 0 for neighbor_type in neighbor_types}

        dfs = pd.read_csv(file_path, sep="\t", usecols=usecols, chunksize=1000000)

        for df in dfs:
            df.columns = [get_standard_name(x) for x in df.columns]

            for neighbor_type, model in neighbor_types.items():
                df_type = df[['gene_id', neighbor_type]].set_index('gene_id')
                ntype = neighbor_type.replace('ids', 'id')
                df_type.rename(columns={neighbor_type: ntype}, inplace=True)
                df_type[ntype] = df_type[ntype].str.split('|')
                df_type = df_type.explode(ntype)
                df_type = df_type[df_type[ntype] != '-'].reset_index()
                df_type.to_sql(
                    model.__tablename__,
                    self.engine,
                    if_exists='append',
                    index=False)
                inserted[neighbor_type] += df_type.shape[0]
        return inserted

    def _insert_info_description(self) -> pd.DataFrame:
        """Insert gene description.

        :return int: Number of inserts
        """
        table = ncbi.NcbiGeneInfo.__tablename__
        file_path = get_file_path(self.urls[table], self.biodb_name)
        df = pd.read_csv(file_path,
                         sep="\t",
                         usecols=['description'],
                         dtype={'description': 'string'}) \
            .dropna().drop_duplicates()
        df.index += 1
        df.index.rename('id', inplace=True)
        df.to_sql(ncbi.NcbiGeneInfoDescription.__tablename__, self.engine, if_exists='append')
        return df.assign(description_id=df.index).set_index(['description'])

    def _insert_info_xref(self, dataframe: pd.DataFrame) -> int:
        """Insert cross references to Gene IDs using Gene Info DataFrame.

        :param dataframe: Gene info pandas DataFrame
        :return int: Number of inserts
        """
        inserted = 0
        df = dataframe[['db_xrefs', 'gene_id']][dataframe.db_xrefs != '-'].dropna()

        if not df.empty:
            df.set_index('gene_id', inplace=True)
            df['db_xrefs'] = df['db_xrefs'].str.split('|')
            df = df.explode('db_xrefs')
            df[['db', 'dbid']] = df['db_xrefs'].str.split(':', 1, expand=True)
            df.drop(columns=['db_xrefs'], inplace=True)
            df.reset_index().to_sql('ncbi_gene_info_xref', self.engine, if_exists="append", index=False)
            inserted = df.shape[0]

        return inserted

    def _insert_info(self, chunksize: int = 1000000) -> int:
        """Insert Gene Info.

        :param chunksize: size of the row aggregates
        :return int: Number of inserts
        """
        df_info_decr = self._insert_info_description()
        inserted = 0
        table = ncbi.NcbiGeneInfo.__tablename__
        file_path = get_file_path(self.urls[table], self.biodb_name)

        # TODO: To decrease the size of gene_info table, type_of_gene should be implemented as its own table
        # df_type_of_gene = pd.read_csv(file_path, sep="\t",usecols=['type_of_gene']).drop_duplicates()\
        #     .reset_index(drop=True).rename_axis('id')
        # df_type_of_gene.index += 1
        # df_type_of_gene.to_sql()

        use_cols = {'#tax_id', 'GeneID', 'LocusTag', 'Symbol', 'chromosome', 'description', 'map_location',
                    'type_of_gene', 'dbXrefs'}
        for df in tqdm(pd.read_csv(file_path,
                                   sep="\t",
                                   low_memory=False,
                                   usecols=use_cols,
                                   chunksize=chunksize), desc=f"Import {self.biodb_name.upper()}"):
            self._standardize_dataframe(df)

            df.drop(columns=['db_xrefs']).set_index(['description']).join(df_info_decr).set_index('gene_id').to_sql(
                table, self.engine, if_exists="append", index=True)
            inserted += df.shape[0]

            self._insert_info_xref(df)

        return inserted

    def update_interactions(self) -> int:
        """Abstract method."""
        pass
