"""BioGrid."""

import typing
import numpy as np
import pandas as pd
from enum import Enum

from tqdm import tqdm
from pyorientdb import OrientDB
from typing import Dict, Tuple

from ebel import tools
from ebel.manager.orientdb.constants import BIOGRID
from ebel.manager.orientdb import odb_meta, odb_structure, urls
from ebel.manager.orientdb.odb_defaults import BelPmod, normalized_pmod_reverse

from ebel.manager.rdbms.models import biogrid

STANDARD_NAMESPACES = {
    9606: 'HGNC',
    10090: 'MGI',
    10116: 'RGD'
}


class BioGridNode:
    """Custom class definition for BioGRID nodes."""

    def __init__(self, rid: str, symbol: str, uniprot: str, taxonomy_id: int, pmod_bel: str = None):
        """Init for BioGRID generated nodes."""
        self.rid = rid
        self.symbol: str = symbol
        self.uniprot: str = uniprot
        self.taxonomy_id: int = taxonomy_id
        self.namespace, self.name = self.__get_nn()
        self.pmod_bel = pmod_bel

    def __get_nn(self) -> Tuple[str, str]:
        if self.taxonomy_id in STANDARD_NAMESPACES:
            namespace = STANDARD_NAMESPACES[self.taxonomy_id]
            name = self.symbol
        else:
            namespace = 'UNIPROT'
            name = self.uniprot
        return namespace, name

    def __get_protein_as_value_dict(self, pmod: bool = False):
        if pmod:
            bel = self.get_pmod_protein_bel()
        else:
            bel = self.get_protein_bel()

        value_dict = {'name': self.name,
                      'namespace': self.namespace,
                      'bel': bel,
                      'uniprot': self.uniprot}
        return value_dict

    def get_pmod_protein_as_value_dict(self):
        """Get all pmod node metadata as dictionary."""
        return self.__get_protein_as_value_dict(pmod=True)

    def get_protein_as_value_dict(self):
        """Get all protein node metadata as dictionary."""
        return self.__get_protein_as_value_dict(pmod=False)

    def get_pmod_protein_bel(self) -> str:
        """Get the namespace and value for a protein and it's protein modification."""
        return f'p({self.namespace}:"{self.name}",pmod({self.pmod_bel}))'

    def get_protein_bel(self) -> str:
        """Get the namespace and value for a protein."""
        return f'p({self.namespace}:"{self.name}")'

    def get_pmod_bel(self):
        """Get the protein modification for a BEL."""
        return {'bel': f"pmod({self.pmod_bel})", 'type': normalized_pmod_reverse[self.pmod_bel]}


class BioGridEdge:
    """Class definition for BioGRID edges."""

    def __init__(self, subject_rid: str, subject_symbol: str, subject_uniprot: str, subject_taxonomy_id: int,
                 modification: str, object_rid: str, object_symbol: str, object_uniprot: str, object_taxonomy_id: int,
                 experimental_system: str, pmids: str, num_pubs: int, dois: str, biogrid_ids: str):
        """Init for BioGRID edges."""
        mods = Modification.get_reverse_dict()
        self.modification = modification

        self.modConfig: ModConfig = mods[modification]

        self.subj: BioGridNode = BioGridNode(subject_rid, subject_symbol, subject_uniprot, subject_taxonomy_id,
                                             self.modConfig.pmod_bel)
        self.obj: BioGridNode = BioGridNode(object_rid, object_symbol, object_uniprot, object_taxonomy_id,
                                            self.modConfig.pmod_bel)

        self.experimental_system: str = experimental_system
        self.pmids: str = pmids
        self.num_pubs: int = num_pubs
        self.dois: str = dois
        self.biogrid_ids = biogrid_ids

    @property
    def both_pure_proteins_exists(self):
        """Check if both subject and object exist."""
        return bool(self.subj.rid) and bool(self.obj.rid)

    def get_edge_value_dict(self):
        """Get edge value dictionary."""
        value_dict = {'modification': self.modification}
        if self.dois:
            value_dict['dois'] = self.dois.split(',')
        if self.pmids:
            value_dict['pmids'] = [int(x) for x in self.pmids.split(',')]
        if self.biogrid_ids:
            value_dict['biogrid_ids'] = [int(x) for x in self.biogrid_ids.split(',')]
        return value_dict

    def get_pmod_as_value_dict(self):
        """Get pmod metadata as dictionary."""
        return {'bel': f'pmod({self.modConfig.pmod_bel})', 'type': normalized_pmod_reverse[self.modConfig.pmod_bel]}

    @property
    def edge_name(self):
        """Get edge name."""
        return self.modConfig.effect + '_' + normalized_pmod_reverse[self.modConfig.pmod_bel] + '_bg'


