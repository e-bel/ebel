"""UniProt API methods."""
from flask import request

from ebel import Bel
from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import uniprot
from ebel.web.api.ebel.v1 import _get_paginated_query_result, _get_terms_from_model_starts_with


def get_uniprot():
    """Get paginated list of UniProt entries."""
    q = RDBMS.get_session().query(uniprot.Uniprot)

    accession = request.args.get('accession')
    q = q.filter_by(accession=accession) if accession else q

    taxid = request.args.get('taxonomy_id')
    q = q.filter_by(taxid=taxid) if taxid else q

    gene_symbol = request.args.get('gene_symbol')
    if gene_symbol:
        q = q.join(uniprot.GeneSymbol).filter_by(symbol=gene_symbol)

    keyword = request.args.get('keyword')
    if keyword:
        q = q.join(uniprot.uniprot__uniprot_keyword) \
            .join(uniprot.Keyword).filter_by(keyword_name=keyword)

    xref_db = request.args.get('xref_db')
    xref_id = request.args.get('xref_id')
    if xref_db or xref_id:
        q = q.join(uniprot.uniprot__uniprot_xref).join(uniprot.Xref)
        q = q.filter_by(db=xref_db) if xref_db else q
        q = q.filter_by(identifier=xref_id) if xref_id else q

    subcellular_location = request.args.get('subcellular_location')
    if subcellular_location:
        q = q.join(uniprot.uniprot__uniprot_subcellular_location) \
            .join(uniprot.SubcellularLocation).filter_by(name=subcellular_location)

    return _get_paginated_query_result(q)


def get_keyword_starts_with():
    """Get entries where keyword starts with given value."""
    return _get_terms_from_model_starts_with('keyword', uniprot.Keyword.keyword_name)


def get_subcellular_location_starts_with():
    """Get entries where subcellular location starts with given value."""
    return _get_terms_from_model_starts_with('subcellular_location', uniprot.SubcellularLocation.name)


def get_gene_symbol_starts_with():
    """Get entries where symbol starts with given value."""
    return _get_terms_from_model_starts_with('gene_symbol', uniprot.GeneSymbol.symbol)


def get_gene_starts_with():
    """Get entries where gene starts with given value."""
    return _get_terms_from_model_starts_with('gene', uniprot.Gene.name)


def get_organism_starts_with():
    """Get entries where organism starts with given value."""
    return _get_terms_from_model_starts_with('organism', uniprot.Organism.scientific_name)


def get_function_starts_with():
    """Get entries where description starts with given value."""
    return _get_terms_from_model_starts_with('description', uniprot.Function.description)


def get_bel_node_uniprot():
    """Get UniProt related eBEL nodes."""
    b = Bel()
    conf = {
        'rid': "@rid.asString()",
        'name': "name",
        'namespace': "namespace",
        'bel': "bel",
        'uniprot_accession': "uniprot"
    }
    sql = "SELECT "
    sql += ', '.join([f"{v} as {k}" for k, v in conf.items()])
    sql += " FROM protein WHERE pure = true"

    uniprot = request.args.get('accession')

    if uniprot:
        sql += f' AND uniprot = "{uniprot}"'
    else:
        return {'error': "uniprot_accession is required."}

    entries = b.query_get_dict(sql)
    if entries:
        result_dict = entries[0]
        result_dict['edges'] = {}
        for direction in ('in', 'out'):
            match = "match {class:protein, where:(uniprot='"
            match += uniprot + "' and pure=true)}." + direction + "E(bel_relation){as:e}"
            match += " return e.@rid, e.@class as relation"
            sql_edges = f"""Select relation, count(*)
                    from ({match}) group by relation order by count desc"""
            result_dict['edges'][direction] = b.query_get_dict(sql_edges)

        return result_dict
