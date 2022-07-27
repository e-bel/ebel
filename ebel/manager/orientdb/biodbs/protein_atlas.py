"""Protein Atlas module."""
import pandas as pd

from pyorientdb import OrientDB
from typing import Dict, Optional

from ebel.tools import get_file_path
from ebel.manager.orientdb import odb_meta, urls
from ebel.manager.orientdb.constants import PROTEIN_ATLAS

from ebel.manager.rdbms.models import protein_atlas
from tqdm import tqdm


class ProteinAtlas(odb_meta.Graph):
    """Protein Atlas (https://www.proteinatlas.org/about/download)."""

    def __init__(self, client: OrientDB = None):
        """Init ProteinAtlas."""
        self.client = client
        self.biodb_name = PROTEIN_ATLAS
        self.urls = {
            protein_atlas.ProteinAtlasNormalTissue.__tablename__: urls.PROTEIN_ATLAS_NORMAL_TISSUE,
            protein_atlas.ProteinAtlasSubcellularLocation.__tablename__: urls.PROTEIN_ATLAS_SUBCELLULAR_LOCATIO,
            protein_atlas.ProteinAtlasRnaTissueConsensus.__tablename__: urls.PROTEIN_ATLAS_RNA_CONSENSUS,
            protein_atlas.ProteinAtlasRnaBrainGtex.__tablename__: urls.PROTEIN_ATLAS_RNA_GTEX_BRAIN,
            protein_atlas.ProteinAtlasRnaBrainFantom.__tablename__: urls.PROTEIN_ATLAS_RNA_FANTOM_BRAIN,
            protein_atlas.ProteinAtlasRnaMouseBrainAllen.__tablename__: urls.PROTEIN_ATLAS_RNA_MOUSE_BRAIN_ALLEN,
        }
        super().__init__(urls=self.urls,
                         tables_base=protein_atlas.Base,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.session.query(protein_atlas.ProteinAtlasNormalTissue).count()

    def __contains__(self, ensembl_id) -> bool:
        count = self.session.query(protein_atlas.ProteinAtlasNormalTissue).filter(
            protein_atlas.ProteinAtlasNormalTissue.gene == ensembl_id).count()
        return bool(count)

    def insert_data(self) -> Dict[str, int]:
        """Insert NCBI gene data.

        :return Dict[str, int]: Inserted metadata.
        """
        self.recreate_tables()
        inserts = dict()
        inserts[protein_atlas.ProteinAtlasNormalTissue.__tablename__] = self._insert_normal_tissue()
        inserts[protein_atlas.ProteinAtlasSubcellularLocation.__tablename__] = self._insert_subcellular_location()
        inserts[protein_atlas.ProteinAtlasRnaTissueConsensus.__tablename__] = self._insert_rna_tissue_consensus()
        inserts[protein_atlas.ProteinAtlasRnaBrainGtex.__tablename__] = self._insert_rna_brain_gtex()
        inserts[protein_atlas.ProteinAtlasRnaBrainFantom.__tablename__] = self._insert_rna_brain_fantom()
        inserts[protein_atlas.ProteinAtlasRnaMouseBrainAllen.__tablename__] = self._insert_rna_mouse_brain_allen()
        return inserts

    def __insert_table(self, model, use_cols=None, sep: str = "\t", chunksize: Optional[int] = None) -> int:
        """Generic method to insert data.

        :param model: NCBI SQLAlchemy model
        :param use_cols: Column names to be used in file
        :param sep: Column separator
        :return int: Number of inserts.
        """
        table = model.__tablename__
        file_path = get_file_path(self.urls[table], self.biodb_name)
        dfs = pd.read_csv(file_path, sep=sep, usecols=use_cols, chunksize=chunksize)
        if chunksize is None:
            dfs = [dfs]

        number_of_inserts = 0

        for df in dfs:
            self._standardize_dataframe(df)
            df.index += 1
            df.index.rename('id', inplace=True)
            df.to_sql(table, self.engine, if_exists="append")
            number_of_inserts += df.shape[0]

        return number_of_inserts

    def _insert_normal_tissue(self) -> int:
        """Insert normal tissue.

        :return int: Number of inserts
        """
        return self.__insert_table(protein_atlas.ProteinAtlasNormalTissue)

    def _insert_subcellular_location(self) -> int:
        """Insert subcellular location.

        :return int: Number of inserts
        """
        return self.__insert_table(protein_atlas.ProteinAtlasSubcellularLocation)

    def _insert_rna_tissue_consensus(self) -> int:
        """Insert RNA tissue consensus.

        :return int: Number of inserts
        """
        return self.__insert_table(protein_atlas.ProteinAtlasRnaTissueConsensus)

    def _insert_rna_brain_gtex(self) -> int:
        """Insert RNA brain GTEx.

        :return int: Number of inserts
        """
        return self.__insert_table(protein_atlas.ProteinAtlasRnaBrainGtex)

    def _insert_rna_brain_fantom(self) -> int:
        """Insert RNA brain Fantom.

        :return int: Number of inserts
        """
        return self.__insert_table(protein_atlas.ProteinAtlasRnaBrainFantom)

    def _insert_rna_mouse_brain_allen(self) -> int:
        """Insert RNA mouse brain Allen.

        :return int: Number of inserts
        """
        return self.__insert_table(protein_atlas.ProteinAtlasRnaMouseBrainAllen)

    def get_tissues_by_ensembl_id(self, ensembl_gene_id):
        """Return tissues for a given ensembl ID."""
        level_exixs = protein_atlas.ProteinAtlasNormalTissue.level.in_(['Medium', 'High', 'Low'])
        columns = (
            protein_atlas.ProteinAtlasNormalTissue.tissue,
            protein_atlas.ProteinAtlasNormalTissue.cell_type,
            protein_atlas.ProteinAtlasNormalTissue.level
        )
        data = [x for x in self.session.query(*columns).filter(level_exixs).filter_by(gene=ensembl_gene_id,
                                                                                      reliability='Approved')]
        tissues = {}
        for d in data:
            if d.tissue not in tissues:
                tissues[d.tissue] = {d.level: [d.cell_type]}
            else:
                if d.level not in tissues[d.tissue]:
                    tissues[d.tissue][d.level] = [d.cell_type]
                else:
                    tissues[d.tissue][d.level].append(d.cell_type)
        return tissues

    def update_interactions(self) -> int:
        """Update edges with Protein Atlas metadata (human)."""
        # TODO: implement also for other species
        match = """Select
                @rid.asString() as rid,
                hgnc.@rid.asString() as hgnc_id,
                hgnc.ensembl_gene_id as ensembl_gene_id,
                namespace,
                name,
                uniprot,
                label
            from protein
            where
                pure=true and
                namespace='HGNC' and
                both('bel_relation').size()>=1 and
                hgnc.ensembl_gene_id IS NOT NULL"""

        rid_ensembl_gene_ids = {x.oRecordData['ensembl_gene_id']: x for x in self.execute(match)}

        self.execute("Delete EDGE has_located_protein where levels IS NOT NULL")

        location_rid_cache = {x['bel']: x['rid'] for x in self.query_class('location', columns=['bel'])}

        for ensembl_gene_id, data in tqdm(rid_ensembl_gene_ids.items()):
            ns_location = "PROTEIN_ATLAS"
            pure_protein = data.oRecordData
            ns = pure_protein['namespace']
            name = pure_protein['name']

            value_dict = {'namespace': ns,
                          'name': name,
                          'hgnc': pure_protein['hgnc_id'],
                          'involved_genes': [pure_protein['name']],
                          'involved_other': [],
                          'species': 9606,
                          'uniprot': pure_protein.get('uniprot'),
                          'label': pure_protein.get('label')}

            tissues = self.get_tissues_by_ensembl_id(ensembl_gene_id)

            for tissue, levels in tissues.items():
                value_dict_located = value_dict.copy()
                location_bel = f'loc({ns_location}:"{tissue}")'
                bel = f'p({ns}:"{name}",{location_bel})'
                value_dict_located.update(bel=bel)
                protein_located_rid = self.get_create_rid(
                    class_name='protein',
                    value_dict=value_dict_located,
                    check_for='bel'
                )

                self.create_edge(class_name='has_located_protein',
                                 from_rid=pure_protein['rid'],
                                 to_rid=protein_located_rid,
                                 value_dict={'levels': levels})

                if location_bel in location_rid_cache:
                    location_rid = location_rid_cache[location_bel]
                else:
                    location_rid = self.get_create_rid(class_name='location',
                                                       value_dict={
                                                           'namespace': ns_location,
                                                           'name': tissue,
                                                           'bel': location_bel
                                                       },
                                                       check_for='bel')
                    location_rid_cache[location_bel] = location_rid

                self.create_edge("has__location", from_rid=protein_located_rid, to_rid=location_rid)