class Effect:
    """Class definition for Effect."""

    INCREASES = 'increases'
    DECREASES = 'decreases'


class ModConfig:
    """Modification configuration."""

    def __init__(self, bg_mod_name: str, effect: str, pmod_bel: str = None):
        """Init method for ModConfig class.

        Parameters
        ----------
        bg_mod_name: str
            BioGrid modification name
        effect: str
            Effect of BioGrid Edge
        pmod_bel: str
            Posttranslational modification as BEL
        """
        self.bg_mod_name: str = bg_mod_name
        self.effect: str = effect
        self.pmod_bel: str = pmod_bel


class Modification(Enum):
    """BioGrid modification and configuration for BEL converting."""

    PHOSPHORYLATION: ModConfig = ModConfig('Phosphorylation', Effect.INCREASES, BelPmod.PHO)
    UBIQUITINATION: ModConfig = ModConfig('Ubiquitination', Effect.INCREASES, BelPmod.UBI)
    ACETYLATION: ModConfig = ModConfig('Acetylation', Effect.INCREASES, BelPmod.ACE)
    DEUBIQUITINATION: ModConfig = ModConfig('Deubiquitination', Effect.DECREASES, BelPmod.UBI)
    PROTEOLYTIC_PROCESSING: ModConfig = ModConfig('Proteolytic Processing', Effect.DECREASES)
    METHYLATION: ModConfig = ModConfig('Methylation', Effect.INCREASES, BelPmod.ME0)
    SUMOYLATION: ModConfig = ModConfig('Sumoylation', Effect.INCREASES, BelPmod.SUM)
    DEPHOSPHORYLATION: ModConfig = ModConfig('Dephosphorylation', Effect.DECREASES, BelPmod.PHO)
    DEACETYLATION: ModConfig = ModConfig('Deacetylation', Effect.DECREASES, BelPmod.ACE)
    NEDD_RUB1_YLATION: ModConfig = ModConfig('Nedd(Rub1)ylation', Effect.INCREASES, BelPmod.NED)
    RIBOSYLATION: ModConfig = ModConfig('Ribosylation', Effect.INCREASES, BelPmod.ADD)
    DESUMOYLATION: ModConfig = ModConfig('Desumoylation', Effect.DECREASES, BelPmod.SUM)
    DEMETHYLATION: ModConfig = ModConfig('Demethylation', Effect.DECREASES, BelPmod.ME0)
    DENEDDYLATION: ModConfig = ModConfig('Deneddylation', Effect.DECREASES, BelPmod.NED)
    PRENYLATION: ModConfig = ModConfig('Prenylation', Effect.INCREASES, BelPmod.PRE)
    GLYCOSYLATION: ModConfig = ModConfig('Glycosylation', Effect.INCREASES, BelPmod.GLY)
    NEDDYLATION: ModConfig = ModConfig('Neddylation', Effect.INCREASES, BelPmod.NED)
    DE_ISGYLATION: ModConfig = ModConfig('de-ISGylation', Effect.INCREASES, BelPmod.DEI)
    FAT10YLATION: ModConfig = ModConfig('FAT10ylation', Effect.INCREASES, BelPmod.FAT)

    @classmethod
    def get_reverse_dict(cls) -> typing.Dict[str, ModConfig]:
        """Reverse the key and values for the dictionary."""
        return {cls.__members__[x].value.bg_mod_name: cls.__members__[x].value for x in cls.__members__}


MODIFICATIONS = tuple(Modification.get_reverse_dict().keys())


