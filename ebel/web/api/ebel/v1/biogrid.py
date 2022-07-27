"""BioGRID API methods."""
import json

from math import ceil
from flask import request
from sqlalchemy import or_, and_
from collections import namedtuple
from typing import List, Dict, Optional

from ebel import Bel
from ebel.manager.orientdb.biodbs.biogrid import MODIFICATIONS
from ebel.manager.rdbms.models.biogrid import (
    Biogrid,
    ExperimentalSystem,
    Source,
    Modification,
    Taxonomy,
    Interactor,
    Publication)
from ebel.web.api import RDBMS
from ebel.web.api.ebel.v1 import _get_data


SQL_SELECT_HAS_PPI_BG = """select
    @rid.asString() as rid,
    in.@rid.asString() as subject_rid,
    in.name as subject_name,
    in.namespace as subject_namespace,
    in.label as subject_label,
    in.uniprot as subject_uniprot,
    in.species as subject_taxonomy_id,
    modification,
    pmids,
    biogrid_ids,
    out.@rid.asString() as object_rid,
    out.name as object_name,
    out.namespace as object_namespace,
    out.label as object_label,
    out.uniprot as object_uniprot,
    out.species as object_taxonomy_id
from has_ppi_bg where """


def get_has_ppi_bg_by_symbol_taxid():
    """Get has_ppi_bg edge by POST request with parameter `symbol`."""
    symbol = request.args.get('symbol')
    if not symbol:
        return {'error': "symbol is required"}
    namespace = request.args.get('namespace', 'HGNC')
    modification = request.args.get('modification')

    sql = f"""{SQL_SELECT_HAS_PPI_BG}((in.name='{symbol}' and in.namespace='{namespace}')
            or (out.name='{symbol}' and out.namespace='{namespace}'))"""
    if modification and modification in MODIFICATIONS:
        sql += f" and modification = '{modification}'"
    return Bel().query_get_dict(sql)


def get_has_ppi_bg_by_uniprot() -> List[dict]:
    """Get has_ppi_bg edge by POST request with parameter `uniprot`."""
    uniprot = request.args.get('uniprot')
    if not uniprot:
        return [{'error': "uniprot is required"}]
    modification = request.args.get('modification')
    sql = f"""{SQL_SELECT_HAS_PPI_BG}( in.uniprot='{uniprot}' or out.uniprot='{uniprot}')"""
    if modification and modification in MODIFICATIONS:
        sql += f" and modification = '{modification}'"
    return Bel().query_get_dict(sql)


def get_biogrid_by_biogrid_id() -> dict:
    """Get BioGrid entry by biogrid_id.

    Parameters:
        biogrid_id (int): BioGrid identifier

    Returns:
        dict: BioGrid entry.
    """
    biogrid_id: int = request.args.get('biogrid_id')
    biogrid_entry = RDBMS.get_session().query(Biogrid).filter_by(biogrid_id=biogrid_id).first()
    return biogrid_entry.as_dict()


def get_experimental_systems() -> Dict[str, int]:
    """Get all available experimental systems.

    Returns:
        Dict[str, int]: schema: Dict[experimental_system, table_id]
    """
    es = ExperimentalSystem.experimental_system
    rs = RDBMS.get_session().query(es, ExperimentalSystem.id).order_by(es.asc()).all()
    return {x.experimental_system: x.id for x in rs}


def get_sources() -> Dict[str, int]:
    """Get all available sources.

    Returns:
        Dict[str, int]: schema: Dict[source, table_id]
    """
    rs = RDBMS.get_session().query(Source.source, Source.id).order_by(Source.source.asc()).all()
    return {x.source: x.id for x in rs}


def get_taxonomies() -> Dict[str, int]:
    """Get all available taxonomies.

    Returns:
        Dict[str, int]: schema: Dict[organism_name, taxonomy_id]
    """
    org = Taxonomy.organism_name
    rs = RDBMS.get_session().query(org, Taxonomy.taxonomy_id).order_by(org.asc()).all()
    return {x.organism_name: x.taxonomy_id for x in rs}


def get_modifications() -> Dict[str, int]:
    """Get all available modifications.

    Returns:
        Dict[str, int]: schema: Dict[modification, table_id]
    """
    mod = Modification.modification
    rs = RDBMS.get_session().query(Modification.id, mod).order_by(mod.asc()).all()
    return {x.modification: x.id for x in rs}


def get_biogrid_by_pmid() -> List[dict]:
    """List of BioGrid entries by PubMed identifier.

    Parameters:
        pmid (int): PubMed identifier

    Returns:
        List[dict]: List[BioGrid entry]
    """
    pmid = request.args.get('pmid')
    publication_id = RDBMS.get_session().query(
        Publication.id
    ).filter_by(
        source='PUBMED', source_identifier=pmid
    ).first()[0]
    biogrid_entry = RDBMS.get_session().query(Biogrid).filter_by(publication_id=publication_id).all()
    return [x.as_dict() for x in biogrid_entry]


