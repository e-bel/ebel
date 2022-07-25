"""PathwayCommons module. Depends on HGNC."""

import warnings
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB

from ebel.constants import RID
from ebel.tools import get_file_path
from ebel.manager.orientdb.biodbs.hgnc import Hgnc
from ebel.manager.orientdb.constants import PATHWAY_COMMONS
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import hgnc, pathway_commons as pc


warnings.filterwarnings("ignore", 'This pattern has match groups')


class PathwayCommons(odb_meta.Graph):
    """Pathway Commons."""

    def __init__(self, client: OrientDB = None):
        """Init Pathway Commons."""
        self.client = client
        self.biodb_name = PATHWAY_COMMONS
        self.url = urls.PATHWAY_COMMONS
        self.urls = {self.biodb_name: self.url}
        self.file_path = get_file_path(self.url, self.biodb_name)

        super().__init__(generics=odb_structure.pathway_commons_generics,
                         edges=odb_structure.pathway_commons_edges,
                         tables_base=pc.Base,
                         urls=self.urls,
                         biodb_name=self.biodb_name)
        self.hgnc = Hgnc(self.client)

    def __len__(self) -> int:
        """Get number of edges in OrientDB."""
        return self.number_of_edges

    def __repr__(self) -> str:
        """Represent PathwayCommons Integration as string."""
        template = "{{BioDatabase:PathwayCommons}}[url:{url}, edges:{edges}, nodes:{generics}]"
        representation = template.format(
            url=self.url,
            edges=self.number_of_edges,
            generics=self.number_of_generics
        )
        return representation

    def __contains__(self, rs_number: int) -> bool:
        """Checks if RS number (without prefix RS) exists in BEL graph."""
        return self.entry_exists(self.biodb_name, rs_number=rs_number)

    def insert_data(self) -> Dict[str, int]:
        """Insert data in generic OrientDB class."""
        usecols = ['PARTICIPANT_A', 'INTERACTION_TYPE', 'PARTICIPANT_B', 'INTERACTION_DATA_SOURCE',
                   'INTERACTION_PUBMED_ID', 'PATHWAY_NAMES']

        df = pd.read_csv(self.file_path, sep="\t", low_memory=True, usecols=usecols)
        # Because 2 tables are in file, we have to identify where second table starts and slice the dataframe
        df = df.iloc[:df[df['PARTICIPANT_A'] == 'PARTICIPANT'].index[0]]

        df.columns = self._standardize_column_names(df.columns)
        df.pathway_names = df.pathway_names.str.split(';')
        df.interaction_data_source = df.interaction_data_source.str.split(';')
        df.interaction_pubmed_id = df.interaction_pubmed_id.str.split(';')

        df.index += 1
        df['id'] = df.index

        # insert main table
        df[['participant_a', 'participant_b', 'interaction_type']].to_sql(
            pc.PathwayCommons.__tablename__,
            self.engine, if_exists='append', index=False, chunksize=10000)

        # insert pmids, names, sources
        self.create_pmids_table(df)
        df_pc_names = self.create_names_table(df)
        df_pc_sources = self.create_sources_table(df)

        # joiing tables
        self.create_joining_table_sources(df, df_pc_sources)
        self.create_joining_table_names(df, df_pc_names)

        self.session.commit()
        return {self.biodb_name: df.shape[0]}

    def create_pmids_table(self, df):
        """Create the Pmid table."""
        df_pmids = df[['id', 'interaction_pubmed_id']].dropna().explode('interaction_pubmed_id')
        df_pmids.rename(columns={
            'id': 'pathway_commons_id',
            'interaction_pubmed_id': 'pmid'
        }, inplace=True)
        df_pmids.pmid = pd.to_numeric(df_pmids.pmid, errors='coerce')
        df_pmids.to_sql(pc.Pmid.__tablename__,
                        con=self.engine,
                        index=False,
                        if_exists='append',
                        chunksize=10000
                        )
        del df_pmids

    def create_joining_table_names(self, df, df_pc_names):
        """Create the joining table for Names."""
        df_pc_names_pc = df[['pathway_names', 'id']].explode('pathway_names').dropna()
        df_pc_names_pc.rename(columns={'id': "pathway_commons_id", 'pathway_names': "name"}, inplace=True)
        df_pc_names_pc.set_index('name', inplace=True)
        df_pc_names['pathway_commons_pathway_name_id'] = df_pc_names.index
        df_pc_names.set_index('name', inplace=True)
        df_pc_names_pc.join(df_pc_names, how='inner').to_sql(
            pc.pathway_commons__pathway_name.fullname,
            con=self.engine,
            index=False,
            if_exists='append',
            chunksize=10000
        )
        del df_pc_names_pc
        del df_pc_names

    def create_joining_table_sources(self, df, df_pc_sources):
        """Create the joining table for Source."""
        df_pc_sources_pc = df[['interaction_data_source', 'id']].explode('interaction_data_source').dropna()
        df_pc_sources_pc.rename(columns={'id': "pathway_commons_id", 'interaction_data_source': "source"},
                                inplace=True)
        df_pc_sources_pc.set_index('source', inplace=True)
        df_pc_sources['pathway_commons_source_id'] = df_pc_sources.index
        df_pc_sources.set_index('source', inplace=True)
        df_pc_sources_pc.join(df_pc_sources, how='inner').to_sql(
            pc.pathway_commons__source.fullname,
            con=self.engine,
            index=False,
            if_exists='append',
            chunksize=10000
        )
        del df_pc_sources_pc
        del df_pc_sources

    def create_sources_table(self, df):
        """Create the Sources table."""
        pc_sources = df.interaction_data_source.explode().str.strip().dropna().unique()
        df_pc_sources = pd.DataFrame(pc_sources, columns=['source'])
        df_pc_sources.index += 1
        df_pc_sources.index.rename('id', inplace=True)
        df_pc_sources.to_sql(pc.Source.__tablename__, self.engine, if_exists='append')
        return df_pc_sources

    def create_names_table(self, df):
        """Create the Names table."""
        pc_names = df.pathway_names.explode().str.strip().dropna().unique()
        df_pc_names = pd.DataFrame(pc_names, columns=['name'])
        df_pc_names.index += 1
        df_pc_names.index.rename('id', inplace=True)
        df_pc_names.to_sql(pc.PathwayName.__tablename__, self.engine, if_exists='append')
        return df_pc_names

    def get_pathway_name_rid_dict(self) -> Dict[str, str]:
        """Get dict of pathway names as keys and their rIDs as values."""
        pathway_name_rid_dict = {}
        number = self.get_number_of_class('pc_pathway_name')

        # insert data from rdbms in odb if not exists
        if number == 0:
            for pc_pathway_name, in self.session.query(pc.PathwayName.name).all():
                value_dict = {'name': pc_pathway_name}
                rid = self.insert_record('pc_pathway_name', value_dict)
                pathway_name_rid_dict[pc_pathway_name] = rid
        # get data from odb
        else:
            pc_pathway_names = self.query_class(class_name='pc_pathway_name', columns=['name'])
            pathway_name_rid_dict = {x['name']: x[RID] for x in pc_pathway_names}
        return pathway_name_rid_dict

    def _get_rid(self, rid, valid, name, pure_symbol_rids_dict):
        """Get the rID of an entry based on passed metadata."""
        _rid = None
        if isinstance(rid, str):
            _rid = rid
        else:
            if valid and name:
                if name in pure_symbol_rids_dict:
                    _rid = pure_symbol_rids_dict[name]
                else:
                    _rid = self.insert_record('protein', {'name': name,
                                                          'namespace': "HGNC",
                                                          'bel': f'p(HGNC:"{name}")',
                                                          'pure': True})
                    pure_symbol_rids_dict[name] = _rid
        return _rid

    def update_interactions(self) -> Dict[str, int]:
        """Update pathway commons interactions in graph."""
        inserted = {}

        pc_pathway_name_rid_dict = self.get_pathway_name_rid_dict()
        valid_hgnc_symbols = {x[0] for x in self.session.query(hgnc.Hgnc).with_entities(hgnc.Hgnc.symbol).all()}

        cols = ['symbol', 'rid']
        pure_symbol_rids_dict = self.hgnc.get_pure_symbol_rids_dict()
        df_all = pd.DataFrame(pure_symbol_rids_dict.items(), columns=cols)
        df_bel = pd.DataFrame(self.hgnc.get_pure_symbol_rids_dict_in_bel_context().items(),
                              columns=cols)

        # skip here if there is no pure symbols with or without BEL context
        if any([df_all.empty, df_bel.empty]):
            return inserted

        edge_types = ['controls-transport-of',
                      'controls-expression-of',
                      'controls-phosphorylation-of']

        for edge_type in edge_types:
            inserted[edge_type] = 0

            sql = f"""Select id, participant_a, participant_b from
                pathway_commons where interaction_type='{edge_type}'"""
            df_ppi_of = pd.read_sql(sql, self.engine)
            df_join = df_ppi_of.set_index('participant_a').join(df_all.set_index('symbol')).rename(
                columns={'rid': 'rid_a_all'}).join(df_bel.set_index('symbol')).reset_index().rename(
                columns={'rid': 'rid_a_bel', 'index': 'a'}).set_index('participant_b').join(
                df_all.set_index('symbol')).rename(columns={'rid': 'rid_b_all'}).join(
                df_bel.set_index('symbol')).reset_index().rename(columns={'rid': 'rid_b_bel', 'index': 'b'}).set_index(
                'id')

            df_join['a_is_valid'] = [(x in valid_hgnc_symbols) for x in df_join.a]
            df_join['b_is_valid'] = [(x in valid_hgnc_symbols) for x in df_join.b]

            a_or_b_in_bel = (df_join.rid_a_bel.notnull() | df_join.rid_b_bel.notnull())
            both_valid = (df_join.a_is_valid & df_join.b_is_valid)
            df_both = df_join[(a_or_b_in_bel & both_valid)]

            for pc_id, row in tqdm(df_both.iterrows(), total=df_both.shape[0], desc=f'Update PC {edge_type}'):

                from_rid = self._get_rid(row.rid_a_all, row.a_is_valid, row.a, pure_symbol_rids_dict)
                to_rid = self._get_rid(row.rid_b_all, row.b_is_valid, row.b, pure_symbol_rids_dict)

                if from_rid and to_rid:
                    pathways, pmids, sources = self.get_pathway_pmids_sources(pc_id, pc_pathway_name_rid_dict)
                    value_dict = {
                        'type': edge_type,
                        'sources': sources,
                        'pmids': pmids,
                        'pathways': pathways
                    }

                    class_name = edge_type.replace('-', '_') + "_pc"
                    self.create_edge(class_name=class_name,
                                     from_rid=from_rid,
                                     to_rid=to_rid,
                                     value_dict=value_dict,
                                     ignore_empty_values=True)
                    inserted[edge_type] += 1

        return inserted

    def get_pathway_pmids_sources(self, pc_id, pc_pathway_name_rid_dict) -> tuple:
        """Return all pathway, PMIDs, and their sources."""
        pc_obj = self.session.query(pc.PathwayCommons).get(pc_id)
        sources = [x.source for x in pc_obj.sources]
        pmids = [x.pmid for x in pc_obj.pmids]
        pathways = [pc_pathway_name_rid_dict[x.name] for x in pc_obj.pathway_names]
        return pathways, pmids, sources
