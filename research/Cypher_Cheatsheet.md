# Cypher Cheatsheet for Neo4j

Quick reference for Neo4j Cypher queries used with Fers knowledge graph.

---

## 📋 Quick Reference (Practical Queries)

### Chunk Info with Metadata
```cypher
MATCH (c:Chunk)
WHERE c.source_file_name IS NOT NULL
WITH c.source_file_name as file, c
ORDER BY c.chunk_index
WITH file, collect(c)[0..5] as chunks
UNWIND chunks as chunk
RETURN file, chunk.chunk_index, chunk.text
```

### Vector Similarity Search with Score
```cypher
MATCH (q:Question {text: "What are the most touristic countries in the world?"})
CALL db.index.vector.queryNodes('questions', 6, q.embedding)
YIELD node, score
RETURN node.text, score
```

### Unique Source Files from Chunks
```cypher
MATCH (c:Chunk)
WHERE c.source_file_path IS NOT NULL
RETURN DISTINCT c.source_file_path as file_path,
       c.source_file_name as filename,
       count(*) as chunks
ORDER BY chunks DESC
```

### Draw Complete Graph (Limited)
```cypher
// Use LIMIT to avoid browser crash on large graphs
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 500
```

### Calculate Relationship Types
```cypher
MATCH ()-[r]->()
RETURN type(r) AS rel_type, count(*) AS count
ORDER BY count DESC
LIMIT 50
```

### Delete Specific Document by Source
```cypher
MATCH (d:Document)
WHERE d.source CONTAINS 'MyDocument.pptx'
DETACH DELETE d
```

### Set Topic Manually to Source
```cypher
MATCH (c:Chunk)
WHERE c.source_file_name = "MyDocument.pdf"
SET c.topics = CASE
    WHEN c.topics IS NULL THEN ["MyTopic"]
    WHEN NOT "MyTopic" IN c.topics THEN c.topics + "MyTopic"
    ELSE c.topics
END
RETURN count(c) as updated_chunks
```

---

## 🧹 Database Cleanup

### Delete Everything (Nuclear Option)
```cypher
// Delete all nodes and relationships
MATCH (n) DETACH DELETE n
---

## 📊 Inspection & Counts

### Count Relationships by Type
```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(*) AS count
ORDER BY count DESC
```

### List All Tags
```cypher
MATCH (t:Tag)
RETURN t.name, t.value
ORDER BY t.name
```

### List All Entities
```cypher
MATCH (e:Entity)
RETURN e.name, e.type, e.value
ORDER BY e.type, e.name
```

---

## 🔍 Search & Query

### Find Document by Path
```cypher
MATCH (d:Document {path: 'docs/03-business/business-plan/Business-Plan-Fers.md'})
RETURN d
```

### Find Chunks for a Document
```cypher
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
WHERE d.path CONTAINS 'Business-Plan'
RETURN d.path, c.header, c.content
ORDER BY c.position
```

### Find Documents with Specific Tag
```cypher
MATCH (d:Document)-[:HAS_TAG]->(t:Tag {name: 'funding_target'})
RETURN d.path, t.value
```

### Find Documents Sharing a Tag
```cypher
MATCH (d1:Document)-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(d2:Document)
WHERE d1 <> d2
RETURN d1.path, t.name, d2.path
```

### Full-Text Search in Chunks
```cypher
MATCH (c:Chunk)
WHERE c.content CONTAINS 'platform subscription'
RETURN c.header, c.content
LIMIT 10
```

### Semantic Search (Vector Index)
```cypher
// Requires vector index on Chunk.embedding
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $queryVector)
YIELD node, score
RETURN node.header, node.content, score
```

---

## 🔗 Relationship Queries

### Document → Chunks → Entities
```cypher
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
WHERE d.path CONTAINS 'Financial'
RETURN d.path, c.header, collect(e.name) AS entities
```

### Find All Connections of a Document
```cypher
MATCH (d:Document {path: 'docs/05-financial/Financial-Model-Fers.md'})-[r]-(connected)
RETURN type(r) AS relationship, labels(connected)[0] AS nodeType,
       COALESCE(connected.name, connected.path, connected.header) AS identifier
