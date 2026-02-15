# Smart Core Configuration Examples

This directory contains example configuration files for setting up Smart Core.

---

## Configuration Files

### 1. mcp.json.example

**Location in your project:** `.mcp.json` (project root)

**Purpose:** Configure Claude Code to connect to Smart Core MCP server

**Setup:**
```bash
# Copy to your project root
cp examples/mcp.json.example .mcp.json

# Edit with your paths
# Update: args[0] → path to server.py
# Update: DB_PASSWORD → your Neo4j password
```

**Example:**
```json
{
  "mcpServers": {
    "smart-core": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/smart-core-repo/app/smart-core-mcp/server.py"],
      "env": {
        "DB_URI": "bolt://127.0.0.1:7687",
        "DB_USER": "neo4j",
        "DB_PASSWORD": "your-password",
        "DB_NAME": "smart-core"
      }
    }
  }
}
```

---

### 2. config.json.template

**Location:** `app/smart-core-mcp/config.json`

**Purpose:** Configure Smart Core MCP server (database, embeddings, document path)

**Setup:**
```bash
# Copy template to create config
cp app/smart-core-mcp/config.json.template app/smart-core-mcp/config.json

# Edit config.json:
# 1. Set database password
# 2. Set project_docs_path (relative from server.py location)
```

**Key settings:**
- `database.password` - Your Neo4j password
- `processing.project_docs_path` - Path to your documents folder (relative from server.py)

**Path examples:**
```
# If server.py is at: smart-core-repo/app/smart-core-mcp/server.py
# And docs are at: your-project/docs/

# Option 1: Relative path (recommended)
"project_docs_path": "../../../../your-project/docs"

# Option 2: Absolute path
"project_docs_path": "/full/path/to/your-project/docs"
```

---

## Quick Start

**1. Setup Neo4j:**
```bash
# In Neo4j Desktop:
# - Create database "smart-core"
# - Set password
# - Start database
```

**2. Install dependencies:**
```bash
cd app/smart-core-mcp
pip install -r requirements.txt
```

**3. Configure Smart Core:**
```bash
# Create config from template
cp config.json.template config.json

# Edit config.json:
# - Set database.password
# - Set processing.project_docs_path
```

**4. Configure Claude Code:**
```bash
# Copy MCP example to your project
cp examples/mcp.json.example /path/to/your-project/.mcp.json

# Edit .mcp.json:
# - Update args[0] to full path to server.py
# - Set DB_PASSWORD
```

**5. Test connection:**
```
# In Claude Code:
User: "Ping Neo4j"

Expected: {"status": "ok", "database": "smart-core"}
```

---

## Troubleshooting

**Issue: "docs directory not found"**
- Check `project_docs_path` in `config.json`
- Verify path is correct from server.py location
- Use `ls` to test: `cd app/smart-core-mcp && ls <your-path>`

**Issue: Connection refused**
- Verify Neo4j is running in Neo4j Desktop
- Check database name matches config
- Test password manually

---

**See main [README.md](../README.md) for full documentation.**
