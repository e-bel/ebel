"""The hub for all things BEL."""
import os
import logging

from tqdm import tqdm
from collections import namedtuple
from typing import Iterable, Union, Set, Dict, Optional
from pyorientdb.exceptions import PyOrientCommandException

from ebel.manager.orientdb.odb_meta import Graph
from ebel.constants import SPECIES_NAMESPACE, RID
from ebel.manager.orientdb.importer import _BelImporter
from ebel.manager.orientdb import odb_meta, odb_structure
from ebel.manager.orientdb.odb_defaults import bel_func_short
from ebel.manager.orientdb.constants import DRUGBANK, EXPRESSION_ATLAS, HGNC, CHEBI, ENSEMBL, GWAS_CATALOG, CLINVAR, \
    UNIPROT, REACTOME, STRINGDB, INTACT, BIOGRID, MIRTARBASE, PATHWAY_COMMONS, DISGENET, KEGG, IUPHAR, NSIDES, \
    CLINICAL_TRIALS, PROTEIN_ATLAS, NCBI

from ebel.manager.orientdb.biodbs.hgnc import Hgnc
from ebel.manager.orientdb.biodbs.kegg import Kegg
from ebel.manager.orientdb.biodbs.ncbi import Ncbi
from ebel.manager.orientdb.biodbs.chebi import Chebi
from ebel.manager.orientdb.biodbs.intact import IntAct
from ebel.manager.orientdb.biodbs.nsides import Nsides
from ebel.manager.orientdb.biodbs.iuphar import Iuphar
from ebel.manager.orientdb.biodbs.clinvar import ClinVar
from ebel.manager.orientdb.biodbs.uniprot import UniProt
from ebel.manager.orientdb.biodbs.biogrid import BioGrid
from ebel.manager.orientdb.biodbs.ensembl import Ensembl
from ebel.manager.orientdb.biodbs.disgenet import DisGeNet
from ebel.manager.orientdb.biodbs.reactome import Reactome
from ebel.manager.orientdb.biodbs.stringdb import StringDb
from ebel.manager.orientdb.biodbs.drugbank import DrugBank
from ebel.manager.orientdb.biodbs.mirtarbase import MirTarBase
from ebel.manager.orientdb.biodbs.gwas_catalog import GwasCatalog
from ebel.manager.orientdb.biodbs.protein_atlas import ProteinAtlas
from ebel.manager.orientdb.biodbs.clinical_trials import ClinicalTrials
from ebel.manager.orientdb.biodbs.pathway_commons import PathwayCommons
from ebel.manager.orientdb.biodbs.expression_atlas import ExpressionAtlas


logger = logging.getLogger(__name__)