```

### Tag Propagation (Find Downstream)
```cypher
MATCH (source:Document {path: $sourcePath})-[:HAS_TAG]->(t:Tag)<-[:HAS_TAG]-(downstream:Document)
WHERE source <> downstream
RETURN t.name, collect(downstream.path) AS affectedDocuments
```

---

## ✏️ Create & Update

### Create Document Node
```cypher
CREATE (d:Document {
  path: 'docs/new-document.md',
  title: 'New Document',
  hash: 'abc123',
  created: datetime()
})
RETURN d
```

### Create Tag and Link to Document
```cypher
MATCH (d:Document {path: 'docs/some-doc.md'})
MERGE (t:Tag {name: 'seed_target', value: '€500,000'})
MERGE (d)-[:HAS_TAG]->(t)
RETURN d, t
```

### Update Tag Value
```cypher
MATCH (t:Tag {name: 'seed_target'})
SET t.value = '€600,000', t.updated = datetime()
RETURN t
```

### Create Entity
```cypher
MERGE (e:Entity {name: 'NVIDIA Jetson Orin', type: 'COMPONENT'})
SET e.value = 'Primary compute platform'
RETURN e
```

### Link Chunk to Entity
```cypher
MATCH (c:Chunk {header: 'Product Specifications'})
MATCH (e:Entity {name: 'NVIDIA Jetson Orin'})
MERGE (c)-[:MENTIONS]->(e)
```

---

## 🔄 MergeRequest Management

### List Pending Merge Requests
```cypher
MATCH (m:MergeRequest {status: 'pending'})
RETURN m.id, m.source_document, m.affected_tag, m.old_value, m.new_value, m.reason
ORDER BY m.created DESC
```

### Approve Merge Request
```cypher
MATCH (m:MergeRequest {id: $mergeId})
SET m.status = 'approved', m.approved_at = datetime()
RETURN m
```

### Find Documents Affected by Merge
```cypher
MATCH (m:MergeRequest {id: $mergeId})-[:AFFECTS]->(d:Document)
RETURN d.path
```

---

## 🛠️ Schema & Index Management

### List All Indexes
```cypher
SHOW INDEXES
```

### Create Vector Index (for Embeddings)
```cypher
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}}
```

### Create Text Index
```cypher
CREATE TEXT INDEX document_path IF NOT EXISTS
FOR (d:Document) ON (d.path)
```

### Create Constraint (Unique)
```cypher
CREATE CONSTRAINT document_path_unique IF NOT EXISTS
FOR (d:Document) REQUIRE d.path IS UNIQUE
```

### Drop Index
```cypher
DROP INDEX chunk_embeddings IF EXISTS
```

---

## 📈 Analytics

### Documents by Tag Count
```cypher
MATCH (d:Document)-[:HAS_TAG]->(t:Tag)
RETURN d.path, count(t) AS tagCount
ORDER BY tagCount DESC
```

### Most Connected Entities
```cypher
MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk)
RETURN e.name, e.type, count(c) AS mentions
ORDER BY mentions DESC
LIMIT 20
```

### Tag Co-occurrence
```cypher
MATCH (d:Document)-[:HAS_TAG]->(t1:Tag)
MATCH (d)-[:HAS_TAG]->(t2:Tag)
WHERE t1 <> t2
RETURN t1.name, t2.name, count(d) AS cooccurrence
ORDER BY cooccurrence DESC
LIMIT 20
```

### Orphan Tags (Not Used)
```cypher
MATCH (t:Tag)
WHERE NOT (t)<-[:HAS_TAG]-()
RETURN t.name, t.value
```

---

## 🚀 Fers-Specific Queries

### Find All Financial Figures
```cypher
MATCH (e:Entity)
WHERE e.type IN ['CURRENCY', 'FINANCIAL', 'METRIC']
RETURN e.name, e.value, e.type
ORDER BY e.type, e.name
```

### Find Product Specifications
```cypher
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
WHERE c.header CONTAINS 'Specification' OR c.header CONTAINS 'Product'
RETURN c.header, collect(DISTINCT e.name) AS specs
```

### Trace Value Across Documents
```cypher
// Find where '€500,000' appears
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
WHERE c.content CONTAINS '€500,000'
RETURN d.path, c.header
```

### Find Inconsistent Values
```cypher
// Tags with same name but different values
MATCH (t1:Tag), (t2:Tag)
WHERE t1.name = t2.name AND t1.value <> t2.value
RETURN t1.name, t1.value, t2.value
```

---

## 💡 Tips

1. **Always use `DETACH DELETE`** when deleting nodes with relationships
2. **Use `MERGE` instead of `CREATE`** to avoid duplicates
3. **Profile queries** with `PROFILE` prefix to see execution plan
4. **Use parameters** (`$paramName`) for dynamic values in production
5. **Batch large deletes** to avoid memory issues:
   ```cypher
   CALL apoc.periodic.iterate(
     'MATCH (n:Chunk) RETURN n',
     'DETACH DELETE n',
     {batchSize: 1000}
   )
   ```

---

*Last updated: 2026-01-28*
