# Agentspace CLI - Complete Guide

A powerful CLI tool for managing Google Cloud Agentspace (Discovery Engine) resources with a gcloud-style interface.

## Table of Contents

- [Quick Reference](#quick-reference)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Authentication](#authentication)
- [Usage Examples](#usage-examples)
- [Deployment Guide](#deployment-guide)
- [Migration Guide](#migration-guide)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## Quick Reference

### Basic Commands

```bash
# List engines (project-id and location are optional!)
python scripts/agentspace.py engines list
python scripts/agentspace.py engines list --location us

# Describe engine
python scripts/agentspace.py engines describe ENGINE_ID
python scripts/agentspace.py engines describe ENGINE_ID --location us

# Export full configuration
python scripts/agentspace.py engines describe ENGINE_ID --full > config.json

# List data stores
python scripts/agentspace.py data-stores list

# Describe data store
python scripts/agentspace.py data-stores describe DATASTORE_ID

# Create data store from GCS bucket
python scripts/agentspace.py data-stores create-from-gcs STORE_ID "Store Name" gs://bucket/path/*

# List documents in a data store
python scripts/agentspace.py data-stores list-documents DATASTORE_ID
```

### Common Options (ALL OPTIONAL!)

| Option | Description | Default |
|--------|-------------|---------|
| `--project-id` | GCP project ID | From gcloud config or $GOOGLE_CLOUD_PROJECT |
| `--location` | Region (global, us, eu) | From $AGENTSPACE_LOCATION or `us` |
| `--format` | Output format (table, json) | `table` |
| `--collection` | Collection ID | `default_collection` |

### Setting Defaults

```bash
# Using gcloud config
gcloud config set project bluefield-dev

# Using environment variables
export GOOGLE_CLOUD_PROJECT=bluefield-dev
export AGENTSPACE_LOCATION=us

# Now run without flags
python scripts/agentspace.py engines list
```

### Authentication

```bash
# Service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# Or use gcloud
gcloud auth application-default login
```

### Help Commands

```bash
python scripts/agentspace.py --help                    # Main help
python scripts/agentspace.py engines --help            # Engines help
python scripts/agentspace.py engines list --help       # Command help
```

---

## Installation

### Requirements

```bash
pip install -r requirements-agentspace.txt
```

Dependencies:
- `google-auth>=2.23.0`
- `google-auth-httplib2>=0.1.1`
- `requests>=2.31.0`
- `click>=8.1.0`

---

## Quick Start

### 1. Set up authentication

```bash
# Using service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Or use application default credentials
gcloud auth application-default login
```

### 2. List engines (AI apps)

```bash
# With explicit flags
python scripts/agentspace.py engines list \
  --project-id bluefield-dev \
  --location us

# Or with defaults (if configured)
python scripts/agentspace.py engines list
```

### 3. Describe a specific engine

```bash
python scripts/agentspace.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us
```

### 4. Export full configuration

```bash
python scripts/agentspace.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us \
  --full > engine-config.json
```

---

## Command Reference

### Command Structure

```
python scripts/agentspace.py <RESOURCE> <COMMAND> [OPTIONS]
```

Similar to gcloud: `gcloud compute instances list`

### Available Resources

- **`engines`** - Manage Agentspace engines (AI apps)
- **`data-stores`** - Manage data stores

---

### Engines Commands

#### `engines list` - List all engines

**Syntax:**
```bash
python scripts/agentspace.py engines list \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--format FORMAT]
```

**Options:**
- `--project-id` (optional): Google Cloud project ID (defaults to gcloud config or $GOOGLE_CLOUD_PROJECT)
- `--location` (optional): Location (defaults to $AGENTSPACE_LOCATION or `us`)
- `--collection` (default: `default_collection`): Collection ID
- `--format` (default: `table`): Output format (table, json, yaml)

**Examples:**
```bash
# Table format (default) - uses defaults for project-id and location
python scripts/agentspace.py engines list

# With explicit flags
python scripts/agentspace.py engines list --project-id bluefield-dev --location us

# JSON format
python scripts/agentspace.py engines list --project-id bluefield-dev --location us --format json

# Different collection
python scripts/agentspace.py engines list --project-id bluefield-dev --location us --collection my-collection
```

**Output (table):**
```
====================================================================================================
NAME                                                         DISPLAY NAME                   TYPE      
====================================================================================================
agentspace-demo-np                                           agentspace-demo-np             SEARCH    

Total: 1 engine(s)
```

---

#### `engines describe` - Describe a specific engine

**Syntax:**
```bash
python scripts/agentspace.py engines describe ENGINE_ID \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--format FORMAT] \
  [--full]
```

**Options:**
- `ENGINE_ID` (required): Engine ID or full resource name
- `--full`: Include complete configuration with all data store details

**Examples:**
```bash
# Basic describe (uses defaults)
python scripts/agentspace.py engines describe agentspace-demo-np

# With explicit flags
python scripts/agentspace.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us

# JSON format
python scripts/agentspace.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us \
  --format json

# Full configuration (for deployment)
python scripts/agentspace.py engines describe agentspace-demo-np \
  --project-id bluefield-dev \
  --location us \
  --full > engine-config.json
```

**Output (human-readable):**
```
================================================================================
Engine: agentspace-demo-np
================================================================================
Name: projects/838086266858/locations/us/collections/default_collection/engines/agentspace-demo-np
Solution Type: SOLUTION_TYPE_SEARCH
Industry Vertical: GENERIC
App Type: APP_TYPE_INTRANET

Common Config:
  companyName: Blue Cross Blue Shield

Search Config:
  Search Tier: SEARCH_TIER_ENTERPRISE
  Search Add-ons: SEARCH_ADD_ON_LLM

Data Stores (3):
  - agentspace-demo-gcs-datastore
  - test_1758213702567
  - logo_1758296148237

Features (7/14 enabled):
  ✓ people-search-org-chart
  ✓ agent-gallery
  ✓ personalization-memory
  ✓ model-selector
  ✓ no-code-agent-builder
  ✓ prompt-gallery
  ✓ disable-onedrive-upload
```

---

### Data Stores Commands

#### `data-stores list` - List all data stores

**Syntax:**
```bash
python scripts/agentspace.py data-stores list \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--format FORMAT]
```

**Examples:**
```bash
# Table format (uses defaults)
python scripts/agentspace.py data-stores list

# With explicit flags
python scripts/agentspace.py data-stores list --project-id bluefield-dev --location us

# JSON format
python scripts/agentspace.py data-stores list --project-id bluefield-dev --location us --format json
```

---

#### `data-stores describe` - Describe a specific data store

**Syntax:**
```bash
python scripts/agentspace.py data-stores describe DATA_STORE_ID \
  [--project-id PROJECT_ID] \
  [--location LOCATION] \
  [--collection COLLECTION_ID] \
  [--format FORMAT]
```

**Examples:**
```bash
# Human-readable format (uses defaults)
python scripts/agentspace.py data-stores describe agentspace-demo-gcs-datastore

# With explicit flags
python scripts/agentspace.py data-stores describe agentspace-demo-gcs-datastore \
  --project-id bluefield-dev \
  --location us

# JSON format
python scripts/agentspace.py data-stores describe agentspace-demo-gcs-datastore \
  --project-id bluefield-dev \
  --location us \
  --format json
```

---

#### `data-stores create-from-gcs` - Create data store from GCS bucket

**Syntax:**
```bash
python scripts/agentspace.py data-stores create-from-gcs DATA_STORE_ID DISPLAY_NAME GCS_URI \
  [--data-schema SCHEMA] \
  [--reconciliation-mode MODE] \
  [--format FORMAT]
```

**Arguments:**
- `DATA_STORE_ID` (required): Unique ID for the data store
- `DISPLAY_NAME` (required): Display name for the data store
- `GCS_URI` (required): GCS URI (e.g., `gs://bucket-name/path/*`)

**Options:**
- `--data-schema` (default: `content`): Data schema type (`content`, `custom`, `csv`, `document`)
- `--reconciliation-mode` (default: `INCREMENTAL`): Import mode (`INCREMENTAL`, `FULL`)

**Examples:**
```bash
# Create data store from PDF files
python scripts/agentspace.py data-stores create-from-gcs my-docs "My Documents" gs://my-bucket/docs/*.pdf

# Create data store from CSV file
python scripts/agentspace.py data-stores create-from-gcs my-data "My Data" gs://my-bucket/data.csv --data-schema=csv

# Create with full reconciliation mode
python scripts/agentspace.py data-stores create-from-gcs my-store "My Store" gs://my-bucket/* --reconciliation-mode=FULL
```

**Required Permissions:**
- `discoveryengine.dataStores.create`
- `discoveryengine.documents.import`
- `storage.objects.list` (for the GCS bucket)

---

#### `data-stores list-documents` - List documents in a data store

**Syntax:**
```bash
python scripts/agentspace.py data-stores list-documents DATA_STORE_ID \
  [--branch BRANCH] \
  [--format FORMAT]
```

**Arguments:**
- `DATA_STORE_ID` (required): Data store ID or full resource name

**Options:**
- `--branch` (default: `default_branch`): Branch name
- `--format` (default: `table`): Output format (table, json)

**Examples:**
```bash
# List documents in table format
python scripts/agentspace.py data-stores list-documents my-datastore

# List documents in JSON format
python scripts/agentspace.py data-stores list-documents my-datastore --format json

# List documents from a specific branch
python scripts/agentspace.py data-stores list-documents my-datastore --branch my-branch
```

**Output (table):**
```
====================================================================================================
Documents in Data Store: agentspace-demo-gcs-datastore
Branch: default_branch
====================================================================================================
ID                                       URI                                                Index Time               
----------------------------------------------------------------------------------------------------
2467dfadb37a342f97743e2c2542f1a4         gs://agentspace-demo-bucket-np/CPC_192255_00237... 09/11/2025, 05:01:39 PM  
4f354155ef0fbaf64591dd8fffb9bee7         gs://agentspace-demo-bucket-np/CI-Earnings Call... 09/11/2025, 02:40:22 PM  

Total: 4 document(s)
```

**Required Permissions:**
- `discoveryengine.documents.list`

---

## Authentication

### Method 1: Service Account (Recommended for automation)

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Method 2: User Credentials

```bash
gcloud auth application-default login
```

### Required IAM Permissions

The authenticated account needs:

**For Read Operations:**
- `discoveryengine.collections.list`
- `discoveryengine.engines.list`
- `discoveryengine.engines.get`
- `discoveryengine.dataStores.list`
- `discoveryengine.dataStores.get`
- `discoveryengine.documents.list`

**For Create Operations (data-stores create-from-gcs):**
- `discoveryengine.dataStores.create`
- `discoveryengine.documents.import`
- `storage.objects.list` (for GCS bucket access)

**Predefined Roles:**
- `roles/discoveryengine.viewer` (for read-only operations)
- `roles/discoveryengine.admin` (for full access including create operations)

### Grant Permissions

```bash
# Grant viewer role to service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='serviceAccount:SERVICE_ACCOUNT_EMAIL' \
  --role='roles/discoveryengine.viewer'
```

### Enable API

The Discovery Engine API must be enabled in:
1. The target project (where resources are)
2. The service account's home project (if using cross-project access)

```bash
# Enable API
gcloud services enable discoveryengine.googleapis.com --project=PROJECT_ID

# Verify API is enabled
gcloud services list --enabled --project=PROJECT_ID | grep discoveryengine
```

---

## Usage Examples

### 1. List All Resources

```bash
# List engines (uses defaults)
python scripts/agentspace.py engines list

# List data stores (uses defaults)
python scripts/agentspace.py data-stores list

# With explicit flags
python scripts/agentspace.py engines list --project-id my-project --location us
python scripts/agentspace.py data-stores list --project-id my-project --location us
```

### 2. Export Configuration for Deployment

```bash
# Export full engine configuration (uses defaults)
python scripts/agentspace.py engines describe my-engine --full > engine-config.json

# With explicit flags
python scripts/agentspace.py engines describe my-engine \
  --project-id my-project \
  --location us \
  --full > engine-config.json
```

The exported configuration includes:
- ✅ Engine settings (search tier, solution type, company name)
- ✅ All 14 feature flags (agent gallery, model selector, etc.)
- ✅ Data store configurations
- ✅ Document processing configs (chunking, parsing, OCR)
- ✅ JSON schemas for each data store
- ✅ ACL settings
- ✅ Billing/size information

### 3. Automation/Scripting

```bash
# Get JSON output for parsing (uses defaults)
ENGINE_COUNT=$(python scripts/agentspace.py engines list \
  --format json 2>/dev/null | jq 'length')

echo "Found $ENGINE_COUNT engines"

# List all engine names
python scripts/agentspace.py engines list \
  --format json | jq -r '.[].displayName'

# With explicit flags
python scripts/agentspace.py engines list \
  --project-id my-project \
  --location us \
  --format json | jq -r '.[].displayName'
```

### 4. Backup All Engines

```bash
# Get all engine configurations (uses defaults)
for engine in $(python scripts/agentspace.py engines list \
  --format json 2>/dev/null | jq -r '.[].name | split("/") | .[-1]'); do
  python scripts/agentspace.py engines describe "$engine" \
    --full > "backup-${engine}.json"
done

# With explicit flags
for engine in $(python scripts/agentspace.py engines list \
  --project-id my-project \
  --location us \
  --format json 2>/dev/null | jq -r '.[].name | split("/") | .[-1]'); do
  python scripts/agentspace.py engines describe "$engine" \
    --project-id my-project \
    --location us \
    --full > "backup-${engine}.json"
done
```

### 5. Check Multiple Locations

```bash
# Check global location
python scripts/agentspace.py engines list --project-id my-project --location global

# Check US region
python scripts/agentspace.py engines list --project-id my-project --location us

# Check EU region
python scripts/agentspace.py engines list --project-id my-project --location eu
```

**Note:** The CLI automatically uses the correct regional endpoint:
- `global` → `https://discoveryengine.googleapis.com/v1`
- `us` → `https://us-discoveryengine.googleapis.com/v1` (default)
- `eu` → `https://eu-discoveryengine.googleapis.com/v1`

---

## Deployment Guide

### Exported Configuration Details

When you export an engine configuration with `--full`, you get complete deployment-ready details:

#### Engine Configuration
- Display name, solution type, industry vertical
- Search tier (STANDARD/ENTERPRISE) & search add-ons
- Company name, app type
- **14+ Feature Flags:**
  - `agent-gallery`, `model-selector`, `prompt-gallery`
  - `personalization-memory`, `people-search-org-chart`
  - `no-code-agent-builder`
  - Upload controls (Google Drive, OneDrive)
  - `session-sharing`, `bi-directional-audio`
  - `notebook-lm`, image/video generation controls

#### Data Store Configuration (for each)
- Display name, creation time, industry vertical
- Content configuration, solution types
- **Document Processing:**
  - Chunking config (layout-based, chunk size)
  - Parsing config (digital, layout, OCR)
  - Table & image annotation settings
- **JSON Schema** (field definitions, validation rules)
- **ACL settings** (if enabled)
- **Billing information** (data size, last update)

### Deployment Steps

#### Step 1: Export from Source Environment

```bash
export GOOGLE_APPLICATION_CREDENTIALS="configs/source-project-creds.json"

python scripts/agentspace.py engines describe my-engine \
  --project-id source-project \
  --location us \
  --full > configs/engine-prod-template.json
```

#### Step 2: Review Configuration

```bash
# View configuration
cat configs/engine-prod-template.json | python3 -m json.tool | less

# Get summary
python3 << 'EOF'
import json
with open("configs/engine-prod-template.json") as f:
    config = json.load(f)

print("Engine:", config['engine']['displayName'])
print("Search Tier:", config['engine']['searchEngineConfig']['searchTier'])
print("Data Stores:", len(config['data_stores']))
print("Features Enabled:", sum(1 for v in config['engine']['features'].values() if 'ON' in v))
EOF
```

#### Step 3: Modify for Target Environment

Edit the configuration file:
1. Change project ID references
2. Update display name if needed
3. Adjust feature flags for different requirements
4. Update company name if different
5. Modify data store configurations as needed

#### Step 4: Deploy

The exported configuration can be used with:
- **Google Cloud Console**: Manual creation using the settings
- **Terraform**: Create IaC based on configuration
- **gcloud CLI**: Use gcloud commands with parameters
- **REST API**: POST configuration to Discovery Engine API

### Example Terraform Template

```hcl
# Based on exported configuration
resource "google_discovery_engine_search_engine" "prod_engine" {
  engine_id        = "my-engine-prod"
  collection_id    = "default_collection"
  location         = var.location
  display_name     = "Production Engine"
  
  solution_type    = "SOLUTION_TYPE_SEARCH"
  industry_vertical = "GENERIC"
  search_tier      = "SEARCH_TIER_ENTERPRISE"
  search_add_ons   = ["SEARCH_ADD_ON_LLM"]
  company_name     = "My Company"
  
  data_store_ids   = [
    google_discovery_engine_data_store.primary.data_store_id,
  ]
}
```

---

## Migration Guide

If you're migrating from the old argparse-based CLI:

### Command Mapping

| Old Command | New Command |
|-------------|-------------|
| `list_agentspace_apps.py --project-id ID --location us` | `scripts/agentspace.py engines list --project-id ID --location us` |
| `list_agentspace_apps.py --get-engine ENGINE` | `scripts/agentspace.py engines describe ENGINE --project-id ID --location us` |
| `list_agentspace_apps.py --get-engine ENGINE --output-file FILE` | `scripts/agentspace.py engines describe ENGINE --full > FILE` |
| `list_agentspace_apps.py --get-all-engines` | Loop over `engines list` results |

### Key Changes

1. **Command Structure**: Changed from flat to hierarchical (resource + action)
2. **Output Files**: Use shell redirection (`>`) instead of `--output-file`
3. **Default Format**: Changed from "text" to "table"
4. **Batch Operations**: Manual iteration instead of `--get-all-engines`

---

## Troubleshooting

### API Not Enabled (403 Error)

**Symptom:** 
```
Error: 403 Client Error: Forbidden
Message: Discovery Engine API has not been used in project...
```

**Solution:**
```bash
# Enable API in target project
gcloud services enable discoveryengine.googleapis.com --project=PROJECT_ID

# If using cross-project service account, enable in SA's home project too
gcloud services enable discoveryengine.googleapis.com --project=SA_PROJECT_ID

# Wait 1-2 minutes for propagation
```

### Permission Denied

**Symptom:** `Permission 'discoveryengine.*.list' denied`

**Solution:**
```bash
# Grant permissions to service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member='serviceAccount:SA_EMAIL' \
  --role='roles/discoveryengine.viewer'

# Wait 30-60 seconds for IAM propagation
```

### No Resources Found

**Symptom:** All counts are 0, but API is enabled

**Possible reasons:**
- Resources exist in a different location (try `--location us` or `--location eu`)
- Resources exist in a different project
- No AI apps have been created yet (this is normal!)

### Authentication Errors

**Symptom:** `DefaultCredentialsError: Your default credentials were not found`

**Solution:**
```bash
# Set up credentials
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### Incorrect Regional Endpoint

**Symptom:** `400 Client Error: Incorrect API endpoint used`

**Solution:** Resources in regional locations (us, eu) require the correct `--location` flag. The CLI handles regional endpoints automatically, but you must specify the correct location:

```bash
# If resources are in 'us' region
python scripts/agentspace.py engines list --project-id PROJECT_ID --location us
```

---

## Advanced Topics

### Regional Endpoints

The CLI automatically uses the correct regional endpoint based on `--location`:

| Location | API Endpoint |
|----------|-------------|
| `global` | `https://discoveryengine.googleapis.com/v1` |
| `us`, `us-central1` | `https://us-discoveryengine.googleapis.com/v1` (default) |
| `eu`, `eu-west1` | `https://eu-discoveryengine.googleapis.com/v1` |

### Cross-Project Access

When using a service account from one project to access resources in another:

1. Enable Discovery Engine API in **both** projects
2. Grant IAM permissions in the target project
3. Wait for permissions to propagate (30-60 seconds)

### Output Formats

#### Table (default)
- Human-readable
- Columnar display
- Summary statistics
- Best for terminal viewing

#### JSON
- Machine-readable
- Complete data structure
- Suitable for automation
- Can be parsed with `jq`

#### YAML
- Similar to table (can be enhanced)
- Good for configuration files

---

## Help Commands

Get help at any level:

```bash
# Main help
python scripts/agentspace.py --help

# Resource help
python scripts/agentspace.py engines --help
python scripts/agentspace.py data-stores --help

# Command help
python scripts/agentspace.py engines list --help
python scripts/agentspace.py engines describe --help
python scripts/agentspace.py data-stores list --help
python scripts/agentspace.py data-stores describe --help
```

---

## API Reference

This tool uses the [Google Cloud Discovery Engine REST API](https://cloud.google.com/generative-ai-app-builder/docs/reference/rest).

Key endpoints:
- `GET /v1/{parent}/collections` - List collections
- `GET /v1/{parent}/engines` - List engines
- `GET /v1/{engine}` - Get engine details
- `GET /v1/{parent}/dataStores` - List data stores
- `GET /v1/{dataStore}` - Get data store details
- `GET /v1/{dataStore}/schemas/{schema}` - Get schema

---

## Contributing

### Adding New Commands

The CLI uses Click's group/command structure:

```python
@cli.group()
def new_resource():
    """Manage new resource type."""
    pass

@new_resource.command('list')
@project_option
@location_option
def new_resource_list(project_id, location):
    """List new resources."""
    # Implementation
```

### Testing

Test all commands before committing:

```bash
# Test help
python scripts/agentspace.py --help
python scripts/agentspace.py engines --help

# Test list commands
python scripts/agentspace.py engines list --project-id TEST_PROJECT --location us
python scripts/agentspace.py data-stores list --project-id TEST_PROJECT --location us

# Test describe commands
python scripts/agentspace.py engines describe ENGINE_ID --project-id TEST_PROJECT --location us
python scripts/agentspace.py data-stores describe DS_ID --project-id TEST_PROJECT --location us

# Test JSON output
python scripts/agentspace.py engines list --project-id TEST_PROJECT --location us --format json
```

---

## License

[Add your license information here]

---

## Support

For questions or issues:
1. Check this README for documentation
2. Use `--help` at any command level
3. Review error messages carefully (they often contain solutions)
4. Check Google Cloud Console to verify resources exist
5. Verify IAM permissions and API enablement

---

## Version History

- **v1.0.0** - Initial Click-based CLI with gcloud-style commands
  - `engines list`, `engines describe`
  - `data-stores list`, `data-stores describe`
  - Regional endpoint support
  - Table and JSON output formats

