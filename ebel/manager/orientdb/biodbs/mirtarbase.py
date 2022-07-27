"""miRTarBase."""
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB

from ebel.tools import get_file_path
from ebel.manager.orientdb.constants import MIRTARBASE
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import mirtarbase


class MirTarBase(odb_meta.Graph):
    """MirTarBase (from NCBI)."""

    def __init__(self, client: OrientDB = None):
        """Init MirTarBase (http://mirtarbase.mbc.nctu.edu.tw)."""
        self.client = client
        self.biodb_name = MIRTARBASE
        self.urls = {self.biodb_name: urls.MIRTARBASE}
        self.file_path = get_file_path(urls.MIRTARBASE, self.biodb_name)
        super().__init__(urls=self.urls,
                         tables_base=mirtarbase.Base,
                         edges=odb_structure.mirtarbase_edges,
                         biodb_name=self.biodb_name)

    def __len__(self) -> Dict[str, int]:
        return self.number_of_generics

    def __contains__(self, item) -> bool:
        # TODO: To be implemented
        return True

    def insert_data(self) -> Dict[str, int]:
        """Insert mirtarbase data into database."""
        # TODO Fix download error -
        #  ssl.SSLError: [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure (_ssl.c:997)
        df = pd.read_excel(self.file_path)
        df.columns = self._standardize_column_names(df.columns)
        df.index += 1
        df.index.rename('id', inplace=True)

        df.to_sql(mirtarbase.Mirtarbase.__tablename__, self.engine, if_exists='append', chunksize=10000)

        return {self.biodb_name: df.shape[0]}

    def update_interactions(self) -> int:
        """Update edges with mirtarbase metadata."""
        self.clear_edges()
        df_symbol_rid = self.get_pure_symbol_rid_df_in_bel_context(class_name='rna', namespace='HGNC')

        sql = f"""Select
                mi_rna,
                target_gene as symbol,
                support_type,
                references_pmid as pmid,
                experiments
            from
                {mirtarbase.Mirtarbase.__tablename__}
            where
                species_mi_rna='Homo sapiens' and
                species_target_gene='Homo sapiens' and
                support_type in ('Functional MTI', 'Non-Functional MTI')"""
        cols = ['mi_rna', 'symbol', 'support_type', 'pmid', 'experiments']
        df_mirtarbase = pd.DataFrame(self.engine.execute(sql).fetchall(), columns=cols)
        df_mirtarbase.experiments = df_mirtarbase.experiments.str.split('//')
        df_join = df_mirtarbase.set_index('symbol').join(df_symbol_rid.set_index('symbol'), how='inner')

        desc = f"Update {self.biodb_name.upper()} interactions"

        updated = 0
        for protein_rid, row in tqdm(df_join.set_index('rid').iterrows(), total=df_join.shape[0], desc=desc):
            mir_data = {'bel': f'm(MIRBASE:"{row.mi_rna}")',
                        'name': row.mi_rna,
                        'namespace': "MIRBASE",
                        'pure': True}
            mir_rid = self.get_create_rid('micro_rna', mir_data, check_for='bel')
            value_dict = {'support_type': row.support_type,
                          'pmid': row.pmid,
                          'experiments': row.experiments}
            self.create_edge('has_mirgene_target', mir_rid, str(protein_rid), value_dict=value_dict)
            updated += 1

        return updated
