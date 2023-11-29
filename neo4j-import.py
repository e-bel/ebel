
from pathlib import Path
from ebel.manager.neo4j.n4j_meta import Neo4jClient
from ebel.manager.neo4j.bel import Neo4jBel

sherpa = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/neo4j-json-files/abstract/sherpa.json"
gpt4 = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/neo4j-json-files/abstract/gpt4.json"
gpt35 = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/neo4j-json-files/abstract/gpt35.json"
tau = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/neo4j-json-files/abstract/tau_modified.json"

# sherpa = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/neo4j-json-files/full-text/sherpa.json"
# gpt4 = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/neo4j-json-files/full-text/gpt4.json"
# gpt35 = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/neo4j-json-files/full-text/gpt35.json"
# tau = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/neo4j-json-files/full-text/tau_modified.json"

neo = Neo4jClient(uri="bolt://localhost:7687", database="neo4j", user="neo4j", password="12345678")
#print("test", neo.session.run("MATCH (n) RETURN n").data())

n4jbel = Neo4jBel(client=neo)
n4jbel.import_json([sherpa, tau, gpt35, gpt4], update_from_protein2gene=False)
#n4jbel.import_json([tau_KG, sherpa_json, common_triples_gpt4_json, common_triples_gpt3])
print("Done")