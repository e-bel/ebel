
from pathlib import Path
from ebel.manager.neo4j.n4j_meta import Neo4jClient
from ebel.manager.neo4j.bel import Neo4jBel

sherpa_json = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/bel-files/Sherpa/total_sherpa_results_cleaned.bel.json"
gpt4 = "c:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/bel-files/gpt4/common_triples_5trials/normalized/gpt4_fixed_cleaned.bel.json"
gpt35 = "c:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/bel-files/gpt3.5-turbo/common_triples_5trials/normalized/gpt35_fixed_cleaned.bel.json"
tau_KG = "C:/Users/nbabaiha/Documents/GitHub/chatgpt-paper/bel-files/initil-tau-graph/taukg_cleaned.bel.json"

neo = Neo4jClient(uri="bolt://localhost:7687", database="neo4j", user="neo4j", password="12345678")
#print(neo.session.run("MATCH (n) RETURN n").data())

n4jbel = Neo4jBel(client=neo)
n4jbel.import_json([gpt35,gpt4], update_from_protein2gene=False)
#n4jbel.import_json([tau_KG, sherpa_json, common_triples_gpt4_json, common_triples_gpt3])
print("Done")