def get_biogrid() -> dict:
    """List BioGrid entries by GET request.

    Parameters:
    * id_type_a (str): Type of Interactor A
    * interactor_a (str): Interactor B identifier
    * taxonomy_id_a (int): NCBI taxonomy ID of interactor B
    * id_type_b (str): Type of Interactor B
    * interactor_b (str): Interactor B identifier
    * taxonomy_id_b (int): NCBI taxonomy ID of interactor B
    * experimental_system (str): Experimental system used to identifiy the interaction
    * modification (str): Type of modification
    * source (str): Reference database
    * page_size (int): Number of entries per page
    * page (int): Number of page

    Returns:
        List[dict]: List[BioGrid entry]
    """
    # cancel if neither interactor_a or interactor_b are submitted
    if not (bool(request.args.get('interactor_a')) or bool(request.args.get('interactor_b'))):
        return {'error': "At least interactor_a or interactor_b"}

    Req = namedtuple('RequestObject', ['id_type_a', 'interactor_a', 'taxonomy_id_a', 'id_type_b', 'interactor_b',
                                       'taxonomy_id_b', 'experimental_system', 'modification', 'source',
                                       'interaction_directed', 'page_size', 'page'])
    q = {
        'id_type_a': "symbol",
        'interactor_a': None,
        'taxonomy_id_a': 9606,
        'id_type_b': "symbol",
        'interactor_b': None,
        'taxonomy_id_b': 9606,
        'experimental_system': None,
        'modification': None,
        'source': None,
        'interaction_directed': False,
        'page_size': 10,
        'page': 1
    }
    for key, value in request.args.items():
        if key in q:
            q[key] = value
    req = Req(**q)

    if req.interactor_a:
        a = {req.id_type_a: req.interactor_a, 'taxonomy_id': req.taxonomy_id_a}
        a = {k: v for k, v in a.items() if v}
        biogrid_a_ids = [x[0] for x in RDBMS.get_session().query(Interactor.biogrid_id).filter_by(**a)]

    if req.interactor_b:
        b = {req.id_type_b: req.interactor_b, 'taxonomy_id': req.taxonomy_id_b}
        b = {k: v for k, v in b.items() if v}
        biogrid_b_ids = [x[0] for x in RDBMS.get_session().query(Interactor.biogrid_id).filter_by(**b)]

    if req.interactor_a and req.interactor_b:
        interaction_forward = and_(Biogrid.biogrid_a_id.in_(biogrid_a_ids), Biogrid.biogrid_b_id.in_(biogrid_b_ids))
        if req.interaction_directed:
            query_filter = interaction_forward
        else:
            interaction_backward = and_(Biogrid.biogrid_a_id.in_(biogrid_b_ids),
                                        Biogrid.biogrid_b_id.in_(biogrid_a_ids))
            query_filter = or_(interaction_forward, interaction_backward)
    else:
        if req.interactor_a:
            if req.interaction_directed is True or req.interaction_directed == 'true':
                query_filter = Biogrid.biogrid_a_id.in_(biogrid_a_ids)
            else:
                query_filter = or_(Biogrid.biogrid_a_id.in_(biogrid_a_ids), Biogrid.biogrid_b_id.in_(biogrid_a_ids))
        if req.interactor_b:
            if req.interaction_directed is True or req.interaction_directed == 'true':
                query_filter = Biogrid.biogrid_b_id.in_(biogrid_b_ids)
            else:
                query_filter = or_(Biogrid.biogrid_a_id.in_(biogrid_b_ids), Biogrid.biogrid_b_id.in_(biogrid_b_ids))

    query = RDBMS.get_session().query(Biogrid).filter(query_filter)

    if req.experimental_system:
        experimental_system_id = RDBMS.get_session().query(ExperimentalSystem.id).filter_by(
            experimental_system=req.experimental_system
        ).first()[0]
        query = query.filter_by(experimental_system_id=experimental_system_id)

    if req.modification:
        modification_id = RDBMS.get_session().query(
            Modification.id
        ).filter_by(
            modification=req.modification
        ).first()[0]
        query = query.filter_by(modification_id=modification_id)

    if req.source:
        source_id = RDBMS.get_session().query(Source.id).filter_by(source=req.source).first()[0]
        query = query.filter_by(source_id=source_id)

    number_of_results = query.count()

    limit = int(req.page_size)
    page = int(req.page)
    offset = (page - 1) * limit
    offset = offset if offset <= 100 else 100
    query = query.limit(limit).offset(offset)
    pages = ceil(number_of_results / limit)

    return {
        'page': page,
        'page_size': limit,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': [x.as_dict() for x in query.all()]
    }


def get_biogrid_using_post():
    """Get BioGRID entry via POSt method."""
    return _get_data(Biogrid)


def get_interactor_by_symbol():
    """Get interactor by gene symbol."""
    ra = request.args

    taxonomy_id = int(ra.get('taxonomy_id', 9606))
    search_term = ra.get('symbol', "")

    query = RDBMS.get_session().query(Interactor).filter(
        Interactor.taxonomy_id == taxonomy_id,
        Interactor.symbol.like(f'{search_term}%')
    )

    number_of_results = query.count()
    limit = int(ra.get('page_size', 1))
    page = int(ra.get('page', 10))
    offset = (page - 1) * limit
    offset = offset if offset <= 100 else 100
    query = query.limit(limit).offset(offset)
    pages = ceil(number_of_results / limit)

    return {
        'page': page,
        'page_size': limit,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': [x.as_dict() for x in query.all()]
    }
