"""IUPHAR drug module."""

import logging
import numpy as np
import pandas as pd

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB

from ebel.tools import get_file_path
from ebel.manager.orientdb.constants import IUPHAR
from ebel.manager.orientdb.biodbs.uniprot import UniProt
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import iuphar

logger = logging.getLogger(__name__)


class Iuphar(odb_meta.Graph):
    """IUPHAR."""

    def __init__(self, client: OrientDB = None):
        """Init IUPHAR."""
        self.client = client
        self.biodb_name = IUPHAR
        self.urls = {'iuphar_int': urls.IUPHAR_INT, 'iuphar_ligands': urls.IUPHAR_LIGANDS}
        super().__init__(edges=odb_structure.iuphar_edges,
                         tables_base=iuphar.Base,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.number_of_generics

    def __contains__(self, item):
        # TODO: To be implemented
        return True

    def insert_data(self) -> Dict[str, int]:
        """Insert data in generic OrientDB class."""
        ligands = self.insert_ligand_data()
        ints = self.insert_interaction_data()

        self.session.commit()
        return {'ligands': ligands, 'interactions': ints}

    def insert_ligand_data(self) -> int:
        """Insert ligand/drug data in generic OrientDB class."""
        logger.info("Reading and formatting IUPHAR drug data")
        df = pd.read_csv(get_file_path(self.urls['iuphar_ligands'], self.biodb_name),
                         sep=",",
                         low_memory=False,
                         # dtype={'Ligand id': 'Int64', 'PubChem SID': 'Int64', 'PubChem CID': 'Int64'},
                         true_values=['yes']).replace({np.nan: None})  # Convert 'yes' to True
        df.columns = self._standardize_column_names(df.columns)
        df.rename(columns={'in_ch_i': 'inchi',
                           'in_ch_ikey': 'inchi_key',
                           'pub_chem_cid': 'pubchem_cid',
                           'pub_chem_sid': 'pubchem_sid',
                           'uni_prot_id': 'uniprot_id',
                           'ligand_id': 'id'}, inplace=True)  # Make it consistent with drugbank
        df.set_index('id', inplace=True)
        df.to_sql(iuphar.IupharLigand.__tablename__, self.engine, if_exists='append')

        return df.shape[0]

    def insert_interaction_data(self) -> int:
        """Insert interaction data in generic OrientDB class."""
        logger.info("Reading and formatting IUPHAR interaction data.")
        df = pd.read_csv(get_file_path(self.urls['iuphar_int'], self.biodb_name),
                         sep=",",
                         low_memory=False,
                         dtype={'target_id': 'Int64', 'ligand_pubchem_sid': 'Int64', 'ligand_id': 'Int64',
                                'target_ligand_id': 'Int64', 'target_ligand_pubchem_sid': 'Int64'},
                         true_values=['t'],
                         false_values=['f']).replace({np.nan: None})

        # df['pubmed_id'] = df['pubmed_id'].str.split("|")  # Split synonyms
        df.index += 1
        df.index.rename('id', inplace=True)
        df.to_sql(iuphar.IupharInteraction.__tablename__, self.engine, if_exists='append')

        return df.shape[0]

    def update_interactions(self) -> int:
        """Update the ligands/drug generic table to include a link to all interactions it is part of."""
        self.clear_edges()
        uniprot = UniProt(self.client)

        iuphar_edge_type_mapper = {
            'Agonist': 'agonist_of__iu',
            'Inhibitor': 'inhibits__iu',
            'Antagonist': 'antagonist_of__iu',
            'Channel blocker': 'channel_blocker_of__iu',
            'Allosteric modulator': 'allosteric_modulator_of__iu',
            'Activator': 'activates__iu',
            'Antibody': 'antibody_against__iu',
            'Gating inhibitor': 'inhibits_gating__iu'
        }

        sql = """select i.pubmed_id, i.assay_description, i.affinity_units, i.affinity_low, i.affinity_median,
        i.affinity_high, i.type,
        i.action,i.target_uniprot, l.name as ligand_name, l.pubchem_sid, i.ligand_gene_symbol, i.ligand_species
        from iuphar_interaction as i inner join iuphar_ligand as l
        on (i.ligand_id=l.id) where i.target_uniprot IS NOT NULL and pubchem_sid IS NOT NULL"""

        df_iuphar = pd.read_sql(sql, self.engine).replace({np.nan: None})
        df_iuphar.set_index('target_uniprot', inplace=True)
        df_graph = pd.DataFrame(
            uniprot.get_pure_uniprot_rid_dict_in_bel_context().items(),
            columns=['target_uniprot', 'rid'])
        df_graph.set_index('target_uniprot', inplace=True)
        df_join = df_graph.join(df_iuphar, how='inner')

        for uniprot, data in tqdm(df_join.iterrows(), total=df_join.shape[0],
                                  desc=f"Update {self.biodb_name.upper()} interactions"):
            if data.ligand_gene_symbol and data.ligand_species and 'Human' in data.ligand_species:
                symbol = data.ligand_gene_symbol.split('|')[0]  # human seems to always the first
                a_value_dict = {'pure': True,
                                'bel': f'p(HGNC:"{symbol}")',
                                'namespace': 'HGNC',
                                'name': symbol,
                                }
                a_class = 'protein'
            else:
                a_value_dict = {'pure': True,
                                'bel': f'a(PUBCHEM:"{data.pubchem_sid}")',
                                'namespace': 'PUBCHEM',
                                'name': str(data.pubchem_sid),
                                'label': data.ligand_name
                                }
                a_class = 'abundance'
            a_rid = self.get_create_rid(a_class, value_dict=a_value_dict, check_for='bel')

            i_value_dict = {'pmids': data.pubmed_id.split('|') if data.pubmed_id else None,
                            'assay_description': data.assay_description,
                            'affinity_units': data.affinity_units,
                            'affinity_low': data.affinity_low,
                            'affinity_median': data.affinity_median,
                            'affinity_high': data.affinity_high,
                            'type': data.type,
                            'action': data.action}
            edge_class = iuphar_edge_type_mapper.get(data.type, 'iuphar_interaction')
            self.create_edge(edge_class, from_rid=a_rid, to_rid=data.rid, value_dict=i_value_dict)

        # not sure if this is really needed
        # Hgnc(self.client).update_bel()

        return df_join.shape[0]
