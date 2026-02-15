"""
Fers Smart Core MCP Server
===========================
Knowledge graph pipeline for project documents.
Claude handles all semantic analysis; server handles chunking, embeddings, storage, retrieval.

Tools: ping, load_project, synchronize_project, merge_report, approve_merge, knowledge_call, store_extraction, commit_changes, get_commit_history
"""

import hashlib
import json
import logging
import re
import traceback
import uuid
import yaml
from pathlib import Path

from mcp.server.fastmcp import FastMCP
# Lazy imports to avoid slow startup (sentence-transformers pulls tensorflow)
import time as _time
GraphDatabase = None
SentenceTransformer = None

def _import_neo4j():
    """Import Neo4j driver only — fast, no ML dependencies."""
    global GraphDatabase
    if GraphDatabase is None:
        log.info("[Smart Core] Loading Neo4j driver...")
        from neo4j import GraphDatabase as _GD
        GraphDatabase = _GD
        log.info("[Smart Core] Neo4j driver ready.")

def _import_embeddings():
    """Import sentence-transformers — slow, loads PyTorch. Only needed for vector search."""
    global SentenceTransformer
    if SentenceTransformer is None:
        # Suppress all ML framework logging before import
        import warnings
        warnings.filterwarnings('ignore')
        import logging as _logging
        _logging.getLogger('transformers').setLevel(_logging.ERROR)
        _logging.getLogger('sentence_transformers').setLevel(_logging.ERROR)

        log.info("[Smart Core] Loading sentence-transformers (this takes 10-20s on first call)...")
        from sentence_transformers import SentenceTransformer as _ST
        SentenceTransformer = _ST
        log.info("[Smart Core] sentence-transformers loaded.")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "config.json"

# Load and validate config
try:
    with open(CONFIG_PATH) as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print(f"ERROR: config.json not found at {CONFIG_PATH}")
    print("Create config.json from template with database credentials.")
    import sys
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON in config.json: {e}")
    import sys
    sys.exit(1)

# Validate required config keys
required_keys = {
    "database": ["uri", "user", "password", "name"],
    "embedding": ["model", "dimensions"],
    "processing": ["chunk_max_tokens", "project_docs_path"]
}

for section, keys in required_keys.items():
    if section not in CONFIG:
        print(f"ERROR: Missing required config section: '{section}'")
        import sys
        sys.exit(1)
    for key in keys:
        if key not in CONFIG[section]:
            print(f"ERROR: Missing required config key: '{section}.{key}'")
            import sys
            sys.exit(1)

# Priority: ENV vars > CLI args > config.json
import argparse
import os

_parser = argparse.ArgumentParser()
_parser.add_argument("--db-uri", default=None)
_parser.add_argument("--db-user", default=None)
_parser.add_argument("--db-password", default=None)
_parser.add_argument("--db-name", default=None)
_args, _ = _parser.parse_known_args()

DB = CONFIG["database"]

# Environment variables take priority (secure)
if os.getenv("DB_URI"):
    DB["uri"] = os.getenv("DB_URI")
elif _args.db_uri:
    DB["uri"] = _args.db_uri

if os.getenv("DB_USER"):
    DB["user"] = os.getenv("DB_USER")
elif _args.db_user:
    DB["user"] = _args.db_user

if os.getenv("DB_PASSWORD"):
    DB["password"] = os.getenv("DB_PASSWORD")
elif _args.db_password:
    DB["password"] = _args.db_password

if os.getenv("DB_NAME"):
    DB["name"] = os.getenv("DB_NAME")
elif _args.db_name:
    DB["name"] = _args.db_name

EMB_CFG = CONFIG["embedding"]
PROC = CONFIG["processing"]

# Safety limits
MAX_FILE_SIZE_MB = 10  # Skip files larger than 10MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("smart-core-mcp")

# Suppress Neo4j driver logging to prevent stdout pollution in stdio mode
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("neo4j.bolt").setLevel(logging.WARNING)
logging.getLogger("neo4j.io").setLevel(logging.WARNING)

# Suppress TensorFlow/PyTorch logging (critical for stdio MCP)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow C++ logs
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN messages
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('transformers').setLevel(logging.ERROR)

# ---------------------------------------------------------------------------
# Globals (initialized lazily)
# ---------------------------------------------------------------------------

_driver = None
_model = None


def get_driver():
    global _driver
    if _driver is None:
        _import_neo4j()
        # Configure timeouts to prevent hanging
        _driver = GraphDatabase.driver(
            DB["uri"],
            auth=(DB["user"], DB["password"]),
            connection_timeout=5.0,  # 5 second connection timeout
            max_connection_lifetime=3600,  # 1 hour max connection lifetime
            connection_acquisition_timeout=10.0  # 10 second timeout to acquire connection from pool
        )
        log.info("[Smart Core] Neo4j driver initialized with timeouts")
    return _driver


