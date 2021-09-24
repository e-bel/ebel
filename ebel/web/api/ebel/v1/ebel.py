"""Generic e(BE:L) API methods."""
import json
import numpy as np
import pandas as pd

from flask import request
from collections import Counter

from ebel import Bel
from ebel.web.api import RDBMS
from ebel.manager.rdbms.models.uniprot import Uniprot


def get_bel_edge_statistics_by_uniprot_accession():
    """Get edge statatistics by UniProt accession number. 'has__' edges are excluded."""
    query_object = json.loads(request.data)
    acc = query_object['uniprot_accession']
    eclass = query_object['edge_class']
    results = {}
    for direction in ('out', 'in'):
        results[direction] = __get_bel_edge_statistics_by_uniprot_accession(acc, eclass, direction)

    return results


def __get_bel_edge_statistics_by_uniprot_accession(acc, eclass, direction):
    sql_direction = {'out': ('out', 'in'), 'in': ('in', 'out')}

    sql = "match {class:protein, where:(uniprot='%s')}.%sE()" % (acc, sql_direction[direction][0])
    sql += "{class:%s, as:e,where:(not @class like 'has__%%')}.%sV(){as:o}" % (eclass, sql_direction[direction][1])
    sql += " return e.@class.asString() as eclass, e.@rid.asString() as erid, o.@class as oclass, " \
           "o.@rid.asString() as orid"

    rows = [x.oRecordData for x in Bel().client.command(sql)]
    edge_counter = Counter([x['eclass'] for x in rows])
    edge_counter_sorted = sorted(edge_counter.items(), key=lambda item: item[1], reverse=True)
    edge_counter_ordered = [{'name': x[0], 'value': x[1]} for x in edge_counter_sorted]
    # make object unique
    object_rid_class_dict = {x['orid']: x['oclass'] for x in rows}
    counter = Counter(object_rid_class_dict.values())
    object_counter_ordered = [{'name': x[0], 'value': x[1]} for x in
                              sorted(counter.items(), key=lambda i: i[1], reverse=True)]
    return {'edges': edge_counter_ordered, 'objects': object_counter_ordered}


def _describe(s: pd.Series):
    return {k: (int(v) if isinstance(v, np.int64) else v) for k, v in s.describe().to_dict().items()}


def get_intact_by_uniprot():
    """Get IntAct entries by UniProt ID."""
    query_object = json.loads(request.data)
    columns = ["name", "recommended_name", "accession", "detection_method", "interaction_type", "confidence_value",
               "pmid"]
    acc = query_object['uniprot_accession']
    sql = f"""(Select u.name, u.recommended_name, i.int_b_uniprot_id, i.detection_method,
     i.interaction_type, i.confidence_value, CAST(i.pmid AS CHAR) from intact i inner join uniprot u on
     (u.accession=i.int_b_uniprot_id) where
     i.int_a_uniprot_id = '{acc}') union
     (Select u.name,u.recommended_name, i.int_a_uniprot_id as uniprot_interaction_partner, i.detection_method,
     i.interaction_type, i.confidence_value, CAST(i.pmid AS CHAR) from intact i inner join uniprot u on
     (u.accession=i.int_a_uniprot_id) where i.int_b_uniprot_id = '{acc}') order by confidence_value desc"""
    df = pd.DataFrame(RDBMS.get_session().execute(sql), columns=columns)
    # rows = [dict(zip(columns, row)) for row in ]
    # statistics_name_10 = Counter([x['name'] for x in rows]).most_common(10)

    r = {
        'rows': df.to_dict('records'),
        'total': df.shape[0],
        'statistics': {
            'confidence_value': _describe(df.confidence_value),
            'name': _describe(df.name),
            'pmid': _describe(df.pmid),
            'detection_method': _describe(df.detection_method),
            'interaction_type': _describe(df.interaction_type),
        }
    }
    return r


def find_all():
    """Get all UniProt entries."""
    term = json.loads(request.data)['term'].strip()
    uniprot_entries = RDBMS.get_session().query(Uniprot.recommended_name).filter(
        Uniprot.recommended_name.like("%" + term + "%")).count()
    return uniprot_entries
