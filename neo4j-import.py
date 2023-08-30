
from pathlib import Path

from ebel.manager.neo4j.n4j_meta import Neo4jClient
from ebel.manager.neo4j.bel import Neo4jBel

sherpa_json = "C:\\Users\\nbabaiha\\Documents\\GitHub\\chatgpt-paper\\bel-files\\Sherpa\\total_sherpa_results_cleaned.bel.json"
gpt3_5_json = "C:\\Users\\nbabaiha\\Documents\\GitHub\\chatgpt-paper\\bel-files\\gpt3.5-turbo\\gpt3.5-prompt2-set1-trial1_cleaned.bel.json"


neo = Neo4jClient(uri="bolt://localhost:7687", database="neo4j", user="neo4j", password="12345678")
# print(neo.session.run("MATCH (n) RETURN n").data())

n4jbel = Neo4jBel(client=neo)


n4jbel.import_json([sherpa_json, gpt3_5_json])
print("Done")