def get_model():
    global _model
    if _model is None:
        _import_neo4j()
        _import_embeddings()
        log.info("[Smart Core] Loading embedding model '%s' ...", EMB_CFG["model"])
        t0 = _time.time()
        _model = SentenceTransformer(EMB_CFG["model"])
        log.info("[Smart Core] Embedding model ready (%.1fs)", _time.time() - t0)
    return _model


def _session():
    # Note: Query timeouts must be configured at Neo4j server level
    # via dbms.transaction.timeout setting (default 30s)
    return get_driver().session(database=DB["name"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _parse_front_matter(text: str) -> tuple[dict, str]:
    """Extract YAML front matter from markdown. Returns (metadata_dict, body_text)."""
    fm_re = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = fm_re.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, text
    body = text[match.end():]
    return meta, body


def _chunk_markdown(text: str, max_tokens: int = PROC["chunk_max_tokens"]) -> list[dict]:
    """Split markdown by headers. Each chunk has section_header and text."""
    header_re = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    splits = list(header_re.finditer(text))

    chunks = []
    if not splits:
        # No headers — single chunk
        chunks.append({"section_header": "", "text": text.strip(), "position": 0})
        return chunks

    # Content before first header
    pre = text[: splits[0].start()].strip()
    if pre:
        chunks.append({"section_header": "(preamble)", "text": pre, "position": 0})

    for i, m in enumerate(splits):
        start = m.start()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
        section = text[start:end].strip()
        header = m.group(2).strip()

        # Sub-chunk if too long (rough token estimate: chars / 4)
        if len(section) / 4 > max_tokens:
            lines = section.split("\n")
            buf, buf_header = [], header
            for line in lines:
                buf.append(line)
                if len("\n".join(buf)) / 4 > max_tokens:
                    chunks.append({
                        "section_header": buf_header,
                        "text": "\n".join(buf).strip(),
                        "position": len(chunks),
                    })
                    buf = []
                    buf_header = header + " (cont.)"
            if buf:
                chunks.append({
                    "section_header": buf_header,
                    "text": "\n".join(buf).strip(),
                    "position": len(chunks),
                })
        else:
            chunks.append({"section_header": header, "text": section, "position": len(chunks)})

    # Reindex positions
    for i, c in enumerate(chunks):
        c["position"] = i

    return chunks


def _embed(texts: list[str]) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return [e.tolist() for e in embeddings]


def _ensure_vector_index():
    """Create Neo4j vector index on Chunk.embedding if not exists."""
    with _session() as s:
        s.run("""
            CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: $dims,
                `vector.similarity_function`: 'cosine'
            }}
        """, dims=EMB_CFG["dimensions"])


def _ensure_schema():
    """Create constraints and indexes."""
    with _session() as s:
        for q in [
            "CREATE CONSTRAINT doc_path IF NOT EXISTS FOR (d:Document) REQUIRE d.path IS UNIQUE",
            "CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT entity_name_type IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE",
            "CREATE CONSTRAINT merge_id IF NOT EXISTS FOR (m:MergeRequest) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT commit_id IF NOT EXISTS FOR (c:Commit) REQUIRE c.commit_id IS UNIQUE",
            "CREATE CONSTRAINT change_id IF NOT EXISTS FOR (c:Change) REQUIRE c.change_id IS UNIQUE",
        ]:
            try:
                s.run(q)
            except Exception:
                pass
    _ensure_vector_index()


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP("smart-core", instructions="Fers knowledge graph pipeline. Call ping first to check Neo4j status. Then use load_project, store_extraction, synchronize_project, merge_report, knowledge_call. After editing docs, use commit_changes to record history. Use get_commit_history to query changes.")


@mcp.tool()
def hello() -> str:
    """Simple test tool that returns hello - used for debugging MCP communication."""
    return json.dumps({"status": "ok", "message": "Hello from Smart Core MCP!"})


@mcp.tool()
def ping() -> str:
    """
    Check if Neo4j database is reachable and responsive.

    **WHEN TO USE:** Call this FIRST at session start, before any other Smart Core tool.
    If Neo4j is down, skip all MCP tools and work with files directly.

    **RETURNS:**
    - status: "ok" → Neo4j is up, proceed with other tools
    - status: "down" → Neo4j unavailable, use file-based operations instead
    """
    try:
        with _session() as s:
            result = s.run("RETURN 1 AS n").single()
            if result and result["n"] == 1:
                return json.dumps({"status": "ok", "database": DB["name"], "uri": DB["uri"]})
        return json.dumps({"status": "down", "reason": "Query failed"})
    except Exception as e:
        error_msg = str(e)
        # Provide helpful error messages
        if "refused" in error_msg.lower():
            error_msg = "Connection refused - is Neo4j running?"
        elif "timeout" in error_msg.lower():
            error_msg = "Connection timeout - check Neo4j address and network"
        elif "authentication" in error_msg.lower():
            error_msg = "Authentication failed - check username/password"
        log.error("Neo4j ping failed: %s", error_msg)
        return json.dumps({"status": "down", "reason": error_msg})


@mcp.tool()
def load_project(project_path: str = "", force_reload: bool = False) -> str:
    """
    Ingest project documents into the knowledge graph.

    **WHEN TO USE:**
    - After creating new documents in docs_ver2/
    - After editing existing documents (only changed files are re-processed)
    - Initial setup to populate the graph

    **WHAT IT DOES:**
    - Scans all .md files in docs_ver2/
    - Parses YAML front matter and markdown structure
    - Chunks documents by headers
    - Generates semantic embeddings
    - Stores in Neo4j with relationships

    **ARGS:**
    - project_path: Root project path (default: auto-detect)
    - force_reload: Re-process all files even if unchanged (default: false)

    **RETURNS:** Document list with chunk counts and section headers
    """
    root = Path(project_path) if project_path else Path(CONFIG_PATH).parent.parent.parent
    docs_dir = root / PROC["project_docs_path"]

    if not docs_dir.exists():
        return json.dumps({"error": f"docs directory not found: {docs_dir}"})

    _ensure_schema()

    md_files = sorted(docs_dir.rglob("*.md"))
    results = []
    doc_meta_map = {}  # rel_path -> front matter dict (for relationship creation)

    for fp in md_files:
        rel = str(fp.relative_to(root))

        # Check file size before reading
        file_size = fp.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            log.warning("Skipping large file: %s (%.1f MB > %d MB limit)",
                       rel, file_size / 1024 / 1024, MAX_FILE_SIZE_MB)
            results.append({
                "path": rel,
                "status": "skipped",
                "reason": f"file_too_large ({file_size / 1024 / 1024:.1f}MB)"
            })
            continue

        text = fp.read_text(encoding="utf-8", errors="replace")
        h = _content_hash(text)

        # Check if already loaded with same hash
        with _session() as s:
            existing = s.run(
                "MATCH (d:Document {path: $p}) RETURN d.content_hash AS h", p=rel
            ).single()
            if not force_reload and existing and existing["h"] == h:
                results.append({"path": rel, "status": "unchanged", "chunks": 0})
                continue

        try:
            meta, _ = _parse_front_matter(text)  # body not used, we chunk full text
            chunks = _chunk_markdown(text)
            texts = [c["text"] for c in chunks]
            embeddings = _embed(texts)
        except Exception as e:
            log.error("Failed to process %s: %s\n%s", rel, e, traceback.format_exc())
            results.append({
                "path": rel,
                "status": "error",
                "reason": str(e)
            })
            continue

        # Flatten front matter for Document node properties
        fm_props = {}
        for key in ("doc_id", "title", "version", "last_updated", "status",
                     "domain", "phase", "owner"):
            if key in meta:
                fm_props[key] = str(meta[key])
        if "deputies" in meta and isinstance(meta["deputies"], list):
            fm_props["deputies"] = ", ".join(str(d) for d in meta["deputies"])
        if "tags" in meta and isinstance(meta["tags"], list):
            fm_props["tags_yaml"] = ", ".join(str(t) for t in meta["tags"])
        if "depends_on" in meta and isinstance(meta["depends_on"], list):
            fm_props["depends_on"] = ", ".join(str(d) for d in meta["depends_on"])
        if "feeds_into" in meta and isinstance(meta["feeds_into"], list):
            fm_props["feeds_into"] = ", ".join(str(f) for f in meta["feeds_into"])

        with _session() as s:
            # Upsert document with front matter metadata
            s.run("""
                MERGE (d:Document {path: $path})
                SET d.name = $name, d.folder = $folder, d.content_hash = $hash,
                    d.updated = datetime(), d.chunk_count = $cc
                SET d += $fm_props
            """, path=rel, name=fp.name, folder=str(fp.parent.relative_to(root)),
                 hash=h, cc=len(chunks), fm_props=fm_props)

            # Remove old chunks
            s.run("MATCH (d:Document {path: $p})-[:CONTAINS]->(c:Chunk) DETACH DELETE c", p=rel)

            # Create new chunks
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{rel}::{i}"
                s.run("""
                    MATCH (d:Document {path: $path})
                    CREATE (c:Chunk {id: $cid, text: $text, position: $pos,
                                     section_header: $header, embedding: $emb})
                    CREATE (d)-[:CONTAINS]->(c)
                """, path=rel, cid=chunk_id, text=chunk["text"], pos=chunk["position"],
                     header=chunk["section_header"], emb=emb)

        doc_meta_map[rel] = meta
        sections = [c["section_header"] for c in chunks]
        results.append({"path": rel, "status": "loaded", "chunks": len(chunks), "sections": sections})

    # --- Build inter-document relationships from YAML front matter ---
    # Build doc_id -> path lookup
    docid_to_path = {}
    with _session() as s:
        for row in s.run("MATCH (d:Document) WHERE d.doc_id IS NOT NULL RETURN d.doc_id AS did, d.path AS path"):
            docid_to_path[row["did"]] = row["path"]

    rel_count = 0
    with _session() as s:
        for rel_path, meta in doc_meta_map.items():
            # DEPENDS_ON: this doc depends on listed doc_ids
            for dep_id in (meta.get("depends_on") or []):
                dep_id = str(dep_id)
                target = docid_to_path.get(dep_id)
                if target:
                    s.run("""
                        MATCH (a:Document {path: $src}), (b:Document {path: $tgt})
                        MERGE (a)-[:DEPENDS_ON]->(b)
                    """, src=rel_path, tgt=target)
                    rel_count += 1

            # RESULTS_FROM: feeds_into means this doc results feed into listed doc_ids
            # Reverse: if A feeds_into B, then B RESULTS_FROM A
            for feed_id in (meta.get("feeds_into") or []):
                feed_id = str(feed_id)
                target = docid_to_path.get(feed_id)
                if target:
                    s.run("""
                        MATCH (a:Document {path: $src}), (b:Document {path: $tgt})
                        MERGE (b)-[:RESULTS_FROM]->(a)
                    """, src=rel_path, tgt=target)
                    rel_count += 1

            # BELONGS_TO phase (as a node)
            phase = meta.get("phase")
            if phase:
                s.run("""
                    MATCH (d:Document {path: $path})
                    MERGE (p:Phase {name: $phase})
                    MERGE (d)-[:BELONGS_TO]->(p)
                """, path=rel_path, phase=str(phase))
                rel_count += 1

            # BELONGS_TO domain (as a node)
            domain = meta.get("domain")
            if domain:
                s.run("""
                    MATCH (d:Document {path: $path})
                    MERGE (dom:Domain {name: $domain})
                    MERGE (d)-[:BELONGS_TO]->(dom)
                """, path=rel_path, domain=str(domain))
                rel_count += 1

    return json.dumps({
        "documents_processed": len(results),
        "documents": results,
        "relationships_created": rel_count,
        "instruction": "Analyze each loaded document. For each, call store_extraction with entities and tags."
    })


@mcp.tool()
def store_extraction(document_path: str, entities: list[dict] = None, tags: list[str] = None) -> str:
    """
    Store extracted entities and tags for a document in the knowledge graph.

    **WHEN TO USE:** After load_project, to enrich documents with structured metadata.

    **WHAT IT DOES:**
    - Links entities to documents (creates Entity nodes + HAS_ENTITY relationships)
    - Links tags to documents (creates Tag nodes + HAS_TAG relationships)
    - Enables cross-document entity tracking

    **ARGS:**
    - document_path: Relative path to document (e.g., "docs_ver2/investor_package/PRD-001.md")
    - entities: List of {name, type, value} dicts (follow Entity-Extraction-Guide.md naming)
    - tags: List of tag strings

    **EXAMPLE:**
    entities = [
      {"name": "Round-Seed", "type": "Funding", "value": "€1,000,000"},
      {"name": "Prod-FersHumanoid", "type": "Product", "value": "Upper-body humanoid"}
    ]
    tags = ["Product", "Funding", "Phase-Seed"]

    **RETURNS:** Confirmation with entity and tag counts
    """
    entities = entities or []
    tags = tags or []

    # Validate entities structure
    for i, ent in enumerate(entities):
        if not isinstance(ent, dict):
            return json.dumps({"error": f"Entity {i} must be a dict, got {type(ent).__name__}"})
        if "name" not in ent or "type" not in ent:
            return json.dumps({"error": f"Entity {i} missing required fields 'name' and/or 'type': {ent}"})
        if not ent["name"] or not ent["type"]:
            return json.dumps({"error": f"Entity {i} has empty name or type: {ent}"})

    # Validate tags structure
    for i, tag in enumerate(tags):
        if not isinstance(tag, str):
            return json.dumps({"error": f"Tag {i} must be a string, got {type(tag).__name__}"})
        if not tag.strip():
            return json.dumps({"error": f"Tag {i} is empty or whitespace-only"})

    with _session() as s:
        # Verify document exists
        doc = s.run("MATCH (d:Document {path: $p}) RETURN d", p=document_path).single()
        if not doc:
            return json.dumps({"error": f"Document not found: {document_path}"})

        # Store entities
        for ent in entities:
            s.run("""
                MERGE (e:Entity {name: $name, type: $type})
                SET e.value = $value
                WITH e
                MATCH (d:Document {path: $path})
                MERGE (d)-[:HAS_ENTITY]->(e)
                MERGE (e)-[:ALSO_IN]->(d)
            """, name=ent["name"], type=ent["type"], value=ent.get("value", ""), path=document_path)

        # Store tag relationships
        for tag in tags:
            s.run("""
                MATCH (d:Document {path: $path})
                MERGE (t:Tag {name: $tag})
                MERGE (d)-[:HAS_TAG]->(t)
            """, path=document_path, tag=tag)

    return json.dumps({
        "document": document_path,
        "entities_stored": len(entities),
        "tags_linked": len(tags),
    })


@mcp.tool()
def synchronize_project(project_path: str = "") -> str:
    """
    Detect drift between local files and knowledge graph state.

    **WHEN TO USE:**
    - After manual file edits (outside of Claude)
    - Before major updates to verify consistency
    - Periodically to check graph health

    **WHAT IT DETECTS:**
    - New files not yet in graph
    - Modified files (hash mismatch)
    - Deleted files still in graph
    - Pending merge requests awaiting approval

    **ARGS:**
    - project_path: Root project path (default: auto-detect)

    **RETURNS:** Drift report with file changes and recommendations
    """
    root = Path(project_path) if project_path else Path(CONFIG_PATH).parent.parent.parent
    docs_dir = root / PROC["project_docs_path"]

    # Graph state
    with _session() as s:
        db_docs = {r["path"]: r["hash"] for r in s.run(
            "MATCH (d:Document) RETURN d.path AS path, d.content_hash AS hash"
        )}
        pending_merges = s.run("""
            MATCH (m:MergeRequest {status: 'pending_approval'})-[:TARGETS]->(d:Document)
            RETURN m.id AS id, m.reason AS reason, m.source_doc AS source, collect(d.path) AS targets
        """).data()

    # Local state
    local_docs = {}
    for fp in sorted(docs_dir.rglob("*.md")):
        rel = str(fp.relative_to(root))

        # Skip large files
        if fp.stat().st_size > MAX_FILE_SIZE_BYTES:
            log.warning("Skipping large file in sync: %s", rel)
            continue

        text = fp.read_text(encoding="utf-8", errors="replace")
        local_docs[rel] = _content_hash(text)

    # Diff
    new_files = [p for p in local_docs if p not in db_docs]
    deleted_files = [p for p in db_docs if p not in local_docs]
    modified_files = [p for p in local_docs if p in db_docs and local_docs[p] != db_docs[p]]
    unchanged_files = [p for p in local_docs if p in db_docs and local_docs[p] == db_docs[p]]

    # Ownership map for modified files (direct Neo4j queries)
    ownership = {}
    with _session() as s:
        for path in modified_files:
            # Get tags for this document
            tag_result = s.run("""
                MATCH (d:Document {path: $path})-[:HAS_TAG]->(t:Tag)
                RETURN t.name AS tag, t.canonical AS canonical
            """, path=path).data()
            owners = {r["tag"]: r["canonical"] for r in tag_result}
            ownership[path] = owners

    return json.dumps({
        "summary": {
            "total_local": len(local_docs),
            "total_db": len(db_docs),
            "new": len(new_files),
            "modified": len(modified_files),
            "deleted": len(deleted_files),
            "unchanged": len(unchanged_files),
            "pending_merges": len(pending_merges),
        },
        "new_files": new_files,
        "modified_files": modified_files,
        "deleted_files": deleted_files,
        "ownership": ownership,
        "pending_merges": pending_merges,
        "instructions": (
            "For new files: call load_project to ingest, then store_extraction. "
            "For modified files: check ownership — if this doc is canonical for affected tags, "
            "call load_project to re-ingest and create merge_reports for downstream docs. "
            "For deleted files: consider removing from graph. "
            "For pending merges: present to user for approval."
        ),
    })


@mcp.tool()
def merge_report(source_document: str, affected_tag: str, old_value: str, new_value: str, reason: str) -> str:
    """
    Create a change propagation request when an entity value changes.

    **WHEN TO USE:** When editing a document changes an entity value that appears in multiple docs.
    This creates a pending merge request that requires user approval before propagating.

    **WORKFLOW:**
    1. User edits document → entity value changes
    2. Call merge_report to create request
    3. System finds all downstream documents with same entity
    4. User approves/rejects via approve_merge
    5. If approved, Claude updates all affected documents

    **ARGS:**
    - source_document: Document where change originated
    - affected_tag: Entity name (e.g., "Round-Seed")
    - old_value: Previous value
    - new_value: New value
    - reason: Why the change was made

    **RETURNS:** Merge request ID and list of affected downstream documents
    """
    # Direct Neo4j queries instead of SmartCore
    with _session() as s:
        # Get documents with this tag
        doc_result = s.run("""
            MATCH (d:Document)-[:HAS_TAG]->(t:Tag {name: $tag})
            RETURN d.path AS path
        """, tag=affected_tag).data()
        affected_docs = [r["path"] for r in doc_result]

        # Get canonical source for this tag
        canon_result = s.run("""
            MATCH (t:Tag {name: $tag}) RETURN t.canonical AS canonical
        """, tag=affected_tag).single()
        canonical = canon_result["canonical"] if canon_result else None

    # Exclude source from targets
    targets = [d for d in affected_docs if d != source_document]

    merge_id = str(uuid.uuid4())[:8]
    changes = {"tag": affected_tag, "old": old_value, "new": new_value}

    with _session() as s:
        s.run("""
            CREATE (m:MergeRequest {
                id: $id, status: 'pending_approval', reason: $reason,
                changes_json: $changes, source_doc: $source, created: datetime()
            })
        """, id=merge_id, reason=reason, changes=json.dumps(changes), source=source_document)

        for doc in targets:
            s.run("""
                MATCH (m:MergeRequest {id: $mid})
                MATCH (d:Document {path: $dp})
                MERGE (m)-[:TARGETS]->(d)
            """, mid=merge_id, dp=doc)

    return json.dumps({
        "merge_id": merge_id,
        "status": "pending_approval",
        "source": source_document,
        "tag": affected_tag,
        "canonical_owner": canonical,
        "changes": changes,
        "affected_documents": targets,
        "instruction": f"Present this merge to the user. Canonical owner for '{affected_tag}' is '{canonical}'."
    })


@mcp.tool()
def approve_merge(merge_id: str) -> str:
    """
    Approve a pending merge request to propagate changes across documents.

    **WHEN TO USE:** After user reviews and approves changes from merge_report.

    **WORKFLOW:**
    1. merge_report creates pending request
    2. Claude asks user for approval
    3. User approves → call approve_merge
    4. Claude updates all affected documents

    **ARGS:**
    - merge_id: Merge request ID from merge_report (e.g., "m-2026-02-12-001")

    **RETURNS:** Approval confirmation and list of documents to update
    """
    with _session() as s:
        result = s.run(
            "MATCH (m:MergeRequest {id: $id}) RETURN m.status AS status, m.changes_json AS changes",
            id=merge_id
        ).single()

        if not result:
            return json.dumps({"error": f"MergeRequest {merge_id} not found"})
        if result["status"] != "pending_approval":
            return json.dumps({"error": f"MergeRequest {merge_id} is already {result['status']}"})

        s.run("""
            MATCH (m:MergeRequest {id: $id})
            SET m.status = 'approved', m.resolved = datetime()
        """, id=merge_id)

        targets = s.run("""
            MATCH (m:MergeRequest {id: $id})-[:TARGETS]->(d:Document)
            RETURN d.path AS path
        """, id=merge_id).data()

    return json.dumps({
        "merge_id": merge_id,
        "status": "approved",
        "changes": json.loads(result["changes"]),
        "target_documents": [t["path"] for t in targets],
        "instruction": "Update each target document with the approved changes."
    })


@mcp.tool()
def knowledge_call(query: str, search_type: str = "hybrid", limit: int = 10) -> str:
    """
    Search the knowledge graph using semantic similarity and/or graph relationships.

    **WHEN TO USE:**
    - Before answering questions about the project
    - Before editing documents (to find all related occurrences)
    - To find cross-document entities and dependencies

    **SEARCH TYPES:**
    - "vector" → Semantic search using embeddings (best for conceptual queries)
    - "graph" → Traverse tags/entities (best for exact entity matches)
    - "hybrid" → Both semantic + graph (default, most comprehensive)

    **ARGS:**
    - query: Natural language query or entity name (e.g., "Seed round funding" or "Round-Seed")
    - search_type: "vector" | "graph" | "hybrid" (default: "hybrid")
    - limit: Max results to return (default: 10, max: 100)

    **RETURNS:** Ranked chunks with source documents, scores, and context

    **EXAMPLE QUERIES:**
    - "What's the Seed round amount?" → finds all mentions across docs
    - "Round-Seed" → finds exact entity references
    - "robot specifications" → semantic search across technical docs
    """
    # Validate inputs
    if not query or not query.strip():
        return json.dumps({"error": "Query cannot be empty"})

    if search_type not in ("vector", "graph", "hybrid"):
        return json.dumps({"error": f"Invalid search_type: {search_type}. Must be 'vector', 'graph', or 'hybrid'"})

    # Clamp limit to reasonable bounds
    limit = min(max(1, limit), 100)

    t0 = _time.time()
    results = {"query": query, "search_type": search_type, "chunks": [], "graph_results": []}

    # Vector search
    if search_type in ("vector", "hybrid"):
        try:
            q_emb = _embed([query])[0]
            with _session() as s:
                rows = s.run("""
                    CALL db.index.vector.queryNodes('chunk_embedding', $k, $emb)
                    YIELD node, score
                    MATCH (d:Document)-[:CONTAINS]->(node)
                    RETURN d.path AS doc, node.section_header AS section,
                           node.text AS text, node.position AS pos, score
                    ORDER BY score DESC
                """, k=limit, emb=q_emb).data()
                results["chunks"] = rows
        except Exception as e:
            log.error("Vector search failed: %s\n%s", e, traceback.format_exc())
            results["vector_error"] = str(e)

    # Graph search — split query into individual terms for ANY-match
    if search_type in ("graph", "hybrid"):
        try:
            # Split query into words (min 3 chars to avoid noise)
            terms = [t.lower() for t in re.split(r'\s+', query.strip()) if len(t) >= 3]
            if not terms:
                terms = [query.lower()]

            with _session() as s:
                # Search tags — match ANY term in name or description
                tag_hits = s.run("""
                    MATCH (t:Tag)
                    WHERE any(term IN $terms WHERE toLower(t.name) CONTAINS term
                        OR (t.description IS NOT NULL AND toLower(t.description) CONTAINS term))
                    MATCH (d:Document)-[:HAS_TAG]->(t)
                    RETURN t.name AS tag, t.description AS desc, collect(d.path) AS documents
                """, terms=terms).data()

                # Search entities — match ANY term in name or value
                entity_hits = s.run("""
                    MATCH (e:Entity)
                    WHERE any(term IN $terms WHERE toLower(e.name) CONTAINS term
                        OR (e.value IS NOT NULL AND toLower(e.value) CONTAINS term))
                    MATCH (e)-[:ALSO_IN]->(d:Document)
                    RETURN e.name AS entity, e.type AS type, e.value AS value, collect(d.path) AS documents
                """, terms=terms).data()

                results["graph_results"] = {"tags": tag_hits, "entities": entity_hits}
        except Exception as e:
            log.error("Graph search failed: %s\n%s", e, traceback.format_exc())
            results["graph_error"] = str(e)

    # Deduplicate chunks if hybrid
    if search_type == "hybrid" and results["chunks"]:
        seen = set()
        deduped = []
        for c in results["chunks"]:
            key = (c["doc"], c["pos"])
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        results["chunks"] = deduped

    elapsed = _time.time() - t0
    results["_timing"] = f"{elapsed:.1f}s"
    n_chunks = len(results.get("chunks", []))
    gr = results.get("graph_results", {})
    n_tags = len(gr.get("tags", [])) if isinstance(gr, dict) else 0
    n_ents = len(gr.get("entities", [])) if isinstance(gr, dict) else 0
    log.info("[Smart Core] knowledge_call done in %.1fs — %d chunks, %d tags, %d entities", elapsed, n_chunks, n_tags, n_ents)
    return json.dumps(results, default=str)


@mcp.tool()
def commit_changes(author: str, message: str, changes: list[dict]) -> str:
    """
    Record document changes in the knowledge graph (git-style commit history).

    **WHEN TO USE:** After editing any document in docs_ver2/ to create an audit trail.

    **WHAT IT CREATES:**
    - Commit node with date, author, message
    - Change nodes for each text modification
    - Links to affected documents
    - Queryable history (use get_commit_history)

    **ARGS:**
    - author: Who made the change (e.g., "CTO", "CFO", "Claude")
    - message: Commit message describing the changes
    - changes: List of change dicts, each with:
        * doc_id: Document ID (e.g., "SP-001", "PRD-001")
        * section: Section name where change occurred
        * old_text: Previous text
        * new_text: New text

    **EXAMPLE:**
    commit_changes(
      author="CTO",
      message="Update Seed round to €1.5M",
      changes=[
        {
          "doc_id": "FM-001",
          "section": "Funding Rounds",
          "old_text": "Seed: €1,000,000",
          "new_text": "Seed: €1,500,000"
        }
      ]
    )

    **RETURNS:** Commit ID and change count
    """
    from datetime import datetime

    # Validate inputs
    if not author or not author.strip():
        return json.dumps({"error": "Author cannot be empty"})
    if not message or not message.strip():
        return json.dumps({"error": "Commit message cannot be empty"})
    if not changes or len(changes) == 0:
        return json.dumps({"error": "At least one change is required"})
    if len(changes) > 1000:
        return json.dumps({"error": f"Too many changes ({len(changes)}). Max 1000 per commit."})

    # Validate change structure
    for i, change in enumerate(changes):
        if not isinstance(change, dict):
            return json.dumps({"error": f"Change {i} must be a dict, got {type(change).__name__}"})
        required_fields = ["doc_id", "section", "old_text", "new_text"]
        for field in required_fields:
            if field not in change:
                return json.dumps({"error": f"Change {i} missing required field '{field}'"})

    _ensure_schema()

    # Generate commit ID: c-YYYY-MM-DD-XXX
    date_str = datetime.now().strftime("%Y-%m-%d")

    with _session() as s:
        # Count existing commits for today to generate sequence number
        count_result = s.run("""
            MATCH (c:Commit) WHERE c.date = $date
            RETURN count(c) AS cnt
        """, date=date_str).single()
        seq = (count_result["cnt"] if count_result else 0) + 1
        commit_id = f"c-{date_str}-{seq:03d}"

        # Create Commit node
        s.run("""
            CREATE (c:Commit {
                commit_id: $commit_id,
                date: $date,
                author: $author,
                message: $message,
                timestamp: datetime(),
                change_count: $change_count
            })
        """, commit_id=commit_id, date=date_str, author=author,
             message=message, change_count=len(changes))

        # Create Change nodes and relationships
        change_results = []
        for i, change in enumerate(changes):
            change_id = f"{commit_id}-ch{i+1:03d}"
            doc_id = change.get("doc_id", "")
            section = change.get("section", "")
            old_text = change.get("old_text", "")
            new_text = change.get("new_text", "")

            # Create Change node
            s.run("""
                CREATE (ch:Change {
                    change_id: $change_id,
                    doc_id: $doc_id,
                    section: $section,
                    old_text: $old_text,
                    new_text: $new_text
                })
            """, change_id=change_id, doc_id=doc_id, section=section,
                 old_text=old_text, new_text=new_text)

            # Link Commit -> Change
            s.run("""
                MATCH (c:Commit {commit_id: $commit_id})
                MATCH (ch:Change {change_id: $change_id})
                CREATE (c)-[:INCLUDES]->(ch)
            """, commit_id=commit_id, change_id=change_id)

            # Link Change -> Document (if document exists in graph)
            s.run("""
                MATCH (ch:Change {change_id: $change_id})
                MATCH (d:Document) WHERE d.doc_id = $doc_id
                CREATE (ch)-[:IN_DOCUMENT]->(d)
            """, change_id=change_id, doc_id=doc_id)

            change_results.append({
                "change_id": change_id,
                "doc_id": doc_id,
                "section": section
            })

    return json.dumps({
        "commit_id": commit_id,
        "date": date_str,
        "author": author,
        "message": message,
        "changes": change_results,
        "instruction": "Commit recorded. Use knowledge_call to query commit history."
    })


@mcp.tool()
def get_commit_history(doc_id: str = None, author: str = None, limit: int = 10) -> str:
    """
    Query document change history from the knowledge graph.

    **WHEN TO USE:**
    - To see what changed in a document over time
    - To track who made specific changes
    - To review change history before major updates
    - To audit document evolution

    **FILTERS:**
    - doc_id: Show changes for specific document (e.g., "PRD-001")
    - author: Show changes by specific person (e.g., "CTO")
    - limit: Max commits to return (default: 10)

    **ARGS:**
    - doc_id: Document ID to filter (optional)
    - author: Author name to filter (optional)
    - limit: Maximum number of commits to return (default: 10)

    **RETURNS:** List of commits with date, author, message, and detailed changes

    **EXAMPLE QUERIES:**
    - get_commit_history() → Last 10 commits across all docs
    - get_commit_history(doc_id="PRD-001") → All changes to PRD-001
    - get_commit_history(author="CTO", limit=5) → Last 5 CTO changes
    """
    with _session() as s:
        if doc_id:
            # Get commits affecting a specific document
            result = s.run("""
                MATCH (c:Commit)-[:INCLUDES]->(ch:Change)-[:IN_DOCUMENT]->(d:Document {doc_id: $doc_id})
                RETURN c.commit_id AS commit_id, c.date AS date, c.author AS author,
                       c.message AS message, ch.section AS section,
                       ch.old_text AS old_text, ch.new_text AS new_text
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """, doc_id=doc_id, limit=limit).data()
        elif author:
            # Get commits by author
            result = s.run("""
                MATCH (c:Commit {author: $author})-[:INCLUDES]->(ch:Change)
                RETURN c.commit_id AS commit_id, c.date AS date, c.author AS author,
                       c.message AS message, ch.doc_id AS doc_id, ch.section AS section,
                       ch.old_text AS old_text, ch.new_text AS new_text
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """, author=author, limit=limit).data()
        else:
            # Get all recent commits
            result = s.run("""
                MATCH (c:Commit)
                OPTIONAL MATCH (c)-[:INCLUDES]->(ch:Change)
                WITH c, collect({doc_id: ch.doc_id, section: ch.section}) AS changes
                RETURN c.commit_id AS commit_id, c.date AS date, c.author AS author,
                       c.message AS message, c.change_count AS change_count, changes
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """, limit=limit).data()

    return json.dumps({"commits": result}, default=str)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def shutdown_handler(_signum, _frame):
    """Graceful shutdown - close driver and exit cleanly."""
    log.info("[Smart Core] Shutdown signal received, cleaning up...")
    global _driver
    if _driver:
        try:
            _driver.close()
            log.info("[Smart Core] Neo4j driver closed.")
        except Exception as e:
            log.error("Error closing driver: %s", e)
    import sys
    sys.exit(0)


if __name__ == "__main__":
    # Register shutdown handlers
    import signal
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    # Pre-initialize Neo4j driver (fast, <1s)
    try:
        _ = get_driver()
        log.info("[Smart Core] Neo4j driver pre-initialized")
    except Exception as e:
        log.warning("[Smart Core] Could not pre-initialize Neo4j driver: %s", e)

    # Pre-warm embedding model with timeout (prevent startup blocking)
    # If model loads <20s: great, knowledge_call will be fast
    # If model loads >20s: skip, first knowledge_call will timeout but 2nd works
    log.info("[Smart Core] Pre-warming embedding model (20s timeout)...")
    import threading
    warmup_done = threading.Event()

    def warmup_model():
        try:
            _ = get_model()
            warmup_done.set()
            log.info("[Smart Core] Embedding model pre-warmed successfully")
        except Exception as e:
            log.warning("[Smart Core] Model warmup failed: %s", e)

    warmup_thread = threading.Thread(target=warmup_model, daemon=True)
    warmup_thread.start()
    warmup_thread.join(timeout=20.0)  # Wait max 20s

    if not warmup_done.is_set():
        log.warning("[Smart Core] Model warmup timed out after 20s - will load on first use")

    mcp.run(transport="stdio")
