# comments

- grégoire: useless
- neo4j:

	- `MATCH (a:User {username: 'u1'}), (b:User {username: 'u2'}) MERGE (a)-[r:COMMENTED {weight: 1}]->(b) ON CREATE SET r.weight = 1 ON MATCH SET r.weight = r.weight + 100` creates a new in most cases, since no match.
	- check with `MATCH (a:User)-[r:COMMENTED]->(b:User)<-[g:COMMENTED]-(a:User) RETURN a` 
	- fix by removing weight in rltshp