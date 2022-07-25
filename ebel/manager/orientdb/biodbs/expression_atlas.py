"""Expression Atlas."""
import logging
import os
import sys
from collections import OrderedDict
from typing import List, Tuple, Optional

import pandas as pd
from pandas.core.frame import DataFrame
import xmltodict
from pyorientdb import OrientDB
from tqdm import tqdm

from ebel.constants import DATA_DIR
from ebel.manager.orientdb import odb_meta, urls
from ebel.manager.rdbms.models import expression_atlas
from ebel.tools import get_standard_name

logger = logging.getLogger(__name__)


class ExpressionAtlas(odb_meta.Graph):
    """ExpressionAtlas."""

    def __init__(self, client: OrientDB = None):
        """Init ExpressionAtlas."""
        self.client = client
        self.biodb_name = 'expression_atlas'
        self.urls = {'latest_data': urls.EXPRESSION_ATLAS_EXPERIMENTS}
        self.data_dir = os.path.join(DATA_DIR, self.biodb_name)

        super().__init__(tables_base=expression_atlas.Base,
                         urls=self.urls,
                         biodb_name=self.biodb_name)

    def __len__(self):
        return self.number_of_generics

    def __contains__(self, item):
        # TODO: To be implemented
        return True

    def update(self):
        """Update ExpressionAtlas."""
        logger.info("Update ExpressionAtlas")
        downloaded = self.download()
        if downloaded['latest_data']:
            self.extract_files()
            self.insert()

    def extract_files(self):
        """Extract relevant files."""
        os.chdir(self.data_dir)
        cmd_temp = "tar -xzf atlas-latest-data.tar.gz --wildcards --no-anchored '{}'"
        patterns = ['*.sdrf.txt',
                    '*.condensed-sdrf.tsv',
                    '*analytics.tsv',
                    '*-configuration.xml',
                    '*.idf.txt',
                    '*.go.gsea.tsv',
                    '*.interpro.gsea.tsv',
                    '*.reactome.gsea.tsv'
                    ]
        with tqdm(patterns) as t_patterns:
            for pattern in t_patterns:
                t_patterns.set_description(f"Extract files with pattern {pattern}")
                command = cmd_temp.format(pattern)
                os.system(command)

    def insert_data(self):
        """Class method."""
        pass

    def update_interactions(self) -> int:
        """Class method."""
        pass

    def insert_experiment(self, experiment_name: str, title: str) -> int:
        """Insert individual experiment into SQL database.

        Parameters
        ----------
        experiment_name : str
            Name of the Expression Atlas experiment.
        title : str
            Title of experiment.

        Returns
        -------
        Table ID of newly inserted experiment.
        """
        experiment = expression_atlas.Experiment(name=experiment_name, title=title)
        self.session.add(experiment)
        self.session.flush()
        self.session.commit()
        return experiment.id

    def insert(self):
        """Override insert method for SQL data insertion."""
        self.recreate_tables()
        data_folder = os.scandir(self.data_dir)
        for experiment_name in tqdm([(f.name) for f in data_folder if f.is_dir()]):
            try:
                df_configuration = self.get_configuration(experiment_name)
                if isinstance(df_configuration, pd.DataFrame):
                    df_idf = self.get_idf(experiment_name)
                    title = df_idf[df_idf.key_name == 'investigation_title'].value.values[0]

                    experiment_id = self.insert_experiment(experiment_name, title)

                    groups_strs: Tuple[str, ...] = self.__insert_configuration(df_configuration, experiment_id)

                    self.__insert_idf(df_idf, experiment_id)
                    self.__insert_sdrf_condensed(experiment_id, experiment_name)
                    self.__insert_foldchange(experiment_id, experiment_name, groups_strs)
                    self.insert_gseas(experiment_id, experiment_name, groups_strs)

            except Exception as e:
                print(experiment_name)
                print(e)
                sys.exit()

    def __insert_foldchange(self, experiment_id: int, experiment_name: str, groups_strs: Tuple[str, ...]):
        df_log2foldchange = self.get_log2foldchange(experiment_name, groups_strs).set_index('group_comparison')
        df_group_comparison = self.get_df_group_comparison(experiment_id, groups_strs).set_index('group_comparison')
        df_log2foldchange.join(df_group_comparison).to_sql(expression_atlas.FoldChange.__tablename__,
                                                           self.engine, if_exists='append', index=False)

    def get_df_group_comparison(self, experiment_id: int, groups_strs: Tuple[str, ...]) -> pd.DataFrame:
        """Get group comparison IDs and group comparison columns for pairs of group strings.

        Parameters
        ----------
        experiment_id : int
            Experiment numerical ID.
        groups_strs : tuple
            Pairs of gene symbols.

        Returns
        -------
        Pandas DataFrame of 'group_comparison_id' and 'group_comparison'.
        """
        data = []
        for groups_str in groups_strs:
            group_comparison_id = self.session.query(expression_atlas.GroupComparison.id).filter_by(
                experiment_id=experiment_id,
                group_comparison=groups_str).first().id
            data.append((group_comparison_id, groups_str))
        return pd.DataFrame(data, columns=['group_comparison_id', 'group_comparison'])

    def __insert_configuration(self, df_configuration, experiment_id: int) -> Tuple[str, ...]:
        df_configuration['experiment_id'] = experiment_id
        df_configuration.to_sql(expression_atlas.GroupComparison.__tablename__, self.engine, if_exists='append',
                                index=False)
        groups_strs = tuple(df_configuration.group_comparison.values)
        self.session.flush()
        self.session.commit()
        return groups_strs

    def __insert_idf(self, df_idf: DataFrame, experiment_id: int):
        df_idf['experiment_id'] = experiment_id
        df_idf.to_sql(expression_atlas.Idf.__tablename__, self.engine, if_exists='append', index=False)

    def __insert_sdrf_condensed(self, experiment_id: int, experiment_name: str):
        df = self.get_sdrf_condensed(experiment_name)
        # organisms = tuple(df[df.parameter == 'organism'].value.unique())
        df['experiment_id'] = experiment_id
        df.drop(columns=['experiment'], inplace=True)
        df.to_sql(expression_atlas.SdrfCondensed.__tablename__, self.engine, if_exists='append', index=False)

    def insert_gseas(self, experiment_id: int, experiment_name: str, groups_strs: Tuple[str, ...]):
        """Insert Gene set enrichment analysis.

        For more information about parameters see https://www.bioconductor.org/packages/release/bioc/html/piano.html

        Args:
            experiment_id (int): [description]
            experiment_name (str): [description]
            groups_strs (Tuple[str, ...]): [description]
        """
        df = self.get_gseas(experiment_name, experiment_id, groups_strs)
        if isinstance(df, pd.DataFrame):
            df.to_sql(expression_atlas.Gsea.__tablename__, self.engine, if_exists='append', index=False)

    def get_gseas(self, experiment_name: str, experiment_id: int, groups_strs: Tuple[str]) -> Optional[pd.DataFrame]:
        """Get GSEA data.

        Parameters
        ----------
        experiment_name : str
            Name of the Expression Atlas experiment.
        experiment_id : int
            Experiment numerical ID.
        groups_strs : tuple
            Pairs of gene symbols.

        Returns
        -------
        If GSEA informaiton is found, returns a pandas DataFrame detailing the GSEAs associated with an experiment.
        """
        dfs = []
        for groups_str in groups_strs:
            for gsea_type in ['go', 'reactome', 'interpro']:
                df = self.get_gsea(experiment_name, groups_str, gsea_type)
                if isinstance(df, pd.DataFrame):
                    df['gsea_type'] = gsea_type
                    df['group_comparison_id'] = self.__get_group_comparison_id(groups_str, experiment_id)
                    dfs.append(df[df.p_adj_non_dir <= 0.05])
        if dfs:
            return pd.concat(dfs)

    def __get_group_comparison_id(self, groups_str: str, experiment_id: int):
        query = self.session.query(expression_atlas.GroupComparison.id)
        return query.filter_by(group_comparison=groups_str, experiment_id=experiment_id).first().id

    def get_gsea(self, experiment_name: str, groups_str: str, gsea_type: str) -> Optional[pd.DataFrame]:
        """Generate a table of GSEA information for a pair of symbols for a given experiment.

        Parameters
        ----------
        experiment_name : str
            Name of the Expression Atlas experiment.
        groups_str : tuple
            Pairs of gene symbol strings.
        gsea_type : str
            Type of GSEA.

        Returns
        -------
        Returns a pandas DataFrame of GSEA information if file exists matching the passed parameters.
        """
        file_path = os.path.join(self.data_dir,
                                 experiment_name,
                                 f"{experiment_name}.{groups_str}.{gsea_type}.gsea.tsv")

        if not os.path.exists(file_path):
            return

        df = pd.read_csv(file_path, sep="\t")
        df.columns = [get_standard_name(x) for x in df.columns]

        if 'term' in df.columns:
            return df

    def get_log2foldchange(self, experiment_name: str, groups_strs: Tuple[str]) -> pd.DataFrame:
        """Generate a table of log2 fold changes between pairs of gene symbols.

        Parameters
        ----------
        experiment_name : str
            Name of the Expression Atlas experiment.
        groups_strs : tuple
            Pairs of gene symbol strings.

        Returns
        -------
        pandas DataFrame.
        """
        dfs = []
        df_analyticss = self.get_analyticss(experiment_name)
        for df_analytics in df_analyticss:
            for g in groups_strs:
                col_p_value = f'{g}_p_value'
                col_log2foldchange = f'{g}_log2foldchange'
                if {col_p_value, col_log2foldchange}.issubset(df_analytics.columns):
                    cols = ['gene_id', 'gene_name', col_p_value, col_log2foldchange]
                    rename_map = {col_p_value: 'p_value', col_log2foldchange: 'log2foldchange'}

                    if f'{g}_t_statistic' in df_analytics.columns:
                        cols.append(f'{g}_t_statistic')
                        rename_map[f'{g}_t_statistic'] = 't_statistic'

                    df = df_analytics[cols].rename(columns=rename_map)
                    df['group_comparison'] = g
                    dfs.append(df)
        df_concat = pd.concat(dfs)
        return df_concat[(df_concat.p_value <= 0.05)
                         & df_concat.gene_name.notnull()
                         & ((df_concat.log2foldchange <= -1) | (df_concat.log2foldchange >= 1))]

    def get_idf(self, experiment_name: str) -> Optional[pd.DataFrame]:
        """Get Data from IDF by experiment name.

        Parameters
        ----------
        experiment_name : str
            Name of the Expression Atlas experiment.

        Returns
        -------
        DataFrame with IDF values.
        """
        file_path = os.path.join(self.data_dir, experiment_name, f"{experiment_name}.idf.txt")

        if not os.path.exists(file_path):
            return

        rows = []

        for line in open(file_path):
            line_splitted = line.strip().split('\t')

            if len(line_splitted) > 1:
                key_name = get_standard_name(line_splitted[0])
                values = [x.strip() for x in line_splitted[1:] if x.strip()]
                rows.append((key_name, values))

        df = pd.DataFrame(rows, columns=('key_name', 'value')).explode('value')
        return df

    def get_sdrf_condensed(self, experiment_name: str) -> Optional[pd.DataFrame]:
        """Generate a condensed version of an experiment's SDRF.

        Parameters
        ----------
        experiment_name : str
            Name of the Expression Atlas experiment.

        Returns
        -------
        pandas DataFrame.
        """
        file_path = os.path.join(self.data_dir, experiment_name, f"{experiment_name}.condensed-sdrf.tsv")

        if not os.path.exists(file_path):
            return

        names = ['experiment', 'method', 'sample', 'parameter_type', 'parameter', 'value', 'url']
        df = pd.read_csv(file_path, sep="\t", header=None, names=names)
        return df

    def get_analyticss(self, experiment_name: str) -> List[pd.DataFrame]:
        """Return list of pandas dataframes detailing specific statistics about a given experiment.

        Parameters
        ----------
        experiment_name : str
            Name of the Expression Atlas experiment.

        Returns
        -------
        List of pandas DataFrames.
        """
        files = os.scandir(os.path.join(self.data_dir, experiment_name))
        analytics_tsv_paths = [f.path for f in files if f.name.endswith("-analytics.tsv")]
        dfs = []
        if analytics_tsv_paths:
            for analytics_tsv_path in analytics_tsv_paths:
                df = pd.read_csv(analytics_tsv_path, sep='\t')
                df.columns = [get_standard_name(x) for x in df.columns]
                dfs.append(df)
        return dfs

    def get_configuration(self, experiment_name: str) -> Optional[DataFrame]:
        """Return pandas dataframe of experiment configuration.

        Parameters
        ----------
        experiment_name : str
            Name of the Expression Atlas experiment.

        Returns
        -------
        pandas DataFrame.
        """
        file_path = os.path.join(self.data_dir, experiment_name, f"{experiment_name}-configuration.xml")

        if not os.path.exists(file_path):
            return

        config = xmltodict.parse(open(file_path).read())['configuration']

        if config['@experimentType'] != 'rnaseq_mrna_baseline':

            compare_dict = {}
            ca = config['analytics']
            ca_items = ca if isinstance(ca, list) else [ca]

            for item in ca_items:
                for _, contrast in item['contrasts'].items():
                    if isinstance(contrast, (OrderedDict, list)):
                        contrasts = contrast if isinstance(contrast, list) else [contrast]
                        for ind_contrast in contrasts:
                            compare_dict[ind_contrast['@id']] = ind_contrast['name']

            return pd.DataFrame(compare_dict.items(), columns=['group_comparison', 'name'])
