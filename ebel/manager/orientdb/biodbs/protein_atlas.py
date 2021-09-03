"""Protein Atlas module."""
import pandas as pd

from pyorient import OrientDB
from typing import Dict, Optional

from ebel.tools import get_file_path
from ebel.manager.orientdb import odb_meta, urls
from ebel.manager.orientdb.constants import PROTEIN_ATLAS

from ebel.manager.rdbms.models import protein_atlas


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

    def update_interactions(self) -> int:
        """Update edges with Protein Atlas metadata."""
        pass
