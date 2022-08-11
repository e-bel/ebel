"""OrientDB structure.

All vertex, edge and index definitions have to follow the following conversion:

prefix: Used in the hole package for domains like BEL, HGNC, UniProt, ...
typeOfClass or Index
"""
from copy import deepcopy
from enum import Enum
from typing import List, Dict, Optional, Tuple

from ebel.manager.orientdb.odb_defaults import OIndexType, ODataType, normalized_pmod


class OClassType(Enum):
    """Class for constants definitions."""

    NODE = 'VERTEX'
    EDGE = 'EDGE'
    GENERIC = 'GENERIC'


class OProperty(object):
    """Generic class definition for creating properties in the OrientDB database."""

    def __init__(self,
                 prop_name: str,
                 data_type: ODataType,
                 linked_class: Optional[str] = None,
                 linked_type: Optional[ODataType] = None,
                 mandatory: bool = False,
                 node_view_label=False,
                 node_view_sub_label=False):
        """Init method."""
        self.prop_name = prop_name
        self.data_type = data_type
        self.linked_type = linked_type
        self.linked_class = linked_class
        self.mandatory = mandatory
        self.node_view_label = node_view_label
        self.node_view_sub_label = node_view_sub_label


class OClass(object):
    """Generic class definition for creating classes in the OrientDB database."""

    def __init__(self,
                 name: str,
                 extends: Tuple[str, ...],
                 abstract: bool,
                 props: Tuple[OProperty, ...],
                 own_class: bool,
                 class_type: OClassType):
        """Init method."""
        self.class_type = class_type
        self.name = name
        self.extends = extends
        self.abstract = abstract
        self.props = list(props)
        self.own_class = own_class

    def add_properties(self, props: List[OProperty]):
        """Add properties to the class."""
        for prop in props:
            self.props.append(prop)
        return self

    def is_edge(self):
        """Check whether class is an edge."""
        return self.class_type == OClassType.EDGE

    def is_node(self):
        """Check whether class is a vertex/node."""
        return self.class_type == OClassType.NODE

    def is_vertex(self):
        """Check whether class is a vertex. Returns "is_node" method and created for convenience."""
        return self.is_node()

    def is_generic(self):
        """Check whether class is generic."""
        return self.class_type == OClassType.GENERIC


class Node(OClass):
    """Generic class definition for creating node classes in the OrientDB database."""

    def __init__(self,
                 name: str,
                 extends: Tuple[OClass, ...] = (),
                 abstract: bool = False,
                 props: Tuple[OProperty, ...] = (),
                 own_class: bool = True):
        """Init method for Node ODB class."""
        extends = tuple(x.name for x in extends)
        OClass.__init__(self, name, extends, abstract, props, own_class, class_type=OClassType.NODE)


class Edge(OClass):
    """Generic class definition for creating edge classes in the OrientDB database."""

    def __init__(self,
                 name: str,
                 extends: Tuple[OClass, ...] = (),
                 abstract: bool = False,
                 props: Tuple[OProperty, ...] = (),
                 own_class: bool = True,
                 in_out: Tuple[Optional[OClass], Optional[OClass]] = (None, None)):
        """Init method for Edge ODB class."""
        extends = tuple(x.name for x in extends)
        in_ = in_out[0].name if in_out[0] else None
        out = in_out[1].name if in_out[1] else None
        OClass.__init__(self, name, extends, abstract, props, own_class, class_type=OClassType.EDGE)
        self.in_out = (in_, out)


class Generic(OClass):
    """Generic class definition for creating generic classes in the OrientDB database."""

    def __init__(self,
                 name: str,
                 extends: Tuple[str, ...] = (),
                 abstract: bool = False,
                 props: Tuple[OProperty, ...] = (),
                 own_class: bool = True):
        """Init method for Generic ODB class."""
        OClass.__init__(self, name, extends, abstract, props, own_class, class_type=OClassType.GENERIC)


class OIndex(object):
    """Generic class definition for creating indices in the OrientDB database."""

    def __init__(self, odb_class: OClass, columns: Tuple[str, ...], index_type: OIndexType):
        """Init method."""
        self.class_name = odb_class.name
        self.columns = columns
        self.index_type = index_type


basic_node = Node(name='V')
basic_edge = Edge(name='E')