class BioGrid(odb_meta.Graph):
    """Class definition for BioGRID."""

    def __init__(self, client: OrientDB = None):
        """Biogrid database."""
        self.client = client
        self.biodb_name = BIOGRID
        self.url = urls.BIOGRID
        self.urls = {self.biodb_name: self.url}
        super().__init__(edges=odb_structure.biogrid_edges,
                         urls=self.urls,
                         tables_base=biogrid.Base,
                         biodb_name=self.biodb_name)
        self.file_path = tools.get_file_path(urls.BIOGRID, self.biodb_name)

        self.bel_rid_cache = {}

    def __len__(self) -> int:
        """Get number of 'biogrid_interaction' graph edges."""
        return self.number_of_edges['biogrid_interaction']

    def __contains__(self, biogrid_id) -> bool:
        """Check if biogrid_interaction edge with biogrid_id exists in graph."""
        # TODO: Check if this is still valid
        sql = "Select 1 from biogrid_interaction where any(biogrid).biogrid_id = {}".format(biogrid_id)
        return bool(len(self.execute(sql)))

    def insert_data(self) -> Dict[str, int]:
        """Insert BioGRID data into database."""
        use_columns = {'#BioGRID Interaction ID': 'biogrid_id',
                       'BioGRID ID Interactor A': 'biogrid_a_id',
                       'BioGRID ID Interactor B': 'biogrid_b_id',
                       'Entrez Gene Interactor A': 'entrez_a',
                       'Entrez Gene Interactor B': 'entrez_b',
                       'Systematic Name Interactor A': 'systematic_name_a',
                       'Systematic Name Interactor B': 'systematic_name_b',
                       'Official Symbol Interactor A': 'symbol_a',
                       'Official Symbol Interactor B': 'symbol_b',
                       'Experimental System': 'experimental_system',
                       'Experimental System Type': 'experimental_system_type',
                       'Author': 'author',
                       'Publication Source': 'publication_source',
                       'Organism ID Interactor A': 'taxonomy_a_id',
                       'Organism ID Interactor B': 'taxonomy_b_id',
                       'Throughput': 'throughput',
                       'Score': 'score',
                       'Modification': 'modification',
                       'Qualifications': 'qualification',
                       'Source Database': 'source',
                       'SWISS-PROT Accessions Interactor A': 'uniprot_a',
                       'TREMBL Accessions Interactor A': 'trembl_a',
                       'SWISS-PROT Accessions Interactor B': 'uniprot_b',
                       'TREMBL Accessions Interactor B': 'trembl_b',
                       'Organism Name Interactor A': 'org_a',
                       'Organism Name Interactor B': 'org_b'}

        # main table
        df = pd.read_csv(self.file_path, usecols=use_columns.keys(), sep="\t", low_memory=False)
        df.rename(columns=use_columns, inplace=True)
        df.replace('-', np.nan, inplace=True)

        # experimental system
        df = self._create_experimental_system_table(df)

        # taxonomy
        self._create_taxonomy_table(df)

        # source
        df = self._create_source_table(df)

        # interactor
        df = self._create_interactor_table(df)

        # modification
        df = self._create_modification_table(df)

        # throughput
        df = self._create_throughput_table(df)

        # publication
        df = self._create_publication_table(df)

        # save main
        df.index += 1
        df.index.rename('id', inplace=True)

        df.to_sql(biogrid.Biogrid.__tablename__, self.engine, if_exists="append")

        return {self.biodb_name: df.shape[0]}

    def _create_publication_table(self, df: pd.DataFrame) -> pd.DataFrame:
        df_ay = df.author.str.extract(r'^(?P<author_name>[^(]+)\s*\((?P<publication_year>\d+)\)$')
        df_source = df.publication_source.str.extract(r'^(?P<source>[^:]+):(?P<source_identifier>.*)')
        df_pub = pd.concat([df_ay, df_source, df.publication_source], axis=1)
        df_pub.drop_duplicates(inplace=True)
        df_pub.reset_index(inplace=True)
        df_pub.index += 1
        df_pub.index.rename('id', inplace=True)
        df_pub['publication_id'] = df_pub.index
        df_pub_4join = df_pub.set_index('publication_source')[['publication_id']]
        df = df_pub_4join.join(df.set_index('publication_source'), how="right").reset_index().drop(
            columns=['publication_source', 'author'])
        df_pub.drop(columns=['publication_source', 'index', 'publication_id'], inplace=True)
        df_pub.to_sql(biogrid.Publication.__tablename__, self.engine, if_exists='append')

        return df

    def _create_modification_table(self, df: pd.DataFrame) -> pd.DataFrame:
        df_mod = df[['modification']].dropna().value_counts().reset_index().rename(columns={0: 'frequency'})
        df_mod.index += 1
        df_mod.index.rename('id', inplace=True)
        df_mod['modification_id'] = df_mod.index
        df = df_mod.set_index('modification')[['modification_id']].join(df.set_index('modification'),
                                                                        how="right").reset_index().drop(
            columns=['modification'])
        df_mod.drop(columns=['modification_id']).to_sql(biogrid.Modification.__tablename__, self.engine,
                                                        if_exists='append')
        return df

    def _create_throughput_table(self, df: pd.DataFrame) -> pd.DataFrame:
        df_tp = df[['throughput']].value_counts().reset_index().rename(columns={0: 'frequency'})
        df_tp.index += 1
        df_tp.index.rename('id', inplace=True)
        df_tp['throughput_id'] = df_tp.index
        df_tp_join = df_tp.set_index('throughput')[['throughput_id']]
        df = df_tp_join.join(df.set_index('throughput'), how="right").reset_index().drop(columns=['throughput'])
        df_tp.drop(columns=['throughput_id'], inplace=True)
        df_tp.to_sql(biogrid.Throughput.__tablename__, self.engine, if_exists='append')
        return df

    def _create_interactor_table(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = ['entrez', 'biogrid_id', 'systematic_name',
                   'symbol', 'uniprot', 'trembl', 'taxonomy_id']
        cols_a = ['entrez_a', 'biogrid_a_id', 'systematic_name_a',
                  'symbol_a', 'uniprot_a', 'trembl_a', 'taxonomy_a_id']
        cols_b = ['entrez_b', 'biogrid_b_id', 'systematic_name_b',
                  'symbol_b', 'uniprot_b', 'trembl_b', 'taxonomy_b_id']
        df_a = df[cols_a]
        df_a.columns = columns
        df_b = df[cols_b]
        df_b.columns = columns
        df_ia = pd.concat([df_a.set_index('biogrid_id'), df_b.set_index('biogrid_id')]).drop_duplicates()
        # extract the first accession
        df_ia.uniprot = df_ia.uniprot.str.split('|').str[0]
        df_ia.trembl = df_ia.trembl.str.split('|').str[0]
        df_ia.replace('-', None).to_sql(biogrid.Interactor.__tablename__, self.engine, if_exists='append')
        cols4delete = list(set(cols_a + cols_b) - {'biogrid_a_id', 'biogrid_b_id'})
        df.drop(columns=cols4delete, inplace=True)
        return df

    def _create_experimental_system_table(self, df: pd.DataFrame) -> pd.DataFrame:
        # extract ExperimentalSystem
        df_exp = df[['experimental_system', 'experimental_system_type']].value_counts().reset_index().rename(
            columns={0: 'frequency'})
        df_exp.index += 1
        df_exp.index.rename('id', inplace=True)
        df_exp['experimental_system_id'] = df_exp.index
        # join ExperimentalSystem ID to main table and drop cols experimental_system, experimental_system_type
        df = df_exp.set_index(['experimental_system', 'experimental_system_type'])[['experimental_system_id']].join(
            df.set_index(['experimental_system', 'experimental_system_type'])).reset_index().drop(
            columns=['experimental_system', 'experimental_system_type'])
        # save ExperimentalSystem
        df_exp.drop(columns=['experimental_system_id']).to_sql(biogrid.ExperimentalSystem.__tablename__, self.engine,
                                                               if_exists='append')
        return df

    def _create_taxonomy_table(self, df: pd.DataFrame):
        df_org_a = df[['taxonomy_a_id', 'org_a']].rename(
            columns={'taxonomy_a_id': 'taxonomy_id', 'org_a': 'organism_name'})
        df_org_b = df[['taxonomy_b_id', 'org_b']].rename(
            columns={'taxonomy_b_id': 'taxonomy_id', 'org_b': 'organism_name'})
        df_taxonomy = pd.concat([df_org_a, df_org_b])
        df_taxonomy.drop_duplicates(inplace=True)
        df_taxonomy.reset_index(inplace=True)
        df_taxonomy.drop(columns=['index'], inplace=True)
        df_taxonomy.set_index('taxonomy_id', inplace=True)
        df_taxonomy.to_sql(biogrid.Taxonomy.__tablename__, self.engine, if_exists='append')
        df.drop(columns=['org_a', 'org_b'], inplace=True)

    def _create_source_table(self, df: pd.DataFrame) -> pd.DataFrame:
        df_source = df[['source']].drop_duplicates().reset_index().drop(columns=['index'])
        df_source.index += 1
        df_source.index.rename('id', inplace=True)
        df_source['source_id'] = df_source.index
        df = df_source.set_index(['source']).join(df.set_index(['source'])).reset_index().drop(columns=['source'])
        df_source.drop(columns=['source_id']).to_sql(biogrid.Source.__tablename__, self.engine, if_exists='append')
        return df

    def get_uniprot_modification_pairs(self):
        """Return all UniProt modification pairs."""
        # TODO: sql as sqlalchemy query
        sql = """Select
            ia.symbol as subject_symbol,
            ia.uniprot as subject_uniprot,
            ia.taxonomy_id as subject_taxonomy_id,
            ib.symbol as object_symbol,
            ib.uniprot as object_uniprot,
            ib.taxonomy_id as object_taxonomy_id
        from
            biogrid b
            inner join biogrid_interactor ia on (b.biogrid_a_id=ia.biogrid_id)
            inner join biogrid_interactor ib on (b.biogrid_b_id=ib.biogrid_id)
            inner join biogrid_modification m on (m.id=b.modification_id)
        where
            m.modification != 'No Modification' and ia.uniprot IS NOT NULL and ib.uniprot IS NOT NULL
        group by
            ia.symbol,
            ia.uniprot,
            ia.taxonomy_id,
            ib.symbol,
            ib.uniprot,
            ib.taxonomy_id"""
        return [dict(x) for x in self.engine.execute(sql).fetchall()]

    def get_create_pure_protein_rid_by_uniprot(self, taxonomy_id, symbol, uniprot):
        """Get pure protein rid by UniProt accession ID if the protein is involved in a BEL statement."""
        namespace = STANDARD_NAMESPACES.get(taxonomy_id, 'UNIPROT')
        name = uniprot if namespace == 'UNIPROT' else symbol
        bel = f'p({namespace}:"{name}")'

        if bel in self.bel_rid_cache:
            rid = self.bel_rid_cache[bel]
        else:
            value_dict = {'bel': bel, 'pure': True, 'namespace': namespace, 'name': name}
            rid = self.get_create_rid('protein', value_dict=value_dict, check_for='bel')
            self.bel_rid_cache[bel] = rid
        return rid

    def update_interactions(self) -> int:
        """Updates all BioGrid interactions."""
        # TODO: sql_temp as sqlalchemy query
        sql_temp = """
        Select
            ia.symbol as subject_symbol,
            ia.uniprot as subject_uniprot,
            ia.taxonomy_id as subject_taxonomy_id,
            m.modification,
            ib.symbol as object_symbol,
            ib.uniprot as object_uniprot,
            ib.taxonomy_id as object_taxonomy_id,
            es.experimental_system,
            group_concat( distinct b.biogrid_id) as biogrid_ids,
            group_concat( distinct if(p.source='PUBMED',CAST(p.source_identifier AS UNSIGNED),NULL)) as pmids,
            count(distinct p.source_identifier) as num_pubs,
            group_concat( distinct if(p.source='DOI',CAST(p.source_identifier AS UNSIGNED),NULL)) as dois
        from
            biogrid b
            inner join biogrid_interactor ia on (b.biogrid_a_id=ia.biogrid_id)
            inner join biogrid_interactor ib on (b.biogrid_b_id=ib.biogrid_id)
            inner join biogrid_modification m on (m.id=b.modification_id)
            inner join biogrid_publication p on (b.publication_id=p.id)
            inner join biogrid_experimental_system es on (b.experimental_system_id=es.id)
        where
            (ia.uniprot = '{subject_uniprot}' and ib.uniprot = '{object_uniprot}') and
            m.modification != 'No Modification'
        group by
            ia.symbol,
            ia.uniprot,
            ia.taxonomy_id,
            m.modification,
            ib.symbol,
            ib.uniprot,
            ib.taxonomy_id,
            es.experimental_system"""

        uniprots_in_bel_set = self.get_pure_uniprots_in_bel_context()
        uniprot_modification_pairs = self.get_uniprot_modification_pairs()

        counter = 0
        self.clear_edges()

        for e in tqdm(uniprot_modification_pairs, desc=f"Update {self.biodb_name.upper()} interactions"):
            if e['subject_uniprot'] in uniprots_in_bel_set or e['object_uniprot'] in uniprots_in_bel_set:
                subj_pure_rid = self.get_create_pure_protein_rid_by_uniprot(
                    taxonomy_id=e['subject_taxonomy_id'],
                    symbol=e['subject_symbol'],
                    uniprot=e['subject_uniprot']
                )

                obj_pure_rid = self.get_create_pure_protein_rid_by_uniprot(
                    taxonomy_id=e['object_taxonomy_id'],
                    symbol=e['object_symbol'],
                    uniprot=e['object_uniprot']
                )

                sql = sql_temp.format(subject_uniprot=e['subject_uniprot'], object_uniprot=e['object_uniprot'])

                for row in self.engine.execute(sql).fetchall():
                    row_dict = dict(row)
                    be = BioGridEdge(subject_rid=subj_pure_rid, object_rid=obj_pure_rid, **row_dict)
                    edge_value_dict = be.get_edge_value_dict()

                    if be.modConfig.bg_mod_name == 'Proteolytic Processing':
                        self.create_edge('decreases_bg',
                                         from_rid=subj_pure_rid,
                                         to_rid=obj_pure_rid,
                                         value_dict=edge_value_dict)
                        counter += 1
                    else:
                        obj_pmod_value_dict = be.obj.get_pmod_protein_as_value_dict()
                        pmod_protein_rid = self.node_exists('protein', obj_pmod_value_dict, check_for='bel')
                        if not pmod_protein_rid:
                            pmod_protein_rid = self.get_create_rid('protein', obj_pmod_value_dict, check_for='bel')
                            self.create_edge('has_modified_protein', obj_pure_rid, pmod_protein_rid)
                            pmod_rid = self.insert_record('pmod', be.get_pmod_as_value_dict())
                            self.create_edge('has__pmod', pmod_protein_rid, pmod_rid)
                        self.create_edge(be.edge_name, subj_pure_rid, pmod_protein_rid, edge_value_dict)
                        counter += 1
        return counter

    def create_view(self):
        """Create SQL view of BioGRID data."""
        sql = """create view if not exists biogrid_view as
            select
                b.biogrid_id,
                ia.symbol as symbol_a,
                ia.uniprot as uniprot_a,
                ta.taxonomy_id as tax_id_a,
                ta.organism_name as organism_a,
                ib.symbol as symbol_b,
                ib.uniprot as uniprot_b,
                tb.taxonomy_id as tax_id_b,
                tb.organism_name as organism_b,
                es.experimental_system,
                m.modification,
                s.source,
                b.qualification,
                p.source as publication_source,
                p.source_identifier as publication_identifier
            from
                biogrid b inner join
                biogrid_interactor ia on (ia.biogrid_id=b.biogrid_a_id) inner join
                biogrid_interactor ib on (ib.biogrid_id=b.biogrid_b_id) inner join
                biogrid_taxonomy ta on (ia.taxonomy_id=ta.taxonomy_id) inner join
                biogrid_taxonomy tb on (ib.taxonomy_id=tb.taxonomy_id) left join
                biogrid_experimental_system es on (b.experimental_system_id=es.id) left join
                biogrid_modification m on (m.id=b.modification_id) left join
                biogrid_source s on (s.id=b.source_id) left join
                biogrid_publication p on (p.id=b.publication_id)"""
        self.engine.execute(sql)