class Bel(Graph):
    """Heart and soul of the package, used for interfacing with all of the BioDBs."""

    __hgnc = None
    __uniprot = None
    __drugbank = None
    __gwascatalog = None
    __reactome = None
    __biogrid = None
    __stringdb = None
    __clinical_trials = None
    __intact = None
    __clinvar = None
    __mirtarbase = None
    __expression_atlas = None
    __disgenet = None
    __pathway_commons = None
    __kegg = None
    __ensembl = None
    __iuphar = None
    __chebi = None
    __nsides = None
    __ncbi = None
    __protein_atlas = None

    def __init__(self, graph_config: Optional[dict] = None, overwrite_config: bool = False):
        """Interface for OrientDB database.

        Bel objects allow the user to interact with the different modules in OrientDB and execute queries.

        Parameters
        ----------
        graph_config : Optional[dict]
            If passed, uses the defined parameters for connecting to OrientDB. The dictionary should take the form:
            {
                "user": <ODB username>,
                "password": <ODB password>,
                "db": <ODB database name>,
                "server": <Server ODB is running on (defaults to 'localhost')>,
                "port": <Port ODB is running on (defaults to '2424')
            }
        overwrite_config : bool
            Default False. If True, and graph configuration parameters are passed, overwrites the default values in the
            configuration file with the passed values.
        """
        generics = odb_structure.bel_generics
        nodes = odb_structure.bel_nodes
        edges = odb_structure.bel_edges
        indices = odb_structure.bel_indices
        super().__init__(
            generics,
            nodes,
            edges,
            indices,
            config_params=graph_config,
            overwrite_config=overwrite_config
        )

    @property
    def protein_atlas(self) -> ProteinAtlas:
        """Create an ProteinAtlas object."""
        if not isinstance(self.__protein_atlas, ProteinAtlas):
            self.__protein_atlas = ProteinAtlas()
        return self.__protein_atlas

    @property
    def ncbi(self) -> Ncbi:
        """Create an Ncbi object."""
        if not isinstance(self.__ncbi, Ncbi):
            self.__ncbi = Ncbi()
        return self.__ncbi

    @property
    def disgenet(self) -> DisGeNet:
        """Create an DisGeNet object."""
        if not isinstance(self.__disgenet, DisGeNet):
            self.__disgenet = DisGeNet()
        return self.__disgenet

    @property
    def expression_atlas(self) -> ExpressionAtlas:
        """Create an ExpressionAtlas object."""
        if not isinstance(self.__expression_atlas, ExpressionAtlas):
            self.__expression_atlas = ExpressionAtlas()
        return self.__expression_atlas

    @property
    def mirtarbase(self) -> MirTarBase:
        """Create an MirTarBase object."""
        if not isinstance(self.__mirtarbase, MirTarBase):
            self.__mirtarbase = MirTarBase()
        return self.__mirtarbase

    @property
    def clinvar(self) -> ClinVar:
        """Create an ClinVar object."""
        if not isinstance(self.__clinvar, ClinVar):
            self.__clinvar = ClinVar()
        return self.__clinvar

    @property
    def hgnc(self) -> Hgnc:
        """Create an Hgnc object."""
        if not isinstance(self.__hgnc, Hgnc):
            self.__hgnc = Hgnc()
        return self.__hgnc

    @property
    def uniprot(self) -> UniProt:
        """Create an UniProt object."""
        if not isinstance(self.__uniprot, UniProt):
            self.__uniprot = UniProt()
        return self.__uniprot

    @property
    def drugbank(self) -> DrugBank:
        """Create an DrugBank object."""
        if not isinstance(self.__drugbank, DrugBank):
            self.__drugbank = DrugBank()
        return self.__drugbank

    @property
    def gwas_catalog(self) -> GwasCatalog:
        """Create an GwasCatalog object."""
        if not isinstance(self.__gwascatalog, GwasCatalog):
            self.__gwascatalog = GwasCatalog()
        return self.__gwascatalog

    @property
    def biogrid(self) -> BioGrid:
        """Create an BioGrid object."""
        if not isinstance(self.__biogrid, BioGrid):
            self.__biogrid = BioGrid()
        return self.__biogrid

    @property
    def stringdb(self) -> StringDb:
        """Create an StringDb object."""
        if not isinstance(self.__stringdb, StringDb):
            self.__stringdb = StringDb()
        return self.__stringdb

    @property
    def reactome(self) -> Reactome:
        """Create an Reactome object."""
        if not isinstance(self.__reactome, Reactome):
            self.__reactome = Reactome()
        return self.__reactome

    @property
    def clinical_trials(self) -> ClinicalTrials:
        """Create an ClinicalTrials object."""
        if not isinstance(self.__clinical_trials, ClinicalTrials):
            self.__clinical_trials = ClinicalTrials()
        return self.__clinical_trials

    @property
    def intact(self) -> IntAct:
        """Create an IntAct object."""
        if not isinstance(self.__intact, IntAct):
            self.__intact = IntAct()
        return self.__intact

    @property
    def pathway_commons(self) -> PathwayCommons:
        """Create an PathwayCommons object."""
        if not isinstance(self.__pathway_commons, PathwayCommons):
            self.__pathway_commons = PathwayCommons()
        return self.__pathway_commons

    @property
    def kegg(self) -> Kegg:
        """Create an Kegg object."""
        if not isinstance(self.__kegg, Kegg):
            self.__kegg = Kegg()
        return self.__kegg

    @property
    def ensembl(self) -> Ensembl:
        """Create an Ensembl object."""
        if not isinstance(self.__ensembl, Ensembl):
            self.__ensembl = Ensembl()
        return self.__ensembl

    @property
    def iuphar(self) -> Iuphar:
        """Create an Iuphar object."""
        if not isinstance(self.__iuphar, Iuphar):
            self.__iuphar = Iuphar()
        return self.__iuphar

    @property
    def chebi(self) -> Chebi:
        """Create an Chebi object."""
        if not isinstance(self.__chebi, Chebi):
            self.__chebi = Chebi()
        return self.__chebi

    @property
    def nsides(self) -> Nsides:
        """Create an NSIDES object."""
        if not isinstance(self.__nsides, Nsides):
            self.__nsides = Nsides()
        return self.__nsides

    def import_json(self,
                    input_path: Union[str, Iterable[str]],
                    extend_graph: bool = True,
                    update_from_protein2gene: bool = True,
                    skip_drugbank: bool = False,
                    drugbank_user: str = None,
                    drugbank_password: str = None,
                    include_subfolders: bool = False) -> list:
        """Import BEL JSON file(s) into OrientDB.

        Parameters
        ----------
        input_path: Iterable or str
            A directory containing BEL JSON files, a single BEL JSON file, or a list of JSON files.
        extend_graph: bool (optional)
            If True, enriches the BEL network after importing. Defaults to True.
        update_from_protein2gene: bool (optional)
            Recursively generates RNA nodes and gene nodes for all protein nodes if none exist. Defaults to True.
        include_subfolders: bool
            Boolean flag to indicate whether to traverse subfolders for BEL files.
        skip_drugbank: bool (optional)
            Flag to disable DrugBank update.
        drugbank_user: str (optional)
            DrugBank user name.
        drugbank_password: str (optional)
            DrugBank password.

        Returns
        -------
        list
            List of files imported
        """
        inserted_files = []
        bel_json_ext = ".bel.json"

        if not skip_drugbank:
            self.drugbank.get_user_passwd(drugbank_user=drugbank_user, drugbank_password=drugbank_password)

        # If directory, get a list of all files there
        if isinstance(input_path, str) and os.path.isdir(input_path):
            if include_subfolders:
                files2d = [
                    [os.path.join(root, f) for f in files if f.endswith(bel_json_ext)]
                    for root, dirs, files in os.walk(input_path)
                ]
                input_path = [x for y in files2d for x in y]
            else:
                input_path = [os.path.join(input_path, file) for file in os.listdir(input_path)]

        if isinstance(input_path, str):
            input_path: Iterable[str] = [input_path]

        for path in input_path:
            if os.path.isfile(path) and path.endswith(bel_json_ext):
                logger.info(f"Begin import: {os.path.basename(path)}")

                try:
                    importer = _BelImporter(path, self.client)
                    file_inserted, number_inserted = importer.insert()
                    if file_inserted:
                        logger.info(f"{os.path.basename(path)} successfully imported")
                        inserted_files.append(path)

                except PyOrientCommandException:
                    logger.error(f"{path} failed to be imported", exc_info=True)

        if inserted_files:
            self._create_and_tag_pure()
            self.update_document_info()

            if update_from_protein2gene:
                self._update_from_protein2gene()

            self._update_involved()

            if extend_graph:
                db_skip = [DRUGBANK] if skip_drugbank else []
                self.enrich_network(skip=db_skip)

            self._update_species()
            self._update_involved()

        return inserted_files

    def enrich_network(self,
                       include: Union[str, Iterable[str]] = [],
                       skip: Union[str, Iterable[str]] = []) -> Set[str]:
        """Add all external resources to the network.

        Parameters
        ----------
        include: Iterable[str]
            List of databases to include during network enrichment.
        skip: Iterable[str]
            List of databases to skip during enrichment. If a database appears in both "include" and "skip" then
            the database will be skipped.

        Returns
        -------
        Set[str]
            Set of updated databases.
        """
        updated = set()

        biodb_updaters = {
            HGNC: self.hgnc,
            CHEBI: self.chebi,
            ENSEMBL: self.ensembl,
            GWAS_CATALOG: self.gwas_catalog,
            CLINVAR: self.clinvar,
            UNIPROT: self.uniprot,
            REACTOME: self.reactome,
            STRINGDB: self.stringdb,
            INTACT: self.intact,
            BIOGRID: self.biogrid,
            MIRTARBASE: self.mirtarbase,
            PATHWAY_COMMONS: self.pathway_commons,
            DISGENET: self.disgenet,
            KEGG: self.kegg,
            DRUGBANK: self.drugbank,
            IUPHAR: self.iuphar,
            NSIDES: self.nsides,
            CLINICAL_TRIALS: self.clinical_trials,
            PROTEIN_ATLAS: self.protein_atlas,
            NCBI: self.ncbi,
            EXPRESSION_ATLAS: self.expression_atlas
        }
        # calc all sets (what is used, missing in skip and include)
        include = [] if include == ['[]'] else include  # fixes problems in python3.9/docker
        skip = [] if skip == ['[]'] else skip  # fixes problems in python3.9/docker
        include_set = {include.lower()} if isinstance(include, str) else set([x.lower() for x in include])
        skip_set = {skip.lower()} if isinstance(skip, str) else set([x.lower() for x in skip])
        biodb_set = set([x.lower() for x in biodb_updaters.keys()])
        used_biodb_set = (biodb_set & include_set) if include_set else biodb_set
        used_biodb_set = (used_biodb_set - skip_set) if skip_set else used_biodb_set
        include_not_exists = include_set - biodb_set
        skip_not_exists = skip_set - biodb_set

        logger.info(f"BioDbs for enrichment: {used_biodb_set}")
        if include_not_exists:
            logger.warning(f"{include_not_exists} cannot be included, because they do not exist")
        if skip_not_exists:
            logger.warning(f"{skip_not_exists} cannot be excluded, because they do not exist.")

        # to get the correct order
        db_names = [x for x in biodb_updaters if x in used_biodb_set]

        for db_name in db_names:
            print(f'Enrich network - {db_name.upper()}')
            db: odb_meta.Graph = biodb_updaters[db_name]
            db.update()
            logger.info(f"Enrichment with {db_name} completed.")
            updated.add(db_name)
        self._update_involved()
        return updated

    @property
    def pure_protein_rid_dict(self) -> dict:
        """Get pure protein/rid dictbel. where name is the key and rid is the value."""
        pureprots = self.query_class(class_name='protein', columns=['name'], with_rid=True, pure=True)  # List of dicts
        return {prot['name']: prot[RID] for prot in pureprots}

    def _update_species(self) -> dict:
        """Add species taxon ID to bel nodes."""
        namespaces_updated = {}

        for molec_state in ['protein', 'rna', 'gene']:
            for namespace, species_id in SPECIES_NAMESPACE.items():
                update_pure_bio_sql = f"""UPDATE {molec_state}
                SET species = {species_id}
                WHERE namespace = '{namespace}'"""

                results = self.execute(update_pure_bio_sql)
                namespaces_updated[namespace] = results[0]

        # Update complexes/composites
        results = self.execute("Select @rid.asString() as rid from bel where both('bel_relation').size()>0")
        for r in tqdm(results, desc="Update species"):
            rid = r.oRecordData[RID]
            sql = f"""Select namespace FROM (
                            TRAVERSE out('has__reactants',
                                         'has__products',
                                         'has__protein',
                                         'has__composite',
                                         'has__complex',
                                         'has__gene',
                                         'has__rna') FROM {rid}) WHERE @class in ['protein','rna','gene']"""
            namespace_results = self.execute(sql)
            ns_set = {x.oRecordData['namespace'] for x in namespace_results if namespace_results}

            if len(ns_set) == 1:
                ns = list(ns_set)[0]
                if ns in SPECIES_NAMESPACE.keys():
                    species_sql = f"""UPDATE {rid} SET species = {SPECIES_NAMESPACE[ns]}"""
                    self.execute(species_sql)
                    namespaces_updated[ns] += 1

        return namespaces_updated

    def _update_from_protein2gene(self) -> Dict[str, int]:
        """Adds translated_to and transcribed_to to pure=true proteins and rnas id not exists."""
        added_translated_to = self._add_missing_translated_to_edges()
        added_transcribed_to = self._add_missing_transcribed_to_edges()
        return {'added_translated_to': added_translated_to, 'added_transcribed_to': added_transcribed_to}

    def _create_and_tag_pure(self):
        """Create pure gene, RNA, micro_rna, abundance, complex (as abundance) and protein objects (if not exists).

        Tag all these objects as pure.

        Strategy:
        1. Identify all above mentioned objects with a edges listed below
        2. Check for each object if pure counterpart object exists
        3. If 2=No -> create pure counterpart object
        3. create edge between pure and "modified" objects


        Check for the following modifications (edges):
        out:
        - has__fragment
        - has__variant
        - has__pmod
        - has__location
        in:
        - has_variant
        """
        self._tag_pure()
        self._create_pure_nodes_to_modified()

    def _tag_pure(self) -> int:
        """Tag pure all objects."""
        sql = """Update bio_object set pure = true where
                    @class in ['protein', 'gene', 'rna', 'abundance', 'complex', 'micro_rna'] and
                    outE('has__fragment', 'has__variant', 'has__pmod', 'has__location', 'has__gmod').size() == 0"""
        return len(self.execute(sql))

    def _create_pure_nodes_to_modified(self) -> int:
        """Create all has_modified_(protein|gene) edges in OrientDB (proteins without a pure counterpart)."""
        edge_classes = {'has__pmod': "has_modified_protein",
                        'has__gmod': "has_modified_gene",
                        'has__fragment': "has_fragmented_protein",
                        'has__variant': "has_variant_{}",
                        'has__location': "has_located_{}"}
        results = {}

        sql = """Select
                    out.@rid.asString() as rid,
                    out.@class as class_name,
                    out.name as name,
                    out.namespace as namespace
                from {}"""

        for edge_class in edge_classes:
            results[edge_class] = self.execute(sql.format(edge_class))

        created = 0
        for edge_class, class_name_from_pure in tqdm(edge_classes.items(), desc="Add edges to pure nodes"):
            for row in results[edge_class]:
                r = row.oRecordData

                if r:  # Might return an empty result, but don't know until we look at oRecordData
                    namespace = r['namespace']
                    name = r['name']
                    class_name = r['class_name']

                    if '{}' in class_name_from_pure:
                        cname_from_pure = class_name_from_pure.format(class_name)
                    else:
                        cname_from_pure = class_name_from_pure

                    bel_function = bel_func_short[class_name]
                    bel = f'{bel_function}({namespace}:"{name}")'

                    data = {'namespace': namespace,
                            'name': name,
                            'pure': True,
                            'bel': bel
                            }

                    from_rid = self.get_create_rid(class_name=class_name, value_dict=data, check_for='bel')
                    to_rid = r[RID]

                    self.create_edge(class_name=cname_from_pure,
                                     from_rid=from_rid,
                                     to_rid=to_rid,
                                     if_not_exists=True)
                    created += 1

        return created

    def __update_involved(self, node_class) -> Dict[str, int]:
        """Update involved genes and others."""
        sql_rids = f"""Select @rid.asString() as rid from {node_class}
        where involved_genes is null or involved_other is null"""
        results = self.execute(sql_rids)
        updated_involved_genes = 0
        updated_involved_other = 0

        if results:
            for r in tqdm(results, desc=f"Update node constituents for {node_class}"):
                rid = r.oRecordData[RID]
                sql = f"""Update {rid} set involved_genes =
                    (Select name from (
                        traverse out('has__reactants',
                                     'has__products',
                                     'has__protein',
                                     'has__composite',
                                     'has__complex',
                                     'has__gene',
                                     'has__rna') from {rid}) where @class in ['protein','rna','gene'])"""
                updated_involved_genes += self.execute(sql)[0]

                sql = f"""Update {rid} set involved_other =
                    (Select name from (traverse out('has__abundance',
                         'has__reactants',
                         'has__products',
                         'has__composite',
                         'has__complex') from {rid})
                         where @class not in ['protein','gene','rna']
                         and name is not null)"""
                updated_involved_other += self.execute(sql)[0]
        return {'updated_involved_genes': updated_involved_genes, 'updated_involved_other': updated_involved_other}

    def _update_involved(self) -> Dict[str, int]:
        """Update involved genes and others."""
        result = {'updated_involved_genes': 0, 'updated_involved_other': 0}
        for node_class in ['bel', 'reactants', 'products']:
            sub_result = self.__update_involved(node_class)
            result['updated_involved_genes'] += sub_result['updated_involved_genes']
            result['updated_involved_other'] += sub_result['updated_involved_other']
        return result

    def _add_missing_has_variant_edges(self):
        # TODO: Implement this completely
        ModifiedProtein = namedtuple('ModifiedProtein', ['ns', 'name', 'rids'])
        modified_proteins_sql = """Select
                                    list(@rid.asString()) as rids,
                                    name,
                                    namespace as ns
                                from protein
                                where
                                sum(out('has__fragment').size(),
                                    out('has__variant').size(),
                                    out('has__pmod').size(),
                                    out('has__location').size()
                                ) > 0 and in('has_variant').size() = 0
                                group by name, namespace"""

        results = [r.oRecordData for r in self.execute(modified_proteins_sql)]
        modified_proteins = [ModifiedProtein(r['ns'], r['name'], r['rids']) for r in results]

        for modified_protein in modified_proteins:
            pass

    def _add_missing_translated_to_edges(self) -> int:
        """Add missing RNAs to proteins and translated_to edges."""
        return self.__add_missing_edges(
            from_class='rna',
            to_class='protein',
            edge_name='translated_to',
            bel_function='r')

    def _add_missing_transcribed_to_edges(self) -> int:
        """Add missing genes to RNAs and transcribed_to edges."""
        return self.__add_missing_edges(
            from_class='gene',
            to_class='rna',
            edge_name='transcribed_to',
            bel_function='g')

    def __add_missing_edges(self, from_class, to_class, edge_name, bel_function) -> int:
        added = 0
        sql_temp = """Select
                    @rid.asString(),
                    namespace,
                    name
                 from
                    {to_class}
                 where
                    pure = true and in('{edge_name}').size() = 0"""

        sql = sql_temp.format(to_class=to_class, edge_name=edge_name)

        results = self.execute(sql)

        if results:
            for to_class_node in tqdm(self.execute(sql), desc=f"Adding {edge_name} edges"):
                p = to_class_node.oRecordData
                bel = '{bel_function}({ns}:"{name}")'.format(
                    ns=p['namespace'],
                    name=p['name'],
                    bel_function=bel_function
                )
                from_rid = self.get_create_rid(from_class,
                                               {'namespace': p['namespace'],
                                                'name': p['name'],
                                                'pure': True,
                                                'bel': bel}, check_for='bel')
                self.create_edge(class_name=edge_name, from_rid=from_rid, to_rid=p[RID])
                added += 1

        return added

    def insert_data(self) -> Dict[str, int]:
        """Abstract method."""
        pass

    def update_interactions(self) -> int:
        """Abstract method."""
        pass