##############################################################################
# Definition of BEL vertices, edges and indices
##############################################################################
bel_document = Generic('bel_document', props=(
    OProperty('name', ODataType.STRING),
    OProperty('date_uploaded', ODataType.DATETIME),
    OProperty('description', ODataType.STRING),
    OProperty('version', ODataType.STRING),
    OProperty('authors', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('contact_info', ODataType.STRING),
    OProperty('copyright', ODataType.STRING),
    OProperty('licences', ODataType.STRING),
    OProperty('git', ODataType.EMBEDDEDMAP),
    OProperty('namespaces', ODataType.EMBEDDEDMAP),
    OProperty('annotations', ODataType.EMBEDDEDMAP),
    OProperty('file', ODataType.EMBEDDEDMAP),
    OProperty('git_info', ODataType.EMBEDDEDMAP),
    OProperty('keywords', ODataType.LINKSET, 'keyword'),
))

bel_generics: Tuple[Generic, ...] = (
    Generic('keyword', props=(
        OProperty('label', ODataType.STRING),
        OProperty('description', ODataType.STRING),
    )),
    bel_document,
)
namespace_name = Node('nn', (basic_node,), abstract=True, props=(
    OProperty('namespace', ODataType.STRING),
    OProperty('name', ODataType.STRING),
))
bel = Node('bel', (basic_node,), abstract=True, props=(
    OProperty('bel', ODataType.STRING, mandatory=True, node_view_sub_label=True),
    OProperty('label', ODataType.STRING),
    OProperty('involved_genes', ODataType.EMBEDDEDSET, linked_type=ODataType.STRING, node_view_label=True),
    OProperty('involved_other', ODataType.EMBEDDEDSET, linked_type=ODataType.STRING, node_view_label=True),
    OProperty('suggested_corrections', ODataType.EMBEDDEDMAP, linked_type=ODataType.STRING),
))
bio_object = Node('bio_object', (bel,), abstract=True, props=(
    OProperty('chebi', ODataType.INTEGER),
))
pure_object = Node('pure_object', (basic_node,), abstract=True, props=(
    OProperty('pure', ODataType.BOOLEAN),
    OProperty('species', ODataType.INTEGER),
))
genetic_flow = Node('genetic_flow', (bio_object, namespace_name, pure_object), abstract=True)
bio_concept = Node('bio_concept', (bel,), abstract=True)
location_object = Node('location_object', (basic_node,), abstract=True, props=(
    OProperty('location', ODataType.EMBEDDEDMAP),
))
bio_act = Node('bio_act', (bel,))
bio_list = Node('bio_list', (bel,), abstract=True)
ebel = Node('ebel', (basic_node,), abstract=True, props=(
    OProperty('bel', ODataType.STRING, node_view_sub_label=True),
    OProperty('name', ODataType.STRING, node_view_label=True),
    OProperty('namespace', ODataType.STRING),
    OProperty('label', ODataType.STRING),
))
protein = Node('protein', (genetic_flow, location_object), props=(
    OProperty('uniprot', ODataType.STRING),
))
gene = Node('gene', (genetic_flow, location_object))
rna = Node('rna', (genetic_flow, location_object))
abundance = Node('abundance', (bio_object, namespace_name, pure_object))
population = Node('population', (bio_object, namespace_name, pure_object))
from_location = Node('from_location', (ebel,))
to_location = Node('to_location', (ebel,))
biological_process = Node('biological_process', (bio_concept, namespace_name))
pathology = Node('pathology', (bio_concept, namespace_name))
complex_ = Node('complex', (bio_object, namespace_name, pure_object))
micro_rna = Node('micro_rna', (bio_object, namespace_name, location_object))
activity = Node('activity', (bio_act, namespace_name), props=(
    OProperty('default', ODataType.STRING),
))
reaction = Node('reaction', (bio_act,))
degradation = Node('degradation', (bio_act,))
cell_secretion = Node('cell_secretion', (bio_act,))
translocation = Node('translocation', (bio_act,))
cell_surface_expression = Node('cell_surface_expression', (bio_act,))
list_ = Node('list', (bio_list,))
composite = Node('composite', (bio_list,))
variant = Node('variant', (ebel,), props=(
    OProperty('hgvs', ODataType.STRING, node_view_label=True),
))
fragment = Node('fragment', (ebel,))
location = Node('location', (ebel,))
pmod = Node('pmod', (ebel,), props=(
    OProperty('position', ODataType.INTEGER, node_view_label=True),
    OProperty('type', ODataType.STRING, node_view_label=True),
    OProperty('amino_acid', ODataType.STRING, node_view_label=True),
))
gmod = Node('gmod', (ebel,))
reactants = Node('reactants', (ebel,))
products = Node('products', (ebel,))
fusion_protein = Node('fusion_protein', (bel,))
fusion_rna = Node('fusion_rna', (bel,))
fusion_gene = Node('fusion_gene', (bel,))

bel_nodes: Tuple[Node, ...] = (
    bel,
    namespace_name,
    pure_object,
    location_object,
    bio_concept,
    biological_process,
    pathology,
    bio_object,
    complex_,
    abundance,
    population,
    genetic_flow,
    gene,
    rna,
    protein,
    micro_rna,
    bio_act,
    activity,
    reaction,
    degradation,
    cell_secretion,
    translocation,
    cell_surface_expression,
    bio_list,
    list_,
    composite,
    ebel,
    variant,
    fragment,
    location,
    pmod,
    gmod,
    from_location,
    to_location,
    reactants,
    products,
    fusion_protein,
    fusion_rna,
    fusion_gene,
)

bel_relation = Edge('bel_relation', (basic_edge,), abstract=True, props=(
    OProperty("evidence", ODataType.STRING),
    OProperty("pmid", ODataType.INTEGER),
    OProperty("pmc", ODataType.STRING),
    OProperty("citation", ODataType.EMBEDDEDMAP),
    OProperty("annotation", ODataType.EMBEDDEDMAP),
    OProperty("document", ODataType.LINKSET, linked_class=bel_document.name)))
ebel_relation = Edge('ebel_relation', (basic_edge,), abstract=True)
causal = Edge('causal', (bel_relation,), abstract=True, in_out=(bel, bel))
correlative = Edge('correlative', (bel_relation,), abstract=True, in_out=(bel, bel))
genomic = Edge('genomic', (bel_relation,), abstract=True)
other = Edge('other', (bel_relation,), abstract=True)
deprecated = Edge('deprecated', (bel_relation,), abstract=True)
compiler = Edge('compiler', (bel_relation,), abstract=True)
has_modified = Edge('has_modified', (ebel_relation,), abstract=True)
has_variant_obj = Edge('has_variant_obj', (ebel_relation,), abstract=True)
has_located = Edge('has_located', (ebel_relation,), abstract=True)
has_ppi = Edge('has_ppi', (ebel_relation,), abstract=True, own_class=False, in_out=(protein, protein))

bel_edges: Tuple[Edge, ...] = (
    bel_relation,
    causal,
    Edge('increases', (causal,)),
    Edge('directly_increases', (causal,)),
    Edge('decreases', (causal,)),
    Edge('directly_decreases', (causal,)),
    Edge('rate_limiting_step_of', (causal,)),
    Edge('causes_no_change', (causal,)),
    Edge('regulates', (causal,)),

    correlative,
    Edge('negative_correlation', (correlative,)),
    Edge('positive_correlation', (correlative,)),
    Edge('association', (correlative,)),
    Edge('no_correlation', (correlative,)),

    genomic,
    Edge('orthologous', (genomic,), in_out=(bel, bel)),
    Edge('transcribed_to', (genomic,), in_out=(rna, gene)),
    Edge('translated_to', (genomic,), in_out=(protein, rna)),

    other,
    Edge('has_member', (other,), in_out=(bel, bel)),
    Edge('has_members', (other,), in_out=(bel, bel)),
    Edge('has_component', (other,), in_out=(bel, bel)),
    Edge('has_components', (other,), in_out=(bel, bel)),
    Edge('equivalent_to', (other,), in_out=(bel, bel)),
    Edge('is_a', (other,), in_out=(bel, bel)),
    Edge('sub_process_of', (other,), in_out=(bel, bel)),

    deprecated,
    Edge('analogous_to', (deprecated,), in_out=(bel, bel)),
    Edge('biomarker_for', (deprecated,), in_out=(bel, bel)),
    Edge('prognostic_biomarker_for', (deprecated,)),

    compiler,
    Edge('acts_in', (compiler,), in_out=(bel, bel)),
    Edge('has_product', (compiler,), in_out=(bel, bel)),
    Edge('has_variant', (compiler,), in_out=(bel, bel)),
    Edge('has_modification', (compiler,), in_out=(bel, bel)),
    Edge('reactant_in', (compiler,), in_out=(bel, bel)),
    Edge('translocates', (compiler,), in_out=(bel, bel)),
    Edge('includes', (compiler,), in_out=(bel, bel)),

    ebel_relation,
    # TODO: check if always basic_node is needed or if we can refine that
    Edge('has__protein', (ebel_relation,), in_out=(protein, basic_node)),
    Edge('has__rna', (ebel_relation,), in_out=(rna, basic_node)),
    Edge('has__gene', (ebel_relation,), in_out=(gene, basic_node)),
    Edge('has__abundance', (ebel_relation,), in_out=(abundance, basic_node)),
    Edge('has__population', (ebel_relation,), in_out=(population, basic_node)),
    Edge('has__location', (ebel_relation,), in_out=(ebel, basic_node)),
    Edge('has__from_location', (ebel_relation,), in_out=(from_location, basic_node)),
    Edge('has__to_location', (ebel_relation,), in_out=(to_location, basic_node)),
    Edge('has__fragment', (ebel_relation,), in_out=(fragment, basic_node)),
    Edge('has__pmod', (ebel_relation,), in_out=(pmod, basic_node)),
    Edge('has__gmod', (ebel_relation,), in_out=(gmod, basic_node)),
    Edge('has__complex', (ebel_relation,), in_out=(complex_, basic_node)),
    Edge('has__micro_rna', (ebel_relation,), in_out=(micro_rna, basic_node)),
    Edge('has__variant', (ebel_relation,), in_out=(variant, basic_node)),
    Edge('has__reactants', (ebel_relation,), in_out=(reactants, basic_node)),
    Edge('has__products', (ebel_relation,), in_out=(products, basic_node)),
    Edge('has__composite', (ebel_relation,), in_out=(composite, basic_node)),

    Edge('has_fragmented_protein', (ebel_relation,), in_out=(bel, bel)),

    has_modified,
    Edge('has_modified_protein', (has_modified,), in_out=(protein, protein)),
    Edge('has_modified_gene', (has_modified,), in_out=(gene, gene)),

    has_variant_obj,
    Edge('has_variant_gene', (has_variant_obj,), in_out=(gene, gene)),
    Edge('has_variant_rna', (has_variant_obj,), in_out=(rna, rna)),
    Edge('has_variant_protein', (has_variant_obj,), in_out=(protein, protein)),
    Edge('has_variant_micro_rna', (has_variant_obj,), in_out=(micro_rna, micro_rna)),

    has_located,
    Edge('has_located_gene', (has_located,), in_out=(gene, gene)),
    Edge('has_located_rna', (has_located,), in_out=(rna, rna)),
    Edge('has_located_protein', (has_located,), in_out=(protein, protein), props=(
        OProperty('levels', ODataType.EMBEDDEDMAP),
    )),
    Edge('has_located_micro_rna', (has_located,), in_out=(micro_rna, micro_rna)),
    Edge('has_located_complex', (has_located,), in_out=(complex_, complex_)),
    Edge('has_located_abundance', (has_located,), in_out=(abundance, abundance)),
    Edge('has_located_population', (has_located,), in_out=(population, population)),
    Edge('pathway_interaction', (ebel_relation,), abstract=True),

    has_ppi,
)

bel_indices = (
    OIndex(bel, ('bel',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(bel, ('involved_genes',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(bel, ('involved_other',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(bel_relation, ('evidence',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(protein, ('uniprot',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(bel_relation, ('annotation',), OIndexType.DICTIONARY),
    OIndex(bel_relation, ('citation',), OIndexType.DICTIONARY),
    OIndex(bel_relation, ('pmid',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(namespace_name, ('namespace', 'name'), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(namespace_name, ('name',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(namespace_name, ('namespace',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(genetic_flow, ('pure',), OIndexType.NOTUNIQUE_HASH_INDEX),
)

##############################################################################
# Definition of IntAct vertices, edges and indices
##############################################################################
has_ppi_ia = Edge('has_ppi_ia', (has_ppi,), props=(
    OProperty("interaction_type", ODataType.STRING),
    OProperty("interaction_type_psimi_id", ODataType.STRING),
    OProperty("confidence_value", ODataType.FLOAT),
    OProperty("detection_method", ODataType.STRING),
    OProperty("detection_method_psimi_id", ODataType.INTEGER),
    OProperty("pmid", ODataType.INTEGER),
    OProperty("interaction_ids", ODataType.EMBEDDEDMAP),
))

intact_edges: Tuple[Edge, ...] = (
    has_ppi,
    has_ppi_ia,
)

intact_indices = (
    OIndex(has_ppi_ia, ('detection_method', 'interaction_type'), OIndexType.NOTUNIQUE),
)

##############################################################################
# Definition of HGNC generics and indices
# ---------------------------------------
# See .urls.HGNC_JSON
# https://www.genenames.org/help/download
##############################################################################
hgnc = Generic('hgnc', props=(
    OProperty('id', ODataType.STRING),
    OProperty('version', ODataType.INTEGER),
    OProperty('alias_name', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('alias_symbol', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('bioparadigms_slc', ODataType.STRING),
    OProperty('ccds_id', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('cd', ODataType.STRING),
    OProperty('cosmic', ODataType.STRING),
    OProperty('date_approved_reserved', ODataType.DATE),
    OProperty('date_modified', ODataType.DATE),
    OProperty('date_name_changed', ODataType.DATE),
    OProperty('date_symbol_changed', ODataType.DATE),
    OProperty('ena', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('ensembl_gene_id', ODataType.STRING),
    OProperty('entrez_id', ODataType.INTEGER),
    OProperty('enzyme_id', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('gene_family', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('gene_family_id', ODataType.EMBEDDEDLIST),
    OProperty('homeodb', ODataType.STRING),
    OProperty('horde_id', ODataType.STRING),
    OProperty('imgt', ODataType.STRING),
    OProperty('intermediate_filament_db', ODataType.STRING),
    OProperty('iuphar', ODataType.STRING),
    OProperty('kznf_gene_catalog', ODataType.INTEGER),
    OProperty('lncipedia', ODataType.STRING),
    OProperty('lncrnadb', ODataType.STRING),
    OProperty('location', ODataType.STRING),
    OProperty('location_sortable', ODataType.STRING),
    OProperty('locus_group', ODataType.STRING),
    OProperty('locus_type', ODataType.STRING),
    OProperty('lsdb', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('mamit_trnadb', ODataType.INTEGER),
    OProperty('merops', ODataType.STRING),
    OProperty('mgd_id', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('mirbase', ODataType.STRING),
    OProperty('name', ODataType.STRING),
    OProperty('omim_id', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('orphanet', ODataType.INTEGER),
    OProperty('prev_name', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('prev_symbol', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('pseudogene_org', ODataType.STRING),
    OProperty('pubmed_id', ODataType.EMBEDDEDLIST, linked_type=ODataType.INTEGER),
    OProperty('refseq_accession', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('rgd_id', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('rna_central_ids', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('snornabase', ODataType.STRING),
    OProperty('status', ODataType.STRING),
    OProperty('symbol', ODataType.STRING),
    OProperty('ucsc_id', ODataType.STRING),
    OProperty('uniprot_ids', ODataType.EMBEDDEDLIST, linked_type=ODataType.STRING),
    OProperty('uuid', ODataType.STRING),
    OProperty('vega_id', ODataType.STRING)))

hgnc_generics: Tuple[Generic, ...] = (hgnc,)

hgnc_nodes: Tuple[Node, ...] = (deepcopy(genetic_flow).add_properties([OProperty('hgnc', ODataType.LINK, 'hgnc')]),)

hgnc_indices = (
    OIndex(hgnc, ('symbol',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(hgnc, ('id',), OIndexType.UNIQUE_HASH_INDEX),
    OIndex(hgnc, ('ensembl_gene_id',), OIndexType.NOTUNIQUE_HASH_INDEX),
)

##############################################################################
# Definition of GwasCatalog generics and indices
##############################################################################

mirtarbase_edges: Tuple[Edge, ...] = (
    Edge('has_mirgene_target', (ebel_relation,), props=(
        OProperty('support_type', ODataType.STRING),
        OProperty('pmid', ODataType.INTEGER),
        OProperty('experiments', ODataType.EMBEDDEDSET, linked_type=ODataType.STRING),
    ), in_out=(rna, micro_rna)),
)

##############################################################################
# Definition of GwasCatalog generics and indices
##############################################################################
snp = Node('snp', (ebel,), False, (
    OProperty('rs_number', ODataType.STRING, node_view_label=True),
), own_class=False)
gwascatalog_nodes: Tuple[Node, ...] = (snp,)

has_snp = Edge('has_snp', (ebel_relation,), abstract=True, own_class=False, in_out=(snp, gene))
has_mapped_snp = Edge('has_mapped_snp', (has_snp,), abstract=True, own_class=False)
has_downstream_snp = Edge('has_downstream_snp', (has_snp,), abstract=True, own_class=False)
has_upstream_snp = Edge('has_upstream_snp', (has_snp,), abstract=True, own_class=False)
has_snp_gwascatalog = Edge('has_snp_gwascatalog', (has_snp,), abstract=True, props=(
    OProperty('disease_trait', ODataType.STRING),
    OProperty('pubmed_id', ODataType.INTEGER)
))

gwascatalog_edges: Tuple[Edge, ...] = (
    has_snp,
    has_snp_gwascatalog,
    has_mapped_snp,
    has_downstream_snp,
    has_upstream_snp,
    Edge('has_mapped_snp_gc', (has_mapped_snp, has_snp_gwascatalog)),
    Edge('has_downstream_snp_gc', (has_downstream_snp, has_snp_gwascatalog)),
    Edge('has_upstream_snp_gc', (has_upstream_snp, has_snp_gwascatalog)),
)

##############################################################################
# Definition of Ortholog generics and indices
##############################################################################
drug = Node('drug', (ebel,), abstract=True, own_class=False)
drug_db = Node('drug_db', (drug,), props=(
    OProperty('label', ODataType.STRING, node_view_label=True),
    OProperty('drugbank_id', ODataType.STRING),
    OProperty('description', ODataType.STRING),
    OProperty('cas_number', ODataType.STRING, node_view_sub_label=True),
    OProperty('indication', ODataType.STRING),
    OProperty('pharmacodynamics', ODataType.STRING),
    OProperty('toxicity', ODataType.STRING),
    OProperty('metabolism', ODataType.STRING),
    OProperty('mechanism_of_action', ODataType.STRING),
))

drugbank_nodes: Tuple[Node, ...] = (
    drug,
    drug_db,
)

has_drug_target = Edge('has_drug_target', (ebel_relation,), abstract=True, own_class=False)
has_drug_target_db = Edge('has_drug_target_db', (has_drug_target,), in_out=(protein, drug_db), props=(
    OProperty("action", ODataType.STRING),
    OProperty("known_action", ODataType.STRING),
))

drugbank_edges: Tuple[Edge, ...] = (
    has_drug_target,
    has_drug_target_db,
)

drugbank_indices = (
    OIndex(has_drug_target_db, ('action',), OIndexType.NOTUNIQUE_HASH_INDEX),
    OIndex(drug_db, ('drugbank_id',), OIndexType.UNIQUE_HASH_INDEX),
)

##############################################################################
# Definition of IUPHAR's Guide to Pharmacology drugs
##############################################################################

iuphar_interaction = Edge('iuphar_interaction', (ebel_relation,), props=(
    OProperty("pmids", ODataType.EMBEDDEDSET, linked_type=ODataType.INTEGER),
    OProperty("assay_description", ODataType.STRING),
    OProperty("affinity_units", ODataType.STRING),
    OProperty("affinity_low", ODataType.FLOAT),
    OProperty("affinity_median", ODataType.FLOAT),
    OProperty("affinity_high", ODataType.FLOAT),
    OProperty("type", ODataType.STRING),
    OProperty("action", ODataType.STRING),
), in_out=(bel, bel))

iuphar_edges: Tuple[Edge, ...] = (
    iuphar_interaction,
    Edge('agonist_of__iu', (iuphar_interaction,)),
    Edge('inhibits__iu', (iuphar_interaction,)),
    Edge('antagonist_of__iu', (iuphar_interaction,)),
    Edge('channel_blocker_of__iu', (iuphar_interaction,)),
    Edge('allosteric_modulator_of__iu', (iuphar_interaction,)),
    Edge('activates__iu', (iuphar_interaction,)),
    Edge('antibody_against__iu', (iuphar_interaction,)),
    Edge('inhibits_gating__iu', (iuphar_interaction,)),
)

##############################################################################
# Definition of Reactome generics and indices
##############################################################################

reactome_nodes: Tuple[Node, ...] = (
    deepcopy(protein).add_properties(
        [OProperty('reactome_pathways', ODataType.EMBEDDEDSET, linked_type=ODataType.STRING)]),
)

##############################################################################
# Definition of Reactome generics and indices
##############################################################################

has_ppi_bg = Edge('has_ppi_bg', (has_ppi,), abstract=True, props=(
    OProperty("modification", ODataType.STRING),
    OProperty("pmids", ODataType.EMBEDDEDSET, linked_type=ODataType.INTEGER),
    OProperty("dois", ODataType.EMBEDDEDSET, linked_type=ODataType.STRING),
    OProperty("biogrid_ids", ODataType.EMBEDDEDSET, linked_type=ODataType.INTEGER),
))

biogrid_edges: Tuple[Edge, ...] = (
    has_ppi_bg,
    Edge('decreases_bg', (has_ppi_bg,)),
)

biogrid_edges_auto_generated = []
for pmod in normalized_pmod.keys():
    for effect in ['increases', 'decreases']:
        edge_name = f"{effect}_{pmod}_bg"
        biogrid_edges_auto_generated.append(Edge(edge_name, (has_ppi_bg,)))

biogrid_edges += tuple(biogrid_edges_auto_generated)

##############################################################################
# Definition of StringDB generics and indices
##############################################################################

has_action = Edge('has_action', (ebel_relation,), abstract=True, own_class=False, in_out=(protein, protein))
has_action_st = Edge('has_action_st', (has_action,), abstract=True)
has_ppi_st = Edge('has_ppi_st', (has_ppi,), abstract=True, props=(
    OProperty("score", ODataType.INTEGER),
))
controls_expression_of_st = Edge('controls_expression_of_st', (has_action_st,), abstract=True)
increases_expression_of = Edge('increases_expression_of', abstract=True, own_class=False)
decreases_expression_of = Edge('decreases_expression_of', abstract=True, own_class=False)

stringdb_edges: Tuple[Edge, ...] = (
    has_ppi,
    Edge('has_ppi_st', (has_ppi,), False, props=(
        OProperty("neighborhood", ODataType.INTEGER),
        OProperty("neighborhood_transferred", ODataType.INTEGER),
        OProperty("fusion", ODataType.INTEGER),
        OProperty("cooccurence", ODataType.INTEGER),
        OProperty("homology", ODataType.INTEGER),
        OProperty("coexpression", ODataType.INTEGER),
        OProperty("coexpression_transferred", ODataType.INTEGER),
        OProperty("experiments", ODataType.INTEGER),
        OProperty("experiments_transferred", ODataType.INTEGER),
        OProperty("database", ODataType.INTEGER),
        OProperty("database_transferred", ODataType.INTEGER),
        OProperty("textmining", ODataType.INTEGER),
        OProperty("textmining_transferred", ODataType.INTEGER),
        OProperty("combined_score", ODataType.INTEGER),
    )),

    has_action,
    has_action_st,
    has_ppi_st,
    Edge('activates_st', (has_action_st,)),
    Edge('inhibits_st', (has_action_st,)),
    controls_expression_of_st,
    increases_expression_of,
    decreases_expression_of,
    Edge('increases_expression_of_st', (has_action_st, controls_expression_of_st, increases_expression_of)),
    Edge('decreases_expression_of_st', (has_action_st, controls_expression_of_st, decreases_expression_of)),
    Edge('controls_pmod_of_st', (has_action_st,)),
)

##############################################################################
# Definition of ClinVar generics and indices
##############################################################################

clinvar_nodes: Tuple[Node, ...] = (
    snp,
)

has_snp_clinvar = Edge('has_snp_clinvar', (has_snp,), abstract=True, props=(
    OProperty('keyword', ODataType.STRING),
    OProperty('clinical_significance', ODataType.STRING),
    OProperty('phenotype', ODataType.STRING),
))

clinvar_edges: Tuple[Edge, ...] = (
    has_snp,
    has_snp_clinvar,
    has_mapped_snp,
    has_downstream_snp,
    has_upstream_snp,
    Edge('has_mapped_snp_cv', (has_mapped_snp, has_snp_clinvar)),
    Edge('has_downstream_snp_cv', (has_downstream_snp, has_snp_clinvar)),
    Edge('has_upstream_snp_cv', (has_upstream_snp, has_snp_clinvar)),
)

clinvar_indices = (
    OIndex(snp, ('rs_number',), OIndexType.UNIQUE_HASH_INDEX),
)

##############################################################################
# Definition of ClinVar generics and indices
# http://stitch.embl.de
##############################################################################
stitch = Generic('stitch', props=(
    OProperty('pubchem_id', ODataType.INTEGER),
    OProperty('ensembl_protein_id', ODataType.INTEGER),
    OProperty('experimental_direct', ODataType.INTEGER),
    OProperty('experimental_transferred', ODataType.INTEGER),
    OProperty('prediction_direct', ODataType.INTEGER),
    OProperty('prediction_transferred', ODataType.INTEGER),
    OProperty('database_direct', ODataType.INTEGER),
    OProperty('database_transferred', ODataType.INTEGER),
    OProperty('textmining_direct', ODataType.INTEGER),
    OProperty('textmining_transferred', ODataType.INTEGER),
    OProperty('combined_score', ODataType.INTEGER),
    OProperty('type', ODataType.STRING),
    OProperty('hgnc', ODataType.LINK, linked_class=hgnc.name),
    OProperty('pubchem', ODataType.LINK, 'stitch_pubchem'),
))

stitch_generics: Tuple[Generic, ...] = (
    Generic('stitch_pubchem', props=(
        OProperty('CID', ODataType.INTEGER),
        OProperty('IUPACName', ODataType.STRING),
        OProperty('MolecularFormula', ODataType.STRING),
        OProperty('IsomericSMILES', ODataType.STRING),
        OProperty('InChI', ODataType.STRING),
        OProperty('InChIKey', ODataType.STRING),
    )),
    stitch,
)

stitch_indices = (
    OIndex(stitch, ("ensembl_protein_id",), OIndexType.NOTUNIQUE),
    OIndex(stitch, ("pubchem_id",), OIndexType.NOTUNIQUE),
    OIndex(stitch, ("pubchem",), OIndexType.NOTUNIQUE),
    OIndex(stitch, ("hgnc",), OIndexType.NOTUNIQUE),
    OIndex(stitch, ("combined_score",), OIndexType.NOTUNIQUE),
)

##############################################################################
# Definition of MirTarBase edges
##############################################################################


##############################################################################
# Definition of DisGeNet
##############################################################################

disgenet_nodes: Tuple[Node, ...] = (
    snp,
)

gene_disease_association = Edge('gene_disease_association', (ebel_relation,), abstract=True)
has_snp_disgenet = Edge('has_snp_disgenet', (has_snp,), abstract=True, props=(
    OProperty('disease_name', ODataType.STRING),
    OProperty('pmid', ODataType.INTEGER),
    OProperty('score', ODataType.FLOAT),
    OProperty('source', ODataType.STRING),
))

disgenet_edges: Tuple[Edge, ...] = (
    gene_disease_association,
    Edge('disgenet_gene_disease', (gene_disease_association,), props=(
        OProperty('pmid', ODataType.INTEGER),
        OProperty('score', ODataType.FLOAT),
        OProperty('source', ODataType.STRING),
    )),

    has_snp,
    has_snp_disgenet,
    has_mapped_snp,
    has_downstream_snp,
    has_upstream_snp,
    Edge('has_mapped_snp_dgn', (has_mapped_snp, has_snp_disgenet)),
    Edge('has_downstream_snp_dgn', (has_downstream_snp, has_snp_disgenet)),
    Edge('has_upstream_snp_dgn', (has_upstream_snp, has_snp_disgenet)),
)

##############################################################################
# Definition of PathwayCommons generics, edges and indices
##############################################################################

pathway_commons_generics: Tuple[Generic, ...] = (
    Generic('pc_pathway_name', props=(
        OProperty('name', ODataType.STRING),
    )),
)
has_action_pc = Edge('has_action_pc', (has_action,), abstract=True, props=(
    OProperty("pathways", ODataType.LINKSET, 'pc_pathway_name'),
    OProperty("sources", ODataType.EMBEDDEDSET, linked_type=ODataType.STRING),
    OProperty("pmids", ODataType.EMBEDDEDSET, linked_type=ODataType.INTEGER),
    OProperty("type", ODataType.STRING),
))

pathway_commons_edges: Tuple[Edge, ...] = (
    has_action,
    has_action_pc,
    Edge('controls_expression_of_pc', (has_action_pc,)),
    Edge('controls_phosphorylation_of_pc', (has_action_pc,)),
    Edge('controls_transport_of_pc', (has_action_pc,)),
)

##############################################################################
# Definition of KEGG generics, edges and indices
##############################################################################

pathway_interaction = Edge('pathway_interaction', (ebel_relation,), abstract=True, own_class=False)
has_ppi_kg = Edge('has_ppi_kg', (pathway_interaction,), abstract=True, props=(
    OProperty("interaction_type", ODataType.STRING),
    OProperty('pathway_names', ODataType.EMBEDDEDSET),
))
increases_expression_of = Edge('increases_expression_of', abstract=True, own_class=False)
decreases_expression_of = Edge('decreases_expression_of', abstract=True, own_class=False)

kegg_edges: Tuple[Edge, ...] = (
    pathway_interaction,
    has_ppi_kg,
    increases_expression_of,
    decreases_expression_of,
    Edge('decreases_pho_kg', (has_ppi_kg,)),
    Edge('increases_gly_kg', (has_ppi_kg,)),
    Edge('increases_me0_kg', (has_ppi_kg,)),
    Edge('increases_pho_kg', (has_ppi_kg,)),
    Edge('increases_ubi_kg', (has_ppi_kg,)),
)

##############################################################################
# NSides definitions
##############################################################################

side_effect = Node('side_effect', (ebel,), props=(
    OProperty('label', ODataType.STRING, node_view_label=True),
    OProperty('condition_meddra_id', ODataType.STRING, node_view_sub_label=True),
))

nsides_nodes: Tuple[Node, ...] = (
    side_effect,
)

nsides_edges: Tuple[Edge] = (
    Edge('has_side_effect', (ebel_relation,), props=(
        OProperty('prr', ODataType.FLOAT),
        OProperty('mean_reporting_frequency', ODataType.FLOAT),
    ), in_out=(side_effect, drug_db)),
)

##############################################################################
# All OrientDB classes as Dict
##############################################################################

nodes: Tuple[Node, ...] = (bel_nodes
                           + hgnc_nodes
                           + gwascatalog_nodes
                           + drugbank_nodes
                           + reactome_nodes
                           + clinvar_nodes
                           + disgenet_nodes
                           + nsides_nodes)

edges: Tuple[Edge, ...] = (bel_edges
                           + intact_edges
                           + mirtarbase_edges
                           + gwascatalog_edges
                           + drugbank_edges
                           + iuphar_edges
                           + biogrid_edges
                           + biogrid_edges
                           + stringdb_edges
                           + clinvar_edges
                           + disgenet_edges
                           + kegg_edges
                           + nsides_edges)

nodes_and_edges: Tuple[OClass, ...] = nodes + edges

nodes_and_edges_dict: Dict[str, OClass] = {o_class.name: o_class for o_class in nodes_and_edges}
non_abstract_nodes_and_edges_dict: Dict[str, OClass] = {o_class.name: o_class for o_class in nodes_and_edges if
                                                        o_class.abstract is False}
abstract_nodes_and_edges_dict: Dict[str, OClass] = {o_class.name: o_class for o_class in nodes_and_edges if
                                                    o_class.abstract is True}


def get_columns(class_name, columns: Tuple[str] = (), exclude_non_serializable: bool = True) -> list:
    """Return list of columns.

    Parameters
    ----------
    class_name : str
        Class name of edge or node.
    columns : List[str], optional
        List of columns.
    exclude_non_serializable : bool
        If True, excludes all non serializable columns.

    Returns
    -------
    list
        List of columns.
    """
    o_class: OClass = nodes_and_edges_dict[class_name]
    exclude_classes = [ODataType.LINK, ODataType.LINKSET, ODataType.LINKMAP, ODataType.LINKBAG]

    columns = list(columns)

    if exclude_non_serializable:
        columns += [p.prop_name for p in o_class.props if p.data_type not in exclude_classes]
    else:
        columns += [p.prop_name for p in o_class.props]
    for extends_name in o_class.extends:
        if extends_name not in ['V', 'E']:
            columns += get_columns(extends_name, tuple(columns), exclude_non_serializable)
    return columns


def get_node_view_labels(name: str, labels: dict = None) -> dict:
    """Get dictionary of labels for a given node.

    Parameters
    ----------
    name : str
        Class name of edge or node.
    labels : dict
        Dictionary of labels and sub labels.

    Returns
    -------
    dict
        {"label": list_of_labels, "sub_label": list_of_sub_labels}
    """
    if not labels:
        labels = {'label': [], 'sub_label': []}
    o_class = nodes_and_edges_dict[name]
    for p in o_class.props:
        if p.node_view_label:
            labels['label'].append(p.prop_name)
        if p.node_view_sub_label:
            labels['sub_label'].append(p.prop_name)
    if not labels['label']:
        for extends_name in o_class.extends:
            if extends_name not in ['V', 'E']:
                get_node_view_labels(extends_name, labels)
    return labels
