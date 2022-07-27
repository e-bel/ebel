"""CHEBI API methods."""
from math import ceil
from flask import request

from ebel import Bel
from ebel.web.api import RDBMS
from ebel.manager.rdbms.models import chebi
from . import _get_pagination


def get_compound_by_name(name: str):
    """Get CHEBI compound information based given name.

    Parameters
    ----------
    name: str
        Compound name.

    Returns
    -------
    dict
        CHEBI compound information.
    """
    return [x.as_dict() for x in RDBMS.get_session().query(chebi.Compound).filter_by(name=name).all()]


def get_compound_name_by_name_starts_with(name: str):
    """Get CHEBI compound name based on fuzzy given value.

    Parameters
    ----------
    name: str
        Beginning of compound name.

    Returns
    -------
    dict
        Names and CHEBI IDs.
    """
    query = RDBMS.get_session().query(
        chebi.Compound.id, chebi.Compound.name
    ).filter(
        chebi.Compound.name.like(f"{name}%")
    )
    return {x.name: x.id for x in query.all()}


def get_compound_by_id(id: int):
    """Get compound by CHEBI ID.

    Parameters
    ----------
    chebi_id: int
        CHEBI ID.

    Returns
    -------
    dict
        Compound information.
    """
    return RDBMS.get_session().query(chebi.Compound).filter_by(id=id).first().as_dict()


def get_compound_by_other_db_accession(accession_number: str, db_name: str = None):
    """Get a compound's information based on accession number.

    Parameters
    ----------
    accession_number: str
        Accession number.
    db_name: str
        Name of database where accession number was derived.

    Returns
    -------
    list
        List of dictionaries of compounds matching accession number.
    """
    query_filter = []
    query_filter.append(chebi.DatabaseAccession.accession_number == accession_number)
    if db_name:
        query_filter.append(chebi.DatabaseAccession.type == db_name)
    chebi_ids_rs = RDBMS.get_session().query(chebi.DatabaseAccession.compound_id).filter(*query_filter).all()
    chebi_ids = {x[0] for x in chebi_ids_rs}
    return [
        x.as_dict() for x in RDBMS.get_session().query(chebi.Compound).filter(chebi.Compound.id.in_(chebi_ids)).all()
    ]


def get_compound_reference():
    """Compile a dictionary of information for a given compound."""
    req = dict(request.args.copy())
    page_size = req.pop('page_size', 10)
    page = req.pop('page', 1)
    if not req:
        return {'error': "At least one of the parameters have to be filled."}
    query = RDBMS.get_session().query(chebi.Reference).filter_by(**req)
    number_of_results = query.count()

    limit = int(page_size)
    page = int(page)
    offset = (page - 1) * limit
    offset = offset if offset <= 100 else 100
    query = query.limit(limit).offset(offset)
    pages = ceil(number_of_results / limit)

    return {
        'page': page,
        'page_size': limit,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': [x.as_dict_with_compound_id() for x in query.all()]
    }


def get_relation():
    """Get CHEBI defined relations."""
    if not (bool(request.args.get('final_id') or bool(request.args.get('init_id')))):
        return {'error': "At least final_id or init_id have to be filled."}
    rs = RDBMS.get_session().query(chebi.Relation).filter_by(**request.args).all()
    return [x.as_dict() for x in rs]


def get_bel_chebi_ids():
    """Get BEL nodes with the CHEBI namespace."""
    b = Bel()
    sql_count = "SELECT count(*) FROM V where chebi IS NOT NULL"
    p = _get_pagination()
    number_of_results = b.query_get_dict(sql_count)[0]['count']
    pages = ceil(number_of_results / p.page_size)
    query = "SELECT @rid.asString(), namespace, name, chebi, bel FROM V where chebi IS NOT NULL"
    paras = {k: v for k, v in dict(request.args.copy()).items() if k in ['namespace', 'name', 'chebi']}
    if paras:
        query += " AND " + ' AND '.join([f"{k} like '{v.strip()}'" for k, v in paras.items()])

    print(query)
    return {
        'page': p.page,
        'page_size': p.page_size,
        'number_of_results': number_of_results,
        'pages': pages,
        'results': b.query_get_dict(f"{query} LIMIT {p.page_size} SKIP {p.skip}")
    }
