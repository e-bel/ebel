"""NSIDES module."""

import logging
import os
import tarfile
from typing import Dict, Optional

import pandas as pd
from pyorientdb import OrientDB
from tqdm import tqdm

from ebel.constants import RID
from ebel.manager.orientdb import odb_meta, odb_structure, urls
from ebel.manager.orientdb.constants import OFFSIDES, ONSIDES
from ebel.manager.rdbms.models import nsides
from ebel.tools import get_file_path

logger = logging.getLogger(__name__)
pd.options.mode.chained_assignment = None


class Nsides(odb_meta.Graph):
    """Drug side effects and drug-drug interactions were mined from publicly available data.

    Offsides is a database
    of drug side effects that were found, but are not listed on the official FDA label. Twosides is the only
    comprehensive database drug-drug-effect relationships. Over 3,300 drugs and 63,000 combinations connected to
    millions of potential adverse reactions.

    Onsides is a database of adverse reactions and boxed warnings extracted from the FDA structured product labels.
    All labels available to download from DailyMed
    (https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm) as of April 2022 were processed in
    this analysis. In total 2.7 million adverse reactions were extracted from 42,000 labels for just
    under 2,000 drug ingredients or combination of ingredients.

    More information can be found on http://tatonettilab.org/offsides/
    """

    def __init__(self, client: OrientDB = None):
        """Init nSIDES."""
        self.client = client
        self.biodb_name = "nsides"
        self.urls = {OFFSIDES: urls.OFFSIDES, ONSIDES: urls.ONSIDES}
        super().__init__(
            edges=odb_structure.nsides_edges,
            nodes=odb_structure.nsides_nodes,
            tables_base=nsides.Base,
            urls=self.urls,
            biodb_name=self.biodb_name,
        )

    def __len__(self):
        return self.number_of_generics

    def __contains__(self, item):
        # TODO: To be implemented
        return True

    def insert_data(self) -> Dict[str, int]:
        """Insert data in generic OrientDB class.

        Columns:

        drug_rxnorn_id 	integer 	RxNorm CUI (RxCUI) of each drug
        drug_concept_name 	string 	String name of each drug
        condition_meddra_id 	integer 	MedDRA code of each (adverse event) condition
        condition_concept_name 	string 	String name of each condition
        source  string  The database the information was derived from: OFFSIDES or OnSIDES
        A 	integer 	Number of reports prescribed the drug that had the condition
        B 	integer 	Number of reports prescribed the drug that did not have the condition
        C 	integer 	Number of reports not prescribed the drug† that had the condition
        D 	integer 	Number of reports not prescribed the drug† that did not have the condition
        PRR 	float 	Proportional reporting ratio*
        PRR_error 	float 	Proportional reporting ratio error*
        mean_reporting_frequency 	float 	a / (a + b)

        Further documentation see here:
        https://github.com/tatonetti-lab/nsides-release/blob/master/release-notes/v0.1.md
        """
        file_path = get_file_path(self.urls[OFFSIDES], self.biodb_name)
        df = pd.read_csv(file_path, low_memory=False)
        df.drop_duplicates(inplace=True)
        df["source"] = "offsides"
        df.columns = self._standardize_column_names(df.columns)

        df.index += 1
        df.index.rename("id", inplace=True)
        df[pd.to_numeric(df["condition_meddra_id"], errors="coerce").notnull()].to_sql(
            nsides.Nsides.__tablename__,
            self.engine,
            if_exists="append",
            chunksize=100000,
        )
        return {self.biodb_name: df.shape[0]}

    # TODO: Reimplement, but structure have changed
    # def __import_onsides(self) -> Optional[pd.DataFrame]:
    #     """Extract OnSIDES CSV file and format into a DF."""
    #     file_path = get_file_path(self.urls[ONSIDES], self.biodb_name)
    #     file_folder = os.path.dirname(file_path)
    #     tar = tarfile.open(file_path, "r:gz")
    #     folder_in_tar_file = tar.members[0].path
    #     fd = tar.extractfile(f"{folder_in_tar_file}/adverse_reactions.csv.gz")
    #     df = pd.read_csv(fd, compression="gzip", encoding="utf-8")

    #     df.drop(  # Remove columns that aren't needed
    #         [
    #             "xml_id",
    #             "Unnamed: 10",
    #             "omop_concept_id",
    #             "drug_concept_ids",
    #             "concept_class_id",
    #         ],
    #         inplace=True,
    #         axis=1,
    #     )

    #     df.rename(
    #         columns={  # Rename columns to match OFFSIDES
    #             "rxnorm_ids": "drug_rxnorn_id",
    #             "pt_meddra_term": "condition_concept_name",
    #             "pt_meddra_id": "condition_meddra_id",
    #             "ingredients_names": "drug_concept_name",
    #         },
    #         inplace=True,
    #     )

    #     # Keep rows with only 1 ingredient/drug
    #     single_value_mask = df["drug_concept_name"].apply(
    #         lambda x: len(x.split(",")) == 1
    #     )
    #     pruned_df = df.loc[single_value_mask]
    #     pruned_df["source"] = "onsides"
    #     return pruned_df

    def update_bel(self) -> int:
        """Create has_side_effect edges between drugs (drugbank) and side_effects.

        RxCUI (https://rxnav.nlm.nih.gov/RxNormAPIs.html#) is used as the mapping identifier.
        """
        self.clear_edges()
        self.delete_nodes_with_no_edges("side_effect")
        self.delete_nodes_with_no_edges("drug")

        # TODO: Translate to sqlalchemy query
        sql_temp = """Select
            o.condition_meddra_id,
            o.condition_concept_name,
            o.prr,
            o.mean_reporting_frequency
        from
            drugbank as d inner join
            drugbank_external_identifier as dei on (d.id=dei.drugbank_id) inner join
            nsides as o on (dei.identifier=o.drug_rxnorn_id)
        where
            d.drugbank_id='{}' and resource='RxCUI'
            and (mean_reporting_frequency>=0.01 OR mean_reporting_frequency is NULL)
        group by
            o.condition_meddra_id,
            o.condition_concept_name,
            o.prr,
            o.mean_reporting_frequency
        """

        drugbank_ids = self.query_class("drug", columns=["drugbank_id"], drugbank_id="notnull")
        drugbank_id_rids = {d["drugbank_id"]: d[RID] for d in drugbank_ids}

        side_effects = self.query_class("side_effect", columns=["condition_meddra_id"])
        side_effect_rids = {d["condition_meddra_id"]: d[RID] for d in side_effects}

        updated = 0

        for drugbank_id, drugbank_rid in tqdm(drugbank_id_rids.items(), desc=f"Update {self.biodb_name.upper()}"):
            for r in self.engine.execute(sql_temp.format(drugbank_id)):
                (
                    condition_meddra_id,
                    condition_concept_name,
                    prr,
                    mean_reporting_frequency,
                ) = r

                if condition_meddra_id not in side_effect_rids:
                    side_effect_rid = self.insert_record(
                        "side_effect",
                        {
                            "label": condition_concept_name,
                            "condition_meddra_id": condition_meddra_id,
                        },
                    )
                    side_effect_rids[condition_meddra_id] = side_effect_rid

                value_dict = {
                    "prr": prr,
                    "mean_reporting_frequency": mean_reporting_frequency,
                }
                side_effect_rid = side_effect_rids[condition_meddra_id]
                self.create_edge(
                    class_name="has_side_effect",
                    from_rid=drugbank_rid,
                    to_rid=side_effect_rid,
                    value_dict=value_dict,
                )
                updated += 1
        return updated

    def update_interactions(self) -> int:
        """Update edges with NSIDES metadata."""
        # not implemented because update_bel is implemented
        pass
