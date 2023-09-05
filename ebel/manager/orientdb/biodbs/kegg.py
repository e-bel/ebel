"""KEGG implemention. Dependent on HGNC."""

import os
import re
import requests
import pandas as pd
import xml.etree.ElementTree as ET

from tqdm import tqdm
from typing import Dict
from pyorientdb import OrientDB

from ebel.defaults import DATA_DIR
from ebel.config import get_config_value
from ebel.manager.orientdb.constants import KEGG
from ebel.manager.orientdb.biodbs.hgnc import Hgnc
from ebel.manager.orientdb.odb_defaults import BelPmod
from ebel.manager.orientdb import odb_meta, urls, odb_structure

from ebel.manager.rdbms.models import kegg


class Kegg(odb_meta.Graph):
    """KEGG class.

    Parses KEGG Markup Language (KGML, https://www.genome.jp/kegg/xml/docs/) and translates to ebel edges.
    """

    def __init__(self, client: OrientDB = None):
        """Init KEGG."""
        self.client = client
        self.biodb_name = KEGG
        self.urls = {'kegg_path_list': urls.KEGG_PATH_LIST}

        # TODO Improve KGML folder creation
        self.file_paths = {'kgml': os.path.join(DATA_DIR, self.biodb_name, 'kgml')}
        _ = [os.makedirs(bio_db_dir, exist_ok=True) for bio_db_dir in self.file_paths.values()]

        super().__init__(tables_base=kegg.Base,
                         edges=odb_structure.kegg_edges,
                         urls=self.urls,
                         biodb_name=self.biodb_name
                         )

        species_list = get_config_value(section="KEGG", option="species", value="hsa, dme, mmu, rno")
        self.species = [species_id.strip() for species_id in species_list.split(",")]

        # TODO Make so it builds dict from info from KEGG directly. JSON url in urls.py, needs method to parse
        self.species_dict = {'hsa': 9606, 'dme': 7227, 'mmu': 10090, 'rno': 10116}
        self.tax_namespace_dict = {9606: 'HGNC', 10090: 'MGI', 10116: 'RGD', 7227: 'DMEL'}
        self.species_namespace_dict = {k: self.tax_namespace_dict[v] for k, v in self.species_dict.items()}
        self.hgnc = Hgnc(self.client)
        self.bel_rid_cache = {}

    def __len__(self) -> int:
        """Get number of edges in OrientDB."""
        return self.number_of_edges

    def __contains__(self, rs_number: int) -> bool:
        # TODO: To be implemented
        return True

    @staticmethod
    def get_entries(kegg_xml) -> dict:
        """Return all KEGG XML entries."""
        root = ET.fromstring(kegg_xml)
        dict_entry = {}
        for entry in root.iter('entry'):
            attribute = entry.attrib
            if 'link' in attribute:
                dict_entry[attribute['id']] = [attribute['name'].split(' '), attribute['type'], attribute['link']]
            else:
                dict_entry[attribute['id']] = [attribute['name'].split(' '), attribute['type'], 'NA']

        return dict_entry

    @staticmethod
    def get_relations(kegg_xml: str) -> list:
        """Return a list of dictionaries containing information on every KEGG relation.

        Parameters
        ----------
        kegg_xml : str
            A parsed kgml file represented as a string

        Returns
        -------
        relations : list
            List of dictionaries. Each dictionary has information on one KEGG relation in the kgml file
        """
        root = ET.fromstring(kegg_xml)
        relations = []
        for rel in root.iter('relation'):
            relation_dict = dict()
            relation_dict['entry1'] = rel.attrib['entry1']
            relation_dict['entry2'] = rel.attrib['entry2']
            relation_dict['kegg_int_type'] = rel.attrib['type']
            relation_dict['interaction_type'] = [name.attrib['name'] for name in rel.iter('subtype')]
            relations.append(relation_dict)

        return relations

    @staticmethod
    def get_kegg_gene_identifiers(kegg_species_id: str) -> dict:
        """Return a dict of KEGG genes and their IDs."""
        url_kegg_genes = f"http://rest.kegg.jp/list/{kegg_species_id}"
        df_kegg_genes = pd.read_csv(url_kegg_genes,
                                    sep='\t',
                                    names=['kegg_id', 'external_id'],
                                    )
        dict_kegg_genes = df_kegg_genes.groupby('kegg_id')['external_id'].apply(list).to_dict()

        # Split by ',' or ';' and take the first gene name
        for kegg_id, values in dict_kegg_genes.items():
            dict_kegg_genes[kegg_id] = re.split(r'[,;]+', values[0])[0]

        return dict_kegg_genes

    def _get_pathway_kgml(self, pathway: str):
        """Reads KGML pathway file if downloaded, downloads if not there. Returns XML content."""
        kgml_path = os.path.join(self.file_paths['kgml'], pathway)

        if os.path.exists(kgml_path):
            with open(kgml_path, 'r') as kgmlf:
                xml_content = kgmlf.read()

        else:
            url_path = f"http://rest.kegg.jp/get/{pathway}/kgml"
            xml_content = requests.get(url_path).text
            with open(kgml_path, 'w') as kgmlf:
                kgmlf.write(xml_content)

        return xml_content

    def insert_data(self) -> Dict[str, int]:
        """Insert KEGG data into database."""
        dfs = []

        for kegg_species_identifier in tqdm(self.species, desc=f"Import {self.biodb_name.upper()}"):
            # i of enumerate is needed to decide replace (=0) or append (>0)

            dict_kegg_genes = self.get_kegg_gene_identifiers(kegg_species_identifier)
            gene_tag = f"{kegg_species_identifier}:"

            url_pathway_list = f"http://rest.kegg.jp/list/pathway/{kegg_species_identifier}"
            df_pathways = pd.read_csv(url_pathway_list, sep='\t', names=['path_id', 'path_desc'])
            df_pathways[['path_name', 'organism']] = df_pathways.path_desc.str.split(' - ', 1, expand=True)
            df_pathways.path_id = df_pathways.path_id.str.split(':').str[1]
            df_pathways.drop(columns=['path_desc'], inplace=True)

            desc = f"Inserting KEGG data for KEGG species: {kegg_species_identifier}"

            for p in tqdm(df_pathways.to_dict('records'), desc=desc):
                xml_content = self._get_pathway_kgml(p['path_id'])
                dict_entries = self.get_entries(xml_content)
                relations = self.get_relations(xml_content)

                # Currently it only take interactions between proteins/genes. Ignores compounds and links to paths
                generic_table_rows = []
                for relation in relations:
                    entry_a, entry_b = dict_entries[relation['entry1']], dict_entries[relation['entry2']]
                    kegg_int_type = relation['kegg_int_type']
                    interaction_type = relation['interaction_type']

                    # TODO implement compound
                    for kegg_gene_a in entry_a[0]:
                        for kegg_gene_b in entry_b[0]:
                            if gene_tag in kegg_gene_b and gene_tag in kegg_gene_a:
                                gene_symbol_a = dict_kegg_genes.get(kegg_gene_a)
                                gene_symbol_b = dict_kegg_genes.get(kegg_gene_b)
                                if gene_symbol_a and gene_symbol_b:
                                    generic_table_rows.append([kegg_species_identifier, kegg_gene_a, gene_symbol_a,
                                                               kegg_gene_b, gene_symbol_b, interaction_type,
                                                               kegg_int_type, p['path_id'], p['path_name']
                                                               ])

                df = pd.DataFrame(generic_table_rows,
                                  columns=['kegg_species_id', 'kegg_gene_id_a', 'gene_symbol_a',
                                           'kegg_gene_id_b', 'gene_symbol_b', 'interaction_type', 'kegg_int_type',
                                           'pathway_identifier', 'pathway_name'])

                dfs.append(df)

        df_all = pd.concat(dfs)
        df_all.explode('interaction_type').to_sql(kegg.Kegg.__tablename__,
                                                  self.engine,
                                                  if_exists='append',
                                                  index=False)

        return {self.biodb_name: df_all.shape[0]}

    def get_pure_rid(self, class_name, symbol, all_prot_symbol_rid_dict):
        """Get pure protein node rID with the metadata."""
        rid = None
        bel_class_mapper = {'protein': 'p', 'rna': 'r'}
        if symbol in all_prot_symbol_rid_dict:
            rid = all_prot_symbol_rid_dict[symbol]
        else:
            correct_symbol = self.hgnc.get_correct_symbol(symbol)
            if correct_symbol:
                short_bel_function = bel_class_mapper[class_name]
                val_dict = {'name': correct_symbol,
                            'namespace': 'HGNC',
                            'bel': f'{short_bel_function}(HGNC:"{correct_symbol}")',
                            'pure': True}
                rid = self.get_create_rid(class_name, val_dict, check_for='bel')
                all_prot_symbol_rid_dict[correct_symbol] = rid
        return rid

    def get_create_pure_protein(self, namespace: str, name: str) -> str:
        """Create or get pure protein node with the given namespace amd value."""
        bel = f'p({namespace}:"{name}")'
        if bel in self.bel_rid_cache:
            rid = self.bel_rid_cache[bel]
        else:
            value_dict = {'bel': bel, 'pure': True, 'namespace': namespace, 'name': name}
            rid = self.get_create_rid('protein', value_dict=value_dict, check_for='bel')
            self.bel_rid_cache[bel] = rid
        return rid

    def update_interactions(self) -> int:
        """Update edges with KEGG metadata."""
        self.clear_edges()

        symbol_rids_dict = self.get_pure_symbol_rids_dict_in_bel_context()

        inserted = 0

        pmods = {'dephosphorylation': ('pho', 'decreases', BelPmod.PHO),
                 'glycosylation': ('gly', 'increases', BelPmod.GLY),
                 'methylation': ('me0', 'increases', BelPmod.ME0),
                 'phosphorylation': ('pho', 'increases', BelPmod.PHO),
                 'ubiquitination': ('ubi', 'increases', BelPmod.UBI)
                 }
        post_translational_modifications = ','.join([f"'{x}'" for x in pmods.keys()])

        species_ids = ','.join([f"'{x}'" for x in self.species])

        sql_temp = f"""Select
                interaction_type,
                pathway_identifier,
                pathway_name,
                gene_symbol_a,
                gene_symbol_b,
                kegg_species_id
            from
                kegg
            where
                (gene_symbol_a='{{symbol}}' or gene_symbol_a='{{symbol}}') and
                kegg_species_id in ({species_ids}) and
                interaction_type in ({{interaction_types}})
            group by
                interaction_type,
                pathway_identifier,
                pathway_name,
                gene_symbol_a,
                gene_symbol_b,
                kegg_species_id"""

        for symbol, rid in tqdm(symbol_rids_dict.items(), desc="Update KEGG posttranslational modifications"):
            sql = sql_temp.format(symbol=symbol, interaction_types=post_translational_modifications)
            df = pd.read_sql(sql, self.engine)
            by = ['interaction_type', 'gene_symbol_a', 'gene_symbol_b', 'kegg_species_id']

            for key, pathway_names in df.groupby(by=by).apply(lambda x: set(x.pathway_name)).to_dict().items():

                interaction_type, subject_name, object_name, kegg_species_id = key

                namespace = self.species_namespace_dict[kegg_species_id]

                subject_rid = self.get_create_pure_protein(namespace, subject_name)
                object_rid = self.get_create_pure_protein(namespace, object_name)

                ebel_pmod, effect, bel_pmod = pmods[interaction_type]

                pmod_bel = f'p({namespace}:"{object_name}",pmod({bel_pmod}))'
                pmod_value_dict = {'name': object_name, 'namespace': namespace, 'bel': pmod_bel}

                pmod_protein_rid = self.node_exists('protein', pmod_value_dict, check_for='bel')

                if not pmod_protein_rid:
                    pmod_protein_rid = self.get_create_rid('protein', pmod_value_dict, check_for='bel')
                    self.create_edge('has_modified_protein', object_rid, pmod_protein_rid)
                    pmod_rid = self.insert_record('pmod', {'bel': f"pmod({bel_pmod})", 'type': ebel_pmod})
                    self.create_edge('has__pmod', pmod_protein_rid, pmod_rid)

                edge_class = f"{effect}_{ebel_pmod}_kg"
                edge_value_dict = {
                    "interaction_type": interaction_type,
                    "pathway_name": list(pathway_names)
                }
                self.create_edge(edge_class, subject_rid, pmod_protein_rid, edge_value_dict)
                inserted += 1

        self.hgnc.update_bel()

        return inserted
