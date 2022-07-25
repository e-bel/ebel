"""Ensembl."""
import re
import gzip
import pandas as pd

from typing import Dict
from pyorientdb import OrientDB

from ebel.tools import get_file_path
from ebel.manager.orientdb import odb_meta, urls
from ebel.manager.orientdb.constants import ENSEMBL

from ebel.manager.rdbms.models import ensembl

# TODO: use ftp://ftp.ensembl.org/pub/release-102/mysql/homo_sapiens_core_102_38/gene.txt.gz instead CDs


class Ensembl(odb_meta.Graph):
    """Ensembl (https://www.ensembl.org/index.html)."""

    def __init__(self, client: OrientDB = None):
        """Init Ensembl."""
        self.client = client
        self.biodb_name = ENSEMBL
        self.urls = {self.biodb_name: urls.ENSEMBL_CDS}
        super().__init__(urls=self.urls,
                         tables_base=ensembl.Base,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.session.query(ensembl.Ensembl).count()

    def __contains__(self, ensembl_id) -> bool:
        count = self.session.query(ensembl.Ensembl).filter(ensembl.Ensembl.gene_id_short == ensembl_id).count()
        return bool(count)

    def insert_data(self) -> Dict[str, int]:
        """Insert Ensembl data."""
        data = []
        file_path = get_file_path(self.urls[self.biodb_name], self.biodb_name)
        with gzip.open(file_path, "r") as f:
            lines = [x.decode("utf-8").strip() for x in f.readlines() if x.startswith(b">")]

        regex = (r"^>(?P<enst>ENST\d+)\.\d+ cds chromosome:GRCh"
                 r"(?P<version>\d+):"
                 r"(?P<chromosome>((1|2)?\d|X|Y|MT)):"
                 r"(?P<start>\d+):"
                 r"(?P<stop>\d+):"
                 r"(?P<orientation>-?1) gene:"
                 r"(?P<gene_id>(?P<gene_id_short>ENSG\d+)\.\d+) "
                 r"gene_biotype:protein_coding transcript_biotype:protein_coding gene_symbol:"
                 r"(?P<symbol>\S+) .*? \[Source:HGNC Symbol;Acc:"
                 r"(?P<hgnc_id>HGNC:\d+)\]")
        pattern = re.compile(regex)
        for line in lines:
            found = pattern.search(line)
            if found:
                data += [found.groupdict()]

        df = pd.DataFrame(data)
        df.index += 1
        df.index.rename('id', inplace=True)
        df.to_sql(ensembl.Ensembl.__tablename__, self.engine, if_exists='append')

        self.session.commit()

        return {self.biodb_name: df.shape[0]}

    def update_interactions(self) -> int:
        """Update edges with EnsEMBL metadata."""
        pass
