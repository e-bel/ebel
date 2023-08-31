"""Neo4j node and edge structure.

These maps are for maintaining backwards compatibility, it allows the eBEL JSONs to be parsed and imported.

NOTE: Nodes can be given multiple labels, but not edges."""


ABSTRACT_LABELS = ("BioConcept", "GeneticFlow")

node_map = {
    "abundance": "Abundance",
    "activity": "Activity",
    "biological_process": "BiologicalProcess:BioConcept",
    "cell_secretion": "CellSecretion",
    "cell_surface_expression": "CellSurfaceExpression",
    "complex": "Complex",
    "composite": "Composite",
    "degradation": "Degradation",
    "fragment": "Fragment",
    "from_location": "FromLocation",
    "fusion": "Fusion",
    "gene": "Gene:GeneticFlow",
    "gmod": "Gmod",
    "list": "List",
    "location": "Location",
    "micro_rna": "MicroRna",
    "molecular_activity": "MolecularActivity",
    "pathology": "BioConcept:Pathology",
    "pmod": "ProteinModification",
    "population": "Population",
    "products": "Products",
    "protein": "GeneticFlow:Protein",
    "reactants": "Reactants",
    "reaction": "Reaction",
    "rna": "GeneticFlow:Rna",
    "to_location": "ToLocation",
    "translocation": "Translocation",
    "variant": "Variant"
}

edge_map = {
    "analogous_to": "ANALOGOUS",
    "association": "ASSOCIATION",
    "biomarker_for": "BIOMARKER_FOR",
    "causes_no_change": "CAUSES_NO_CHANGE",
    "decreases": "DECREASES",
    "directly_decreases": "DIRECTLY_DECREASES",
    "directly_increases": "DIRECTLY_INCREASES",
    "equivalent_to": "EQUIVALENT_TO",
    "has_activity": "HAS_ACTIVITY",
    "has_component": "HAS_COMPONENT",
    "has_components": "HAS_COMPONENTS",
    "has_member": "HAS_MEMBER",
    "has_members": "HAS_MEMBERS",
    "has_modification": "HAS_MODIFICATION",
    "includes": "INCLUDES",
    "increases": "INCREASES",
    "is_a": "IS_A",
    "negative_correlation": "NEGATIVE_CORRELATION",
    "orthologous": "ORTHOLOGOUS",
    "positive_correlation": "POSITIVE_CORRELATION",
    "prognostic_biomarker_for": "PROGNOSTIC_BIOMARKER_FOR",
    "rate_limiting_step_of": "RATE_LIMITING_STEP_OF",
    "regulates": "REGULATES",
    "sub_process_of": "SUB_PROCESS_OF",
    "transcribed_to": "TRANSCRIBED_TO",
    "translated_to": "TRANSLATED_TO",
}
