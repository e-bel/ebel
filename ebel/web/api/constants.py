"""API server string constants."""
select_bel_columns_list = [
    'out.name as subject_name',
    'out.label as subject_label',
    'out.namespace as subject_namespace',
    'out.bel as subject_bel',
    'out.involved_genes as subject_involved_genes',
    'out.involved_other as subject_involved_other',
    'out.@class as subject_class',
    'out.@rid.asString() as subject_id',
    '@class as relation',
    'pmid',
    '@rid.asString() as edge_id',
    'evidence',
    'citation.last_author as last_author',
    'citation.title as title',
    'citation.pub_date as publication_date',
    'annotation',
    'in.name as object_name',
    'in.label as object_label',
    'in.namespace as object_namespace',
    'in.bel as object_bel',
    'in.involved_genes as object_involved_genes',
    'in.involved_other as object_involved_other',
    'in.@class as object_class',
    'in.@rid.asString() as object_id'
]

select_bel_columns = ', '.join(select_bel_columns_list)

match_bel_columns_list = [
    's.bel as subject_bel',
    's.involved_genes as subject_involved_genes',
    's.involved_other as subject_involved_other',
    's.@class as subject_class',
    's.@rid.asString() as subject_id',
    's.name as subject_name',
    's.label as subject_label',
    's.namespace as subject_namespace',
    'r.@class as relation',
    'r.pmid as pmid',
    'r.@rid.asString() as edge_id',
    'r.evidence as evidence',
    'r.citation.last_author as last_author',
    'r.citation.title as title',
    'r.citation.pub_date as publication_date',
    'r.annotation as annotation',
    'o.bel as object_bel',
    'o.involved_genes as object_involved_genes',
    'o.involved_other as object_involved_other',
    'o.@class as object_class',
    'o.@rid.asString() as object_id',
    'o.name as object_name',
    'o.label as object_label',
    'o.namespace as object_namespace',
]

match_bel_columns = ', '.join(match_bel_columns_list